# AIoT Smart Inventory Case v5: print and assembly guide

This is a new design based on your reference photo: a tower with an open bin bay, an overhanging "head" that holds the electronics, and a base that hides the load cell under the bin. It is not a modified v4. Every sensor opening was sized from your GrabCAD models, or from datasheets where no model was given. I also placed all the sensors in a full 3D assembly and ran a collision check: **0 collisions**.

Overall size is 132 × 179 mm footprint and 226 mm tall (tower 196 mm plus base 30 mm).

---

## 1. What's in this folder

| Folder / file | What it is | Use it for |
|---|---|---|
| `STEP_for_Fusion360/00_CASE_ASSEMBLY_printed_parts_only.step` | All printed parts in their assembled positions (1.8 MB) | **Open this first in Fusion 360** |
| `STEP_for_Fusion360/00_FULL_ASSEMBLY_with_sensors.step` | Same, plus every sensor placed inside (47 MB, slower to open) | Checking the fit visually |
| `STEP_for_Fusion360/01…09_*.step` | Each part on its own | Editing one part |
| `print_ready_STL/*.stl` | Every part already turned the right way for the print bed | **Drag straight into your slicer (Cura / PrusaSlicer / Bambu Studio)** |
| `STL_assembled_position/*.stl` | Same parts in assembled position | Reference only |
| `renders/*.png` | Pictures of the design | Showing people |
| `source_python/` | The script that generates everything (CadQuery) | Changing sizes precisely (see section 7) |

### Parts list

| # | Part | Qty | Print on bed as |
|---|---|---|---|
| 01 | Tower body (sides + head) | 1 | Lying on its **open back** |
| 02 | Base (plinth + load-cell pocket) | 1 | Upright |
| 03 | Faceplate, for a **1.3" OLED** | 1 | Front face down |
| 03b | *Alternative* faceplate for a **0.96" OLED** | only if your OLED is 0.96" | Front face down |
| 04 | Back cover | 1 | Flat |
| 05 | Weighing platform (the bin sits on it) | 1 | Upright |
| 06 | Load-cell spacer | 1 | Flat |
| 07 | Camera plate, **standard Pi camera OV5647** (25 × 24 mm board, like your PDF photo) | 1 | Flat |
| 07b | *Alternative* camera plate for the **wide-angle 32 × 32 mm** OV5647 (your GrabCAD model) | only if you have that one | Flat |
| 08 | Storage bin (pick-bin with a low front, like the blue bin in your reference) | 1 or more | Upright |
| 09 | 4 small standoffs for the MAX32630FTHR | 1 set | Flat |

**Which OLED and camera do you have?** Your GrabCAD OLED model is 1.3", but the photo in your PDF could be either 1.3" or 0.96". The camera in your PDF photo is the small 25 × 24 mm board, but your GrabCAD camera is the 32 × 32 mm wide-angle one. Measure your parts with a ruler before printing and pick the matching 03/03b and 07/07b. Both are small, quick prints.

---

## 2. Opening in Fusion 360

1. Fusion 360 → **File → Open → Open from my computer…** → choose `00_CASE_ASSEMBLY_printed_parts_only.step`. It uploads, then opens with each part as its own component in the browser on the left.
2. **If the model appears lying on its back:** Fusion's default is "Y up" and these files are "Z up". Go to **Preferences → General → Design → Default modeling orientation → Z up**, then re-open. You can also just rotate the view; nothing is actually wrong with the file.
3. **Editing:** STEP files open as solid bodies without the original timeline. You can still edit them directly:
   - **Press Pull** (shortcut Q) on any face moves it. Click the inside of a hole and type a new size.
   - **Move/Copy** (M) on a face moves a hole or window.
   - Sketch on a face, then **Extrude → Cut** to add a hole.
   - To print a part: right-click the body → **Save as Mesh** → STL (or 3MF).
4. The 47 MB full assembly also shows the sensors (green) sitting in their mounts. Use **Inspect → Section Analysis** to look inside.

---

## 3. Printing

**Material:** PLA or PETG. Use black or dark grey for the case to match the reference.

**Settings:** 0.4 mm nozzle, 0.2 mm layers (0.28 mm is fine for the body and base to save time), 3 walls/perimeters, 15 % infill, **supports OFF**, brim ON for the tower body.

