#!/usr/bin/env bash
# ==============================================================================
# Prometheus FC - Bootloader Flash Script (DFU / ST-Link)
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOOTLOADER_BIN="${SCRIPT_DIR}/../bootloader/Prometheus-FC_bl.bin"
BOOTLOADER_HEX="${SCRIPT_DIR}/../bootloader/Prometheus-FC_bl.hex"

echo "======================================================================"
echo "Prometheus FC Bootloader Flasher"
echo "Board: DevEBox STM32H743VIT6 | Board ID: 7121"
echo "======================================================================"

if [ "$1" == "stlink" ]; then
    echo "Flashing via ST-Link (st-flash)..."
    st-flash write "${BOOTLOADER_BIN}" 0x08000000
    echo "Done! Please power cycle the board."
elif [ "$1" == "dfu" ] || [ -z "$1" ]; then
    echo "Flashing via DFU (dfu-util)..."
    echo "Make sure the board is in DFU mode (hold BOOT0 button while connecting USB)."
    sudo dfu-util -a 0 --dfuse-address 0x08000000:leave -D "${BOOTLOADER_BIN}"
    echo "Done! Bootloader flashed to 0x08000000."
else
    echo "Usage: $0 [dfu|stlink]"
    exit 1
fi
