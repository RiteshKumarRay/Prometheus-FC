#!/usr/bin/env bash
# ==============================================================================
# Prometheus FC - ArduPilot Installation & Patching Script
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

ARDUPILOT_DIR="${1:-}"

if [ -z "$ARDUPILOT_DIR" ]; then
    # Try looking in common parent locations
    if [ -f "${REPO_DIR}/../../wscript" ] && [ -d "${REPO_DIR}/../../libraries" ]; then
        ARDUPILOT_DIR="$(cd "${REPO_DIR}/../.." && pwd)"
    elif [ -d "/home/ritesh/ardupilot" ]; then
        ARDUPILOT_DIR="/home/ritesh/ardupilot"
    else
        echo "Usage: $0 /path/to/ardupilot"
        exit 1
    fi
fi

if [ ! -f "${ARDUPILOT_DIR}/wscript" ] || [ ! -d "${ARDUPILOT_DIR}/libraries" ]; then
    echo "Error: '${ARDUPILOT_DIR}' does not appear to be an ArduPilot root directory."
    exit 1
fi

echo "======================================================================"
echo "Installing Prometheus FC to: ${ARDUPILOT_DIR}"
echo "======================================================================"

HWDEF_DEST="${ARDUPILOT_DIR}/libraries/AP_HAL_ChibiOS/hwdef/Prometheus-FC"
mkdir -p "${HWDEF_DEST}"

echo "[1/4] Copying hwdef files..."
cp -v "${REPO_DIR}/hwdef.dat" "${HWDEF_DEST}/"
cp -v "${REPO_DIR}/hwdef-bl.dat" "${HWDEF_DEST}/"
cp -v "${REPO_DIR}/README.md" "${HWDEF_DEST}/"

echo "[2/4] Applying BMI160 SPI wakeup & clone ID patch..."
if patch -p1 -N --dry-run -d "${ARDUPILOT_DIR}" < "${REPO_DIR}/patches/0001-AP_InertialSensor_BMI160.patch" >/dev/null 2>&1; then
    patch -p1 -d "${ARDUPILOT_DIR}" < "${REPO_DIR}/patches/0001-AP_InertialSensor_BMI160.patch"
    echo "  -> Applied 0001-AP_InertialSensor_BMI160.patch"
else
    echo "  -> 0001-AP_InertialSensor_BMI160.patch already applied or conflict, skipping."
fi

echo "[3/4] Applying Buzzer LED sync patch..."
if patch -p1 -N --dry-run -d "${ARDUPILOT_DIR}" < "${REPO_DIR}/patches/0002-AP_Notify_Buzzer_LED_sync.patch" >/dev/null 2>&1; then
    patch -p1 -d "${ARDUPILOT_DIR}" < "${REPO_DIR}/patches/0002-AP_Notify_Buzzer_LED_sync.patch"
    echo "  -> Applied 0002-AP_Notify_Buzzer_LED_sync.patch"
else
    echo "  -> 0002-AP_Notify_Buzzer_LED_sync.patch already applied or conflict, skipping."
fi

echo "[4/4] Applying Board ID 7121 bootloader patch..."
if patch -p1 -N --dry-run -d "${ARDUPILOT_DIR}" < "${REPO_DIR}/patches/0003-board_types_7121.patch" >/dev/null 2>&1; then
    patch -p1 -d "${ARDUPILOT_DIR}" < "${REPO_DIR}/patches/0003-board_types_7121.patch"
    echo "  -> Applied 0003-board_types_7121.patch"
else
    echo "  -> 0003-board_types_7121.patch already applied or conflict, skipping."
fi

echo "======================================================================"
echo "Installation complete!"
echo "To build firmware:"
echo "  cd \"${ARDUPILOT_DIR}\""
echo "  ./waf configure --board Prometheus-FC"
echo "  ./waf copter"
echo "======================================================================"
