# Prometheus FC

![Prometheus FC (DevEBox STM32H743VIT6)](https://shop.controllerstech.com/cdn/shop/files/750_2.png?v=1715678880&width=1445)

**Prometheus FC** is a custom ArduPilot hardware definition and configuration project that transforms a generic, low-cost **DevEBox STM32H743VIT6 V3.0** development board into a fully functional, high-performance flight controller for drones and rovers.

## Why this board?
Traditionally, the DevEBox STM32H743 is an industrial/generic microcontroller development board. It has historically **never been used in drones** and nobody had written an ArduPilot `hwdef` for it for a few reasons:
1. **No Onboard Sensors:** Unlike a Pixhawk or Matek flight controller, this board does not have an onboard IMU (gyro/accelerometer), Barometer, or Compass.
2. **No Standard Connectors:** It lacks standard drone JST-GH connectors, relying entirely on bare 2.54mm header pins.
3. **Power Design:** It does not have built-in 5V BECs or power protection circuits specifically designed for RC servos and drone peripherals.

**However**, this board features the incredibly powerful **STM32H743VIT6** processor (running at 480MHz with 2MB Flash and 1MB RAM). For DIY builders willing to wire up their own external sensors (like an external MPU6000/ICM20602 via SPI, and a BMP280/Compass via I2C), this board offers **Pixhawk 6-level processing power at a fraction of the cost**.

## Project Features
This repository provides the custom ArduPilot hardware definition (`hwdef.dat`) required to compile firmware for this board, unlocking its massive potential:

*   **8x Serial Ports (UART/USART):** Configured for GPS, Telemetry, RC, etc.
*   **2x SPI Buses & 2x I2C Buses:** For external IMUs, Baros, Compasses, and OLEDs.
*   **ADC Battery Monitoring:** PA2 and PA3 configured for analog Voltage and Current sensing.
*   **CAN Bus (DroneCAN):** CAN1 enabled on PD0/PD1 (requires external transceiver).
*   **PWM Outputs:** Up to 12 DShot/PWM motor/servo outputs.
*   **MicroSD Slot:** Full FatFS support for ArduPilot dataflash logging.

## How to Use This Project

### 1. Wiring Your Sensors
Since the board has no onboard sensors, you **must** connect an external SPI IMU and an I2C barometer before ArduPilot will successfully boot without errors.
Please refer to the highly detailed **[DevEBoxH743_Prometheus_FC_Pinout_Guide.txt](DevEBoxH743_Prometheus_FC_Pinout_Guide.txt)** included in this repository for exact pin mappings.

### 2. Compiling the Firmware
If you wish to modify the hardware definition:
1. Copy the `DevEBoxH743` folder into your ArduPilot source code at `libraries/AP_HAL_ChibiOS/hwdef/`.
2. Configure the build: `./waf configure --board DevEBoxH743`
3. Compile for your vehicle type: `./waf copter` (or `plane`, `rover`).

### 3. Flashing the Board
1. Connect the board via USB to your computer.
2. Put the board into **DFU Mode** (Hold the `BOOT0` button while powering on/plugging in USB).
3. Flash using `dfu-util`:
   ```bash
   sudo dfu-util -a 0 --dfuse-address 0x08020000 -D arducopter.bin
   ```
4. Disconnect, replug normally, and connect via Mission Planner or MAVProxy!

## Disclaimer
This project is for educational and DIY purposes. Ensure you understand the power requirements (3.3V vs 5V logic) of the STM32H743 before connecting peripherals, as failure to do so can destroy the MCU.
