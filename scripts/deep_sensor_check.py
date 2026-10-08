#!/usr/bin/env python3
import sys
import time
import json
from pymavlink import mavutil

def main():
    print("[*] Connecting to /dev/ttyACM0...")
    mav = mavutil.mavlink_connection('/dev/ttyACM0', baud=115200)

    print("[*] Waiting for heartbeat...")
    hb = mav.wait_heartbeat(timeout=10)
    if not hb:
        print("[-] Timeout waiting for heartbeat.")
        return

    # Request all streams at 10Hz
    mav.mav.request_data_stream_send(
        mav.target_system, mav.target_component,
        mavutil.mavlink.MAV_DATA_STREAM_ALL, 10, 1
    )

    # Trigger pre-arm check messages
    mav.mav.command_long_send(
        mav.target_system, mav.target_component,
        mavutil.mavlink.MAV_CMD_RUN_PREARM_CHECKS,
        0, 0, 0, 0, 0, 0, 0, 0
    )

    # Request sensor parameters
    param_names = [
        # INS / IMU
        "INS_ACC_ID", "INS_GYR_ID", "INS_ACC2_ID", "INS_GYR2_ID", "INS_ACC3_ID", "INS_GYR3_ID",
        "INS_USE", "INS_USE2", "INS_USE3",
        "INS_ENABLE_MASK", "INS_FAST_SAMPLE",
        # Barometer
        "BARO1_DEVID", "BARO2_DEVID", "BARO3_DEVID", "BARO_PRIMARY", "BARO_EXT_BUS", "BARO_PROBE_EXT",
        # Compass
        "COMPASS_DEV_ID", "COMPASS_DEV_ID2", "COMPASS_DEV_ID3",
        "COMPASS_USE", "COMPASS_USE2", "COMPASS_USE3",
        "COMPASS_EXTERNAL", "COMPASS_EXT2", "COMPASS_EXT3",
        "COMPASS_AUTODEC", "COMPASS_ORIENT", "COMPASS_ORIENT2",
        # GPS
        "GPS_TYPE", "GPS_TYPE2", "GPS_GNSS_MODE", "GPS_RATE_MS",
        # System
        "BRD_TYPE", "SYSID_THISMAV", "BATT_MONITOR", "BATT_VOLT_PIN", "BATT_CURR_PIN", "BATT_VOLT_MULT"
    ]

    for p in param_names:
        mav.mav.param_request_read_send(
            mav.target_system, mav.target_component,
            p.encode('utf-8'), -1
        )

    # Also request message intervals for specific telemetry
    msg_ids = [
        mavutil.mavlink.MAVLINK_MSG_ID_RAW_IMU,
        mavutil.mavlink.MAVLINK_MSG_ID_SCALED_IMU2,
        mavutil.mavlink.MAVLINK_MSG_ID_HIGHRES_IMU,
        mavutil.mavlink.MAVLINK_MSG_ID_SCALED_PRESSURE,
        mavutil.mavlink.MAVLINK_MSG_ID_SCALED_PRESSURE2,
        mavutil.mavlink.MAVLINK_MSG_ID_GPS_RAW_INT,
        mavutil.mavlink.MAVLINK_MSG_ID_ATTITUDE,
        mavutil.mavlink.MAVLINK_MSG_ID_SYS_STATUS,
        mavutil.mavlink.MAVLINK_MSG_ID_BATTERY_STATUS,
        mavutil.mavlink.MAVLINK_MSG_ID_VFR_HUD
    ]

    for mid in msg_ids:
        mav.mav.command_long_send(
            mav.target_system, mav.target_component,
            mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,
            0, mid, 100000, 0, 0, 0, 0, 0 # 100000 us = 10Hz
        )

    data = {
        "params": {},
        "statustext": [],
        "samples": {
            "imu1_acc": [],
            "imu1_gyro": [],
            "imu2_acc": [],
            "imu2_gyro": [],
            "mag1": [],
            "mag2": [],
            "baro1_press": [],
            "baro1_temp": [],
            "baro2_press": [],
            "baro2_temp": [],
            "attitude_rpy": [],
            "gps": {}
        }
    }

    start = time.time()
    while time.time() - start < 8.0:
        msg = mav.recv_match(blocking=True, timeout=0.5)
        if not msg:
            continue
        mtype = msg.get_type()

        if mtype == "STATUSTEXT":
            txt = msg.text
            if txt not in data["statustext"]:
                data["statustext"].append(txt)

        elif mtype == "PARAM_VALUE":
            pid = msg.param_id
            if isinstance(pid, bytes):
                pid = pid.decode('utf-8', errors='ignore').rstrip('\\x00')
            data["params"][pid] = msg.param_value

        elif mtype == "RAW_IMU":
            data["samples"]["imu1_acc"].append((msg.xacc, msg.yacc, msg.zacc))
            data["samples"]["imu1_gyro"].append((msg.xgyro, msg.ygyro, msg.zgyro))
            data["samples"]["mag1"].append((msg.xmag, msg.ymag, msg.zmag))

        elif mtype == "SCALED_IMU2":
            data["samples"]["imu2_acc"].append((msg.xacc, msg.yacc, msg.zacc))
            data["samples"]["imu2_gyro"].append((msg.xgyro, msg.ygyro, msg.zgyro))
            data["samples"]["mag2"].append((msg.xmag, msg.ymag, msg.zmag))

        elif mtype == "SCALED_PRESSURE":
            data["samples"]["baro1_press"].append(msg.press_abs)
            data["samples"]["baro1_temp"].append(msg.temperature / 100.0)

        elif mtype == "SCALED_PRESSURE2":
            data["samples"]["baro2_press"].append(msg.press_abs)
            data["samples"]["baro2_temp"].append(msg.temperature / 100.0)

        elif mtype == "ATTITUDE":
            data["samples"]["attitude_rpy"].append((round(msg.roll * 57.2958, 2), round(msg.pitch * 57.2958, 2), round(msg.yaw * 57.2958, 2)))

        elif mtype == "GPS_RAW_INT":
            data["samples"]["gps"] = {
                "fix_type": msg.fix_type,
                "lat": msg.lat / 1e7,
                "lon": msg.lon / 1e7,
                "alt_m": msg.alt / 1000.0,
                "eph": msg.eph,
                "epv": msg.epv,
                "vel": msg.vel / 100.0,
                "cog": msg.cog / 100.0,
                "satellites_visible": msg.satellites_visible
            }

    # Summary calculations
    def stats(series):
        if not series:
            return None
        return {
            "count": len(series),
            "latest": series[-1],
            "min": min(series),
            "max": max(series),
            "avg": round(sum(series) / len(series), 3)
        }

    def stats_3d(series):
        if not series:
            return None
        xs = [s[0] for s in series]
        ys = [s[1] for s in series]
        zs = [s[2] for s in series]
        return {
            "count": len(series),
            "latest": series[-1],
            "avg": (round(sum(xs)/len(xs), 2), round(sum(ys)/len(ys), 2), round(sum(zs)/len(zs), 2))
        }

    summary = {
        "params": data["params"],
        "statustext_alerts": data["statustext"],
        "imu1_acc_stats": stats_3d(data["samples"]["imu1_acc"]),
        "imu1_gyro_stats": stats_3d(data["samples"]["imu1_gyro"]),
        "imu2_acc_stats": stats_3d(data["samples"]["imu2_acc"]),
        "imu2_gyro_stats": stats_3d(data["samples"]["imu2_gyro"]),
        "mag1_stats": stats_3d(data["samples"]["mag1"]),
        "mag2_stats": stats_3d(data["samples"]["mag2"]),
        "baro1_press_hPa": stats(data["samples"]["baro1_press"]),
        "baro1_temp_C": stats(data["samples"]["baro1_temp"]),
        "baro2_press_hPa": stats(data["samples"]["baro2_press"]),
        "baro2_temp_C": stats(data["samples"]["baro2_temp"]),
        "attitude_rpy_stats": stats_3d(data["samples"]["attitude_rpy"]),
        "gps": data["samples"]["gps"]
    }

    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
