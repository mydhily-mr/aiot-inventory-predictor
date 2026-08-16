[← Back to README](../README.md)

## Day -1: Planning
**14 Aug 2026**

### Data Collection

Feedback was gathered from real inventory users about common problems in physical stock rooms:

| # | Identified Issue | Suggested Solution |
|---|---|---|
| 1 | Correct **quantity** doesn't necessarily mean correct **inventory** — e.g. a bin meant to hold 100 × 10 kΩ resistors could instead be filled with 100 × 1 kΩ resistors, and a simple count would never catch it. | Camera-based identification |
| 2 | Manually updating stock in software takes too much time. | Automated sensor updates |
| 3 | It's hard to know exactly where things are physically located. | Digital display + location tracking |

**Current situation vs. our improved model**

Most inventory systems only ask *"How much stock do we have?"*

Our system asks four questions instead:
- Is it the **right component**?
- Is the **quantity** correct?
- Is it stored in the **right location**?
- Will we have **enough for production** when it's needed?

### Implementation Model

![Estimated Flow chart](images/flow_chart.png)
   *Fig 1.1: Estimated Flow chart*

> 📷 **`Fig 1.1`** — System architecture flowchart (Smart Inventory Bin → Camera / Load Cell / RFID → MAX32630FTHR → IoT Link → AI Backend → Image Analysis / Quantity Analysis / Inventory DB → Inventory Verification → Match/Mismatch → Alert & Update)

The flow works like this:

1. **Three sensors feed the controller:**
   - **Camera** → *"What is it?"* (identity)
   - **Load Cell** → *"How many?"* (quantity)
   - **RFID / ID** → *"Which bin?"* (location)
2. All three feed into the **MAX32630FTHR** microcontroller.
3. Data is pushed over an **IoT Link** to an **AI Backend**.
4. The backend runs **Image Analysis**, **Quantity Analysis**, and checks the **Inventory Database** in parallel.
5. Results feed into **Inventory Verification**, which outputs either:
   - **MATCH** → Normal, no action needed.
   - **MISMATCH** → Alert user → Update / Correct the record.

**What each sensor tracks:**

| # | Thing to Track | Description | Solution |
|---|---|---|---|
| 1 | Identity | Is this the correct component? | Camera |
| 2 | Quantity | How many are there? | Load cell + AI estimation |
| 3 | Location | Is the component in the correct bin? | RFID / bin ID |
| 4 | Future availability | Will we have enough for upcoming production? | AI prediction |
| 5 | AI chatbot | For asking questions about reordering | AI bot (GPT-style) |

### Circuit Diagram & Wiring (To: Do)

> 📷 **`image24`** — Wiring/circuit diagram (hand-drawn, Fritzing, or KiCad export) showing the MAX32630FTHR at the center with every peripheral wired in: 3× HX711 → load cells, USB camera, RFID reader, OLED, buzzer, LEDs, temp/humidity sensor. **This is the single most important missing piece for judging** — a system flowchart (above) shows data flow, but judges will also want to see actual pin-level wiring to verify the build is real and reproducible.

**Suggested pin-connection reference table** (fill in with your actual pin numbers once wired):

| Component | Interface | MAX32630FTHR Pin(s) | Notes |
|---|---|---|---|
| HX711 #1 (Bin 1 load cell) | Digital (DT/SCK) | e.g. `P0`, `P1` | One HX711 per bin |
| HX711 #2 (Bin 2 load cell) | Digital (DT/SCK) | e.g. `P2`, `P3` | |
| HX711 #3 (Bin 3 load cell) | Digital (DT/SCK) | e.g. `P4`, `P5` | |
| USB Camera | USB / UART bridge | USB host or external Pi/module | If MAX32630FTHR lacks native USB host, consider offloading camera capture to a companion board (e.g. Raspberry Pi) and sending results over serial/Wi-Fi |
| RFID Reader (e.g. RC522) | SPI | `MOSI`, `MISO`, `SCK`, `SS` | |
| OLED Display | I2C | `SDA`, `SCL` | |
| Temp/Humidity Sensor | I2C or 1-Wire | `SDA`, `SCL` or 1 GPIO | |
| Buzzer | Digital out | 1 GPIO per bin | |
| LEDs | Digital out | 1 GPIO per bin (+ resistor) | |

><!--⚠️ Replace the placeholder pin names above with your actual pinout once you've wired it — this table is a template, not a verified schematic. Consider generating the real diagram in [Fritzing](https://fritzing.org/) (free, beginner-friendly) or [draw.io](https://app.diagrams.net/) and exporting as PNG so it renders inline on GitHub.-->

### Complete Product

**Pipeline:** `Identify → Count → Verify → Predict`
  
> 📷 **`(images/flow_chart.png)`** — Expected Photo of the finished smart storage bin prototype: mini display screens mounted on blue storage bins on a shelf, plus a close-up of the bin housing the electronics (RFID reader, load cell wiring, MAX32630FTHR).

### Components Required

**Core hardware:**

| Hardware | Purpose | Quantity |
|---|---|---|
| MAX32630FTHR | IoT / edge controller | 1 |
| Load cell | Quantity measurement | 3 |
| HX711 | Load-cell interface (amplifier/ADC) | 3 |
| USB camera | Component identification | 1 |
| Temperature/humidity sensor | Environmental monitoring | 1 |
| OLED display | Local status display | 1 |
| Storage bins | Physical inventory containers | 3 |
| Breadboard | Prototyping | 1–2 |
| Wires / connectors | Interconnects | As required |

** Hardware:(To Do)**

| Hardware | Purpose | Quantity |
|---|---|---|
| RFID reader | Automatic bin identification | 3 |
| RFID tags | Bin/item tagging | 3 |
| Buzzer | Critical alert | 3 |
| LEDs | Status indication | 3 |
| Custom PCB | Final prototype consolidation | — |

**Reference builds / inspiration:**

> 📷 **`(images/image3.jpg)`** — "IoT-Based Smart Retail Shelf Monitoring System" demo: bottles on a shelf next to an RFID reader module and an OLED showing item count.

> 📷 **`(images/image4.jpg)`** — Load cell mounted under a shelf bracket (close-up of the sensor and mounting hardware).

> 📷 **`(images/image5.jpg)`** — Tablet dashboard mockup showing inventory info (product, pallets, boxes, occupied range), live temperature/humidity graph, and a weekly inventory bar chart.

> 📷 **`(images/image6.jpg)`** — Warehouse shelving fitted with barcode-labeled bins and IoT gateway/sensor modules along the shelf rail.

> 📷 **`(images/image7.jpg)`** — Example industrial HMI touchscreen dashboard showing device counts and live stats, used as UI/UX inspiration for the local display.



---
[← Back to README](../README.md) · [Next: Software Architecture & Code →](software-architecture.md)