Every part is designed to print **without supports** in the orientation in `print_ready_STL`. I checked this with an overhang scan. The remaining overhangs are small bridges (≤ 20 mm) or 45° slopes.

**Bed size needed:** the largest parts are 122 × 196 mm (tower body and back cover) and 132 × 179 mm (base). They fit a 220 × 220 mm bed (Ender-3, Bambu A1/P1, Prusa MK3/MK4). **They will not fit a 180 mm bed** (Bambu A1 mini, Prusa Mini). Tell me if that's your printer and I'll split the tower into two halves.

**Rough time:** these are estimates only; your slicer will give the real figure. About 400 g of PLA in total. Roughly 8–10 h on a fast printer (Bambu, Prusa MK4), or 18–24 h on an Ender-3-class printer at normal speed. Since you're short on time:
- **Start the tower body first.** It's the longest print (about 40 % of the total).
- Next: base → faceplate + camera plate + spacer + standoffs (these can share one plate) → platform → bin → back cover.
- The back cover is only needed to close the case, so it can be printed last.

---

## 4. Hardware list

| Where | Screws |
|---|---|
| Faceplate → tower | 4 × M3 × 10 (self-tapping into the 2.5 mm pilot holes) |
| Back cover → tower | 4 × M3 × 10 |
| Back cover → base | 2 × M3 × 8 |
| Tower → base (through the side walls into the base lip) | 4 × M3 × 8 |
| 1.3" OLED → faceplate (screws from the front, nuts behind) | 4 × M2.5 × 8 + nuts |
| MAX32630FTHR → front of faceplate (through printed standoffs) | 4 × M2.5 × 10 + nuts |
| NodeMCU → inside left wall (into the bosses) | 4 × M3 × 6 |
| Camera plate → head floor | 4 × M3 × 10 + nuts |
| Camera → camera plate | 4 × M2 × 6 (standard camera) or M2.5 × 6 (wide camera) |
| IR sensor → its tab | 1 × M3 × 10 + nut |
| Load cell → base (from underneath, socket head) | 2 × M4 × 12 |
| Platform → spacer → load cell (countersunk, from the top) | 2 × M4 × 16 flat-head |
| Under the base | 4 rubber feet, 12 mm (optional) |
| HC-SR04, PIR, buzzer, RYG LED, Grove Vision AI, HX711 | Located by frames/rails; a dab of **hot glue** holds them |

M3 and M2.5 "laptop" screw kits work well here.

---

## 5. Where every sensor goes

The sizes below are real board sizes. The sizes in your PDF are **Amazon package sizes**, not board sizes (for example, it lists the HC-SR04 as "13 × 13 × 8 cm"; the board itself is 45 × 20 mm), so I didn't use them for fitting.

