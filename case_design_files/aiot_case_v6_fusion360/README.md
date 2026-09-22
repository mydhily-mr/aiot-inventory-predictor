# AIoT Smart Storage Bin — Case v6

A case sized to your **real sensor geometry** (measured from the STEP files
in `sensors.zip`, not the PDF's numbers — several of those were clearly
wrong, e.g. HC-SR04 listed as 13x13x8cm when the actual part is
45.7 x 27.3 x 19.3mm). Layout follows your annotated photo (`claud_image.PNG`);
styling (rounded "kiosk" body, raised top sensor pod) takes cues from your
reference photo (`image_reference.jpeg`) without copying the previous
`case_design_v4` design.

## What changed in v6

You flagged three real problems after reviewing v5 — here's what was
actually wrong and what changed:

1. **"Camera/ultrasonic openings on top are closed."** True. The v5 holes
   only went 9mm deep from the pod's outer surface, which landed inside
   the pod's own solid mass — there was an ~11mm plug of material still
   blocking the path down into the hollow shaft (confirmed by ray-casting
   straight down through the mesh: the ray hit solid material well before
   reaching the interior). **Fixed**: the lens hole and both ultrasonic eye
   holes now cut from above the pod all the way through into the hollow
   interior. Re-verified with the same ray-cast test — now the only thing
   a ray hits on the way down is the floor. `verify_openings.py` in this
   folder is that test; run it any time you change hole positions.

2. **"PIR should face outside like the OLED, need a hole for that."** The
   PIR dome hole was actually already a real through-hole in v5 (confirmed
   separately by the same ray-cast method), so no change was needed there.
   What follows from your note is stated explicitly in this version:
   the PIR is on the **front face**, and its 24mm dome hole passes
   completely through the wall so the dome sits flush/exposed at the
   outside surface — the same "faces outward" relationship the OLED
   window has.

3. **NEW: hand-detect IR sensor.** Added the IR LM393 (from `sensors.zip`
   — it was in the parts list but unused in v5) mounted on the **inner
   right wall, right at the front bin opening**, sensing face pointing
   across the access gap. A hand reaching in for a component breaks its
   beam, so it can count access events. No PDF/estimated numbers used
   here — this one's dimensions are measured straight from
   `IR LM393.step`.

While fixing #1, a **real but separate bug** turned up and got fixed too:
the NodeMCU side window in v5 never actually cut through the outer wall —
same class of mistake (a cut positioned a few mm off, landing entirely
inside the already-hollow interior instead of touching the wall), also
caught and confirmed fixed by ray-casting. All other hole/pocket sizes are
untouched from v5 — **every sensor's cutout is still sized off its actual
measured dimensions in `sensor_dims.py`, nothing was shrunk**.

## What's in this folder

| File | What it is |
|---|---|
| `sensor_dims.py` | Every sensor dimension used, with a note on where each came from (measured vs. standard vs. estimated). **Read this first if anything doesn't fit** — it's the one file to edit. |
| `build_case.py` → `case_body_v6.step` / `.stl` | The main enclosure: plinth, tower, all sensor cutouts, top sensor pod, IR sensor mount, back opening. |
| `build_platform.py` → `loadcell_platform.step` / `.stl` | The round turntable that sits on the case floor and holds your HX711 load-cell bar (the "weight measurement" mechanism from your reference photo). |
| `build_bin.py` → `storage_bin_optional.step` / `.stl` | **Optional** printable storage bin, sized to sit on the platform and fit inside the case's bin bay. Skip this if you're using your real "Plastic Bin Box" part instead (see below). |
| `build_back_cover.py` → `back_cover_v6.step` / `.stl` | Screw-on back panel, closes the open back used for wiring access. |
| `verify_openings.py` | The ray-cast test that found and confirmed the fixes above. Re-run after any change to hole positions. |
| `render_sensors_assembly.py` → `sensors_placed_preview_v6.png` | Renders a labelled preview with the real sensor CAD (camera, ultrasonic, Grove Vision AI, OLED, buzzer, NodeMCU) placed where they mount, plus sized placeholder blocks for the others. Sanity-check only, not needed for printing. |

All `build_*.py` files are plain **CadQuery** (Python) scripts — this is
how your previous `case_design_v4` was made too, so the workflow is the
same one you already used.

## Opening and editing in Fusion 360

**Fastest path — just print or view:** File → Open → pick any `.step` file.
Fusion imports it as a solid body you can inspect, measure, and
directly-edit (push/pull faces, add fillets, move holes) right away. Do
this for all 4 parts (`case_body_v6`, `loadcell_platform`,
`storage_bin_optional`, `back_cover_v6`) and you have a fully assembled,
print-ready design in Fusion within a minute.

