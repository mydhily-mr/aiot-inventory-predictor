# AI-Based Predictive Inventory Management System (PIMS)
 ![Cover Image](../images/cover_image.png)— Cover Image

# List of Components


| Component | Interface | MAX32630FTHR Pin(s) | Notes |
|---|---|---|---|
| [MAX32630 FTHR board](https://www.digikey.in/en/products/detail/analog-devices-inc-maxim-integrated/MAX32630FTHR/6575544) | - | - | 1 |
| [HX711](https://www.digikey.in/en/products/detail/soldered-electronics/333005/21720457) #1 (Bin 1 load cell) | Digital (DT/SCK) | e.g. `P0`, `P1` | One HX711 per bin |
| [Load Cell](https://www.digikey.in/en/products/detail/sparkfun-electronics/14729/9555603) #1 (Bin 1 load cell) | - | - | 1 |
| [Raspberry PI  Camera](https://www.digikey.in/en/products/detail/seeed-technology-co-ltd/114990838/6578359?s=N4IgTCBcDaIIwFYCcB2AtHALGdA5AIiALoC%2BQA) | - | - | 1|
| [Grove Vision AI Module v2](https://www.digikey.in/en/products/detail/seeed-technology-co-ltd/101021112/22469630) | - | - | 1 |
| [OLED Display](https://www.digikey.in/en/products/detail/adafruit-industries-llc/326/5353680) | I2C | `SDA`, `SCL` | 1 |
| WiFi Module  | UART | `RX` `TX` | |
| [Buzzer](https://www.digikey.in/en/products/detail/soberton-inc/PB-1408-1/1245336) | Digital out | - | |
| [Ultrasonic Sensor](https://www.digikey.in/en/products/detail/adafruit-industries-llc/3942/9658069) | - | - | |
| [PIR Sensor](https://www.digikey.in/en/products/detail/sunfounder/ST0012/22116811?s=N4IgTCBcDaICxwIyILQGUAqAGLiwoDkAREAXQF8g) | - | - | |
| Storage Bin | -| - | |
| Jumper Wires |- | - | |
| [Bread Board](https://www.digikey.in/en/products/detail/busboard-prototype-systems/KIT-BB400-SB400/28714582) | - | - | |


# Detailed Project Description
Manufacturing industries often face production delays due to inaccurate inventory monitoring, unexpected stock shortages, delayed procurement, and inefficient manual inventory management. Most existing inventory systems only notify users after stock levels become critically low, leaving insufficient time to procure replacement materials.

AIoT Inventory Predictor is an edge-based IoT system using the Analog Devices MAX32630FTHR to monitor material consumption and predict potential stockouts before they disrupt manufacturing.
Most inventory systems only track how much stock exists. This project tracks four things instead:

- Identity — is it the right component? (camera)
- Quantity — how many are there, really? (load cell)
- Future need — will there be enough for upcoming production? (AI forecast)

A microcontroller (MAX32630FTHR) reads all sensor readings per bin, pushes the readings to a Firebase Realtime Database over Wi-Fi, and a Python backend on a laptop/server runs image analysis, quantity verification, and a regression-based depletion forecast. When a bin is predicted to run out before its reorder lead time, the system sends an email/WhatsApp alert automatically.

## Features
- Real-time weight-based quantity tracking (HX711 + load cell) pushed to the cloud every 30s
- Camera-based component identification to catch "right bin, wrong part" errors
- RFID-based bin/location verification
- Machine-learning depletion forecasting (rate of consumption → days until empty)
- Automatic reorder alerts via Email and WhatsApp (CallMeBot)
- Web-based GUI dashboard (HTML front end)
- Local OLED + buzzer + LED status indicators on the bin itself

# Schematics
# Code
# CAD/ PCB Design If any *Optional 
# Photo of project
# Video displaying working of Project
# BONUS/OPTIONAL: Video explaining working of the project