| Sensor | Location | How it mounts | Size source |
|---|---|---|---|
| **HC-SR501 PIR** | Faceplate top-left; the dome pokes out the front through a 23.4 mm hole | Dome sits in the hole, PCB in a frame behind, hot glue | Datasheet (32.3 × 24.3 PCB, Ø23 dome) |
| **SSD1306 OLED** | Faceplate top-centre, behind a window; pins at the top | Glass drops into a 1.9 mm recess; 4 × M2.5 screws from the front (1.3") | **Your GrabCAD model**: PCB 35.7 × 34, holes 30.4 × 28.6, active area 30.4 × 15.5 |
| **Piezo buzzer module** | Faceplate top-right; buzzer pokes through a 12.4 mm hole, pins pointing down | U-frame behind, hot glue | Your GrabCAD buzzer (Ø12) + PDF (13.3 mm wide module) |
| **RYG LED module** | Faceplate right, vertical slot (like a real traffic light) | LEDs poke through the 32 × 10 slot, hot glue | Estimate. The slot fits 5 mm or 8 mm LEDs at 8–11 mm spacing |
| **MAX32630FTHR** | **Front** of the faceplate (shown off like the board in your reference photo) on 4 mm standoffs; header pins go through the opening behind it for Dupont wires | 4 × M2.5 through **slotted** holes (±1.5 mm) | Feather format 50.8 × 22.86, holes 45.72 × 17.78 |
| **NodeMCU + 0.96" OLED** | Inside the **left side wall** of the head; its OLED shows through a side window; USB end toward the back | 4 × M3 into bosses (4 mm standoff) | **Your GrabCAD model**: PCB 57.8 × 31.5, holes 53.5 × 26.5 |
| **Pi camera OV5647** | Head floor, lens looking straight down at the bin centre | On its camera plate (07 or 07b), which screws onto the floor | PDF photo (25 × 24) / **your GrabCAD** (32 × 32) |
| **Grove Vision AI V2** | Inside the **right side wall**, in two rails; slides in from the back with the camera connector (CSI) toward the front | Rails + dab of glue (the board has no mounting holes) | **Your GrabCAD model**: 40 × 20 |
| **HC-SR04 ultrasonic** | Head floor behind the camera, both "eyes" looking down into the bin through 20 mm holes | Side guides + ledges, hot glue; pins point to the back | **Your GrabCAD model** (the holes also fit the common Ø16 @ 26 mm version) |
| **IR sensor LM393** | Just inside the front edge of the hood, LEDs pointing straight down: a **hand trigger** that fires when someone reaches into the bin | Stands on edge against a tab, 1 × M3; LEDs through two Ø5.6 holes | **Your GrabCAD model** |
| **Load cell** (75 × 12.7 × 12.7, 4 × M4) | In the base pocket, running front-to-back under the bin | Back end bolted to the base riser from below; front end bolted through the spacer to the platform | Drawing in your load-cell zip |
| **HX711** | In the base pocket beside the load cell | Frame (21.8 × 34.8 inside) + tape/glue | Typical 34 × 21 board |

**Load cell direction:** the end with the **wires** goes to the **back** (the fixed end on the riser), and the arrow on the cell points **down**. The platform must only touch the spacer. It has a 3 mm gap to the base on every side, and the fit check confirms that.

**Camera view:** at this height a standard ~62° camera sees roughly the middle 100 × 75 mm of the bin. The wide-angle camera sees the whole bin.

---

## 6. Assembly order

1. **Base:** bolt the load cell onto the riser from underneath (2 × M4 × 12), wire end at the back. Glue the HX711 in its frame. Route its 4 wires out through the notch in the back lip.
2. **Platform:** put the spacer on the front end of the load cell, then the platform on top, and fix with 2 × M4 × 16 countersunk screws from the top. Check that the platform floats freely.
3. **Head floor (inside the tower, from the back):** camera + camera plate, HC-SR04, IR sensor on its tab, and the Grove Vision AI slid into the right-wall rails. Connect the camera ribbon to the Grove board.
4. **Left wall:** NodeMCU (OLED facing the window).
5. **Faceplate:** fit the PIR, OLED, buzzer and RYG LED from behind, and the MAX32630FTHR on the front. Wire everything, then screw the faceplate into the front of the head.
6. Lower the tower onto the base (it slides over the lip) and fix with 4 × M3 through the side walls.
7. Pass the wires from the base up through the slot at the back of the head floor. Fit the back cover (6 × M3); the USB cables come out through its two slots.
8. Put the bin on the platform. The rim stops it sliding around.

---

## 7. Changing sizes precisely (optional)

`source_python/build_case_v5.py` rebuilds every part. All the important numbers are in the PARAMETERS block at the top: bin size, wall thickness, positions of each sensor on the faceplate (`PIR_UV`, `OLED_UV`, …), head floor layout, and so on.

```
pip install cadquery trimesh
python build_case_v5.py                  # writes ./out/*.step and *.stl
python assembly_check.py                 # re-runs the collision check (needs the GrabCAD sensor folders)
```

For example, to make the bin bigger, change `BIN_W, BIN_L, BIN_H`. The platform, base pocket and tower resize automatically.

---

## 8. Measure these before printing

These are the parts I had to size from datasheets rather than from your models:

- **MAX32630FTHR mounting holes.** Assumed Feather standard 45.7 × 17.8 mm; the holes are slotted so small differences are OK.
- **RYG LED module.** The slot takes 3 LEDs up to 8 mm across and 11 mm apart.
- **PIR.** The dome should be about 23 mm across.
- **OLED:** 1.3" or 0.96"? **Camera:** 25 mm or 32 mm board? Pick the matching faceplate and camera plate.