**To actually change dimensions (recommended if any sensor doesn't fit):**
these parts were generated from code, not sketched by hand, so the real
"parametric" source is the `.py` script, not the STEP file. To resize
something:
1. Open `sensor_dims.py`, change the number(s) for that sensor.
2. Re-run the matching `build_*.py` (needs Python 3 + `pip install cadquery`
   — takes a few minutes to install once).
3. Re-import the new `.step` into Fusion (or just re-open it in Design →
   New Design; it replaces the old one).

This is faster and safer than hand-editing a STEP body in Fusion (which
can break if a hole isn't in exactly the right spot), but if you'd rather
work by hand, the STEP import is a completely normal Fusion body —
direct-edit tools work on it as with any solid.

**Your SolidWorks (.SLDPRT) sensor files** — the PIR, the HX711 load-cell
parts, and the plastic storage bin only came as `.SLDPRT`, which this
Python/CadQuery toolchain can't read (proprietary format). **Fusion 360
opens `.SLDPRT` natively** (File → Open → Upload), so before you print:
open those three parts in Fusion, use Inspect → Measure to check their
real size, and compare against the three flagged entries in
`sensor_dims.py` (`PIR_HCSR501`, `LOAD_CELL_HX711_BAR`, `PLASTIC_BIN`) —
those are the only estimated ones; everything else (including the IR
sensor added in v6) came from measuring your actual STEP files.

## Assembly

- Case sits on its plinth. Inner floor is at `PLINTH_T + T` (17mm) above
  the plinth bottom.
- `loadcell_platform` — place its flange centred at **X=0, Y=-9mm**
  (printed as `platform_center_y` when you run `build_case.py`), flange
  bottom flush on the case's inner floor. Four 2.2mm pilot holes in the
  case floor line up with the platform's four 2.4mm clearance holes —
  self-tapping M2 screws hold it down.
- Storage bin (yours, or the optional printed one) rests on the platform's
  90mm platter, roughly centred, visible through the front bin window —
  see "Does the bin actually fit" below.
- Electronics mount in the three front rows, the left-side window, and the
  new right-side IR mount, as labelled directly in `build_case.py`'s
  comments (search for "Row 1", "Row 2", "Row 3", "LEFT SIDE", "RIGHT
  INNER WALL").
- Grove Vision AI V2 mounts on 4 small internal pegs under the top pod,
  next to the camera — no external hole, it just cables to the camera.
- IR LM393 mounts on 2 small internal pegs on the right inner wall, right
  at the bin opening — also fully internal, no external hole; it just
  needs a clear sightline across the opening.
- Close up with `back_cover_v6`, four screws into the lip (3.2mm holes,
  self-tapping screw or M3).

## Does the bin actually fit inside this case?

Yes, checked geometrically:
- The optional printed bin's footprint (62×42mm bottom, 76×54mm top) sits
  on the platform's 90mm-diameter platter with **7.6mm clearance on every
  corner** (its bottom corners are 37.4mm from centre vs. the platter's
  45mm radius).
- Its height (45mm) plus the platform stack under it puts the bin's rim at
  ~83mm above the case floor — well inside the 92mm-tall bin bay (`BASE_H`)
  before the electronics section starts, and lines up with the 96mm-wide,
  76mm-tall front bin window so it's visible/reachable from the front.
- If you're using your real "Plastic Bin Box" part instead: open it in
  Fusion, check it's under roughly 80×58mm at the base and 45mm tall, and
  it'll sit on the platform the same way. If it's bigger than that, the
  two numbers to change are `PLATFORM_R` (currently 50mm radius) in both
  `build_case.py` and `build_platform.py` — keep them equal in both files
  — and `BIN_WINDOW` sizing in `build_case.py`'s step 6.

## Printing tonight

- PLA or PETG, 0.2mm layers, 15–20% infill, 2–3 wall loops is plenty for
  this size.
- Print the case standing up in its natural orientation (as designed) —
  the open back is a plain cutout, not an overhang, so it needs **no
  supports** for the main body.
- Turn supports ON only if your slicer flags the small internal mounting
  pegs (Grove Vision AI, IR sensor) — they're only ~3-4mm, most printers
  handle them fine without.
- The back cover and platform print flat, no supports needed.
- Everything was verified watertight (single manifold solid, checked with
  `trimesh`) before export, so slicers shouldn't report errors — if one
  does, it's almost always fixed by your slicer's "fix mesh" / re-mesh
  option.

## What to double check before printing

The dimensions below are the ones **not** taken from a measured STEP file
— worth a 2-minute check against your physical parts or the SLDPRT files
in Fusion before committing to a print:
- HX711 load-cell bar length/hole spacing (`sensor_dims.py` → `LOAD_CELL_HX711_BAR`)
- PIR HC-SR501 dome size (`PIR_HCSR501`) — very standard, low risk
- Plastic storage bin footprint (`PLASTIC_BIN`) — biggest unknown, since it
  only affects the printed *optional* bin; if you're using your real bin,
  see "Does the bin actually fit" above.
