# Prometheus FC

![Prometheus FC (DevEBox STM32H743VIT6)](https://stm32-base.org/assets/img/boards/STM32H743VIT6_STM32H7XX_M/Top.jpg)

**Prometheus FC** is a custom ArduPilot hardware definition that transforms a generic **DevEBox STM32H743VIT6 V3.0** development board into a fully functional, high-performance flight controller with **full dual-sensor redundancy**.

---

## Hardware

| Component | Details |
|-----------|---------|
| **MCU** | STM32H743VIT6 @ 480MHz, 2MB Flash, 1MB RAM |
| **Board** | DevEBox STM32H743VIT6 V3.0 (LQFP100) |
| **Crystal** | 25MHz HSE |
| **Board ID** | 7121 |

---

## Confirmed Working Sensors (as of Aug 2026)

| Sensor | Interface | Pins | Status |
|--------|-----------|------|--------|
| **IMU 1** | BMI160 on SPI1 | SCK=PA5, MISO=PA6, MOSI=PD7, CS=PB5 | ✅ Working |
| **IMU 2** | BMI160 on SPI4 | SCK=PE12, MISO=PE13, MOSI=PE14, CS=PD4 | ✅ Working (clone chip, ID=0xD3) |
| **Baro 1** | BMP280 on SPI1 | Shared SPI1 bus, CS=PB12 | ✅ Working |
| **Baro 2** | BMP280 on SPI4 | Shared SPI4 bus, CS=PB13 | ✅ Working |
| **Compass 1** | External via I2C1 | SCL=PB6, SDA=PB7 | ✅ Working |
| **Compass 2** | External via I2C2 | SCL=PB10, SDA=PB11 | ✅ Working |
| **GPS 1** | u-blox via USART1 | TX=PA9, RX=PA10 | ✅ 3D Fix, 9 sats |
| **GPS 2** | u-blox via USART6 | TX=PC6, RX=PC7 | ✅ 3D Fix, 8 sats |
| **RC Receiver** | FSIA10B iBUS via UART4 | RX=PB8 | ✅ Working |

---

## UART / Serial Port Map

| Serial | UART | TX Pin | RX Pin | Default Use |
|--------|------|--------|--------|-------------|
| SERIAL0 | OTG1 (USB) | PA11 | PA12 | MAVLink / GCS |
| SERIAL1 | USART1 | PA9 | PA10 | GPS 1 |
| SERIAL2 | USART2 | PD5 | PD6 | MAVLink2 (companion) |
| SERIAL3 | USART3 | PD8 | PD9 | Telemetry |
| SERIAL4 | UART4 | PB9 | PB8 | RC Input (iBUS/SBUS) |
| SERIAL5 | USART6 | PC6 | PC7 | GPS 2 |
| SERIAL6 | UART7 | PE8 | PE7 | Debug console |
| SERIAL7 | UART8 | PE1 | PE0 | Spare |

---

## Motor Outputs

| PWM | Timer | Pin | Use |
|-----|-------|-----|-----|
| PWM1 | TIM4_CH1 | PD12 | Motor 1 |
| PWM2 | TIM4_CH2 | PD13 | Motor 2 |
| PWM3 | TIM4_CH3 | PD14 | Motor 3 |
| PWM4 | TIM4_CH4 | PD15 | Motor 4 |

DShot300 recommended (MOT_PWM_TYPE = 6).

---

## LED & Buzzer

| Function | Pin | GPIO |
|----------|-----|------|
| Bootloader LED | PA1 | — |
| Status LED 0 (synced to buzzer) | PE2 | GPIO(90) |
| Status LED 1 | PE3 | GPIO(91) |
| Status LED 2 | PB0 | GPIO(92) |
| Buzzer | PE4 | GPIO(80) |

The PE2 LED is synced to the buzzer — it flashes in sync with all buzzer patterns.

---

## Battery Monitoring

| Function | Pin |
|----------|-----|
| Voltage sense | PA2 (ADC1) |
| Current sense | PA3 (ADC1) |

Scales: HAL_BATT_VOLT_SCALE 11.0, HAL_BATT_CURR_SCALE 11.0

---

## CAN Bus

| Signal | Pin |
|--------|-----|
| CAN1_RX | PD0 |
| CAN1_TX | PD1 |

Requires external CAN transceiver (e.g. SN65HVD230).

---

## Firmware Patches Required

Two patches must be applied to ArduPilot source before building:

### 1. libraries/AP_InertialSensor/AP_InertialSensor_BMI160.cpp

Problem: BMI160 powers up in I2C mode. The driver attempted a SOFTRESET write
before doing the SPI wakeup sequence, so the write failed and the chip was
never switched to SPI mode. Also, the SPI4 BMI160 is a clone chip returning
chip ID 0xD3 instead of the official 0xD1.

Fix 1 - Add SPI wakeup BEFORE the init loop in _hardware_init():
    uint8_t v;
    for (uint8_t wakeup = 0; wakeup < 10; wakeup++) {
        _dev->read_registers(0x7F, &v, 1);
        hal.scheduler->delay(5);
    }
    hal.scheduler->delay(20);

Fix 2 - Accept clone chip ID 0xD3 alongside official 0xD1:
    #define BMI160_CHIPID   0xD1
    #define BMI160_CHIPID2  0xD3  // clone/variant (common on Chinese boards)
    // Change chip ID check to:
    if (v != BMI160_CHIPID && v != BMI160_CHIPID2) {

### 2. libraries/AP_Notify/Buzzer.cpp + hwdef.dat

Fix - Sync LED to buzzer:
    In hwdef.dat: define HAL_BUZZER_LED_PIN 90
    In Buzzer.cpp: Add GPIO write to HAL_BUZZER_LED_PIN alongside buzzer pin writes.

---

## Building the Firmware

    git clone --recurse-submodules https://github.com/ArduPilot/ardupilot.git
    cd ardupilot
    cp -r "Prometheus-FC" libraries/AP_HAL_ChibiOS/hwdef/
    # Apply firmware patches (see above)
    ./waf configure --board Prometheus-FC
    ./waf copter

---

## Flashing

Via bootloader (USB, recommended):
    python Tools/scripts/uploader.py --port /dev/ttyACM0 build/Prometheus-FC/bin/arducopter.apj

Via DFU (first flash only - hold BOOT0 while plugging USB):
    sudo dfu-util -a 0 --dfuse-address 0x08020000 -D arducopter.bin

---

## RC Receiver Setup (FSIA10B + FSi6X)

1. Use the B/S port (iBUS output) on FSIA10B — NOT the individual PWM ports
2. Connect B/S signal wire to PB8 (UART4_RX)
3. Connect 5V and GND to receiver
4. Bind receiver to FSi6X (solid LED = bound)
5. Set: SERIAL4_PROTOCOL=23, RC_PROTOCOLS=32 (iBUS)

---

## Disclaimer

This project is for educational and DIY purposes. The STM32H743 runs on 3.3V logic.
Ensure all peripherals are 3.3V compatible or use level shifters.
