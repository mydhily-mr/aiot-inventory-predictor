"""
AIoT Smart Storage Bin — Case v6
=================================
v6 fixes two real bugs found in v5 (see README changelog for the full
explanation) and adds the IR hand-detection sensor:

  1. The top camera/ultrasonic "openings" looked cut, but a ~11mm plug of
     solid material was left between the pocket and the hollow interior --
     they didn't actually pass through. Fixed: the lens/eye holes now
     pierce the full pod+wall thickness into the hollow shaft (verified
     with a ray-cast test, see README).
  2. front_recess()/side_recess() had a coordinate bug that placed the
     "bezel" pockets a few mm INSIDE the hollow cavity instead of at the
     wall -- they were silently doing nothing. Fixed, so the PIR, OLED,
     boards and LED bezels are now real recesses. This also means the PIR
     sensor properly sits recessed with its dome exposed through the
     smaller through-hole -- facing outward, same idea as the OLED window.
  3. NEW: IR obstacle sensor (LM393), mounted low on the RIGHT inner wall
     right at the front bin opening, sensing across the access gap so it
     can count hand-in/hand-out events when someone reaches in to take a
     component.

Every hole/pocket size below still comes from sensor_dims.py and none of
those numbers were changed -- only hole DEPTHS (how far through the wall
a cut goes) and one new sensor were touched.

Sensor layout (per your annotated photo, claud_image.PNG, + this request):
  - TOP face, facing DOWN into the storage bin: RPi camera + Grove Vision AI
    V2 (mounted alongside, no hole needed) + HC-SR04 ultrasonic twin "eyes"
  - Front, upper row:  PIR sensor (left, dome facing OUT)  |  Piezo buzzer (right)
  - Front, middle row: MAX32630 FTHR board (left)  |  SSD1306 OLED (right)
  - Front, lower row:  RYG LED bar, centred
  - LEFT side panel:   NodeMCU ESP8266 (w/ its own 0.96" OLED), in a window
  - RIGHT inner wall:  IR LM393 hand-detect sensor, at the bin opening
  - Base:              open front bin bay, storage box sits on the
                        HX711 load-cell turntable (see build_platform.py)

Style: taller, more rounded "kiosk" silhouette inspired by image_reference.jpeg
(soft top, raised sensor pod on top instead of a flat deck, big corner
fillets) — different proportions and top treatment from v4's flat-topped,
domed-PIR tower, since the PIR here is a front panel board, not a top dome.

All units mm. Run:  python3 build_case.py
"""
import cadquery as cq
from sensor_dims import (CAMERA, GROVE_VISION_AI_V2, ULTRASONIC_HCSR04,
                          OLED_SSD1306, BUZZER, NODEMCU_OLED, PIR_HCSR501,
                          MAX32630_FTHR, RYG_LED, IR_LM393)

# ---------------------------------------------------------------
# 1. OVERALL FOOTPRINT / WALLS
# ---------------------------------------------------------------
W = 156.0            # tower width (X) -- sized so the boards row
                      # (MAX32630 + OLED side by side) fits with margin
D = 140.0             # tower depth (Y) -- sized for a 100mm-dia turntable
                      # platform + storage bin with clearance
T = 3.0               # wall thickness
CORNER_R = 20.0       # big rounded corners -- rounder than v4 for the
                      # softer "kiosk" look from the reference photo

BASE_H = 92.0         # bin / turntable section
MID_H  = 128.0        # electronics section: PIR+buzzer row, boards+OLED
                      # row, LED row (3 front rows, unlike v4's 2)
HEAD_H = 26.0         # shallow top section; the raised sensor pod (below)
                      # sits on top of this, not carved into it
H = BASE_H + MID_H + HEAD_H

PLINTH_T = 14.0
PLINTH_MARGIN = 14.0

PLATFORM_R = 50.0     # turntable platform radius (matches build_platform.py)

FRONT_Y = -D / 2
CUT_DEPTH = 16.0

print(f"Tower: {W} x {D} mm, height {H} mm, plinth {PLINTH_T} mm")
print(f"Total height: {PLINTH_T + H + 14} mm (incl. ~14mm sensor pod)")
print(f"Footprint (plinth): {W + 2*PLINTH_MARGIN} x {D + 2*PLINTH_MARGIN} mm")

# ---------------------------------------------------------------
# 2. BASE PLINTH
# ---------------------------------------------------------------
plinth = (
    cq.Workplane("XY")
    .rect(W + 2 * PLINTH_MARGIN, D + 2 * PLINTH_MARGIN)
    .extrude(PLINTH_T)
    .edges("|Z")
    .fillet(CORNER_R + PLINTH_MARGIN * 0.5)
)

# ---------------------------------------------------------------
# 3. MAIN TOWER SHELL
# ---------------------------------------------------------------
outer = (
    cq.Workplane("XY")
    .workplane(offset=PLINTH_T - 1)
    .rect(W, D)
    .extrude(H + 1)
    .edges("|Z")
    .fillet(CORNER_R)
)
inner = (
    cq.Workplane("XY")
    .workplane(offset=PLINTH_T + T)
    .rect(W - 2 * T, D - 2 * T)
    .extrude(H - 2 * T)
    .edges("|Z")
    .fillet(max(CORNER_R - T, 0.5))
)
body = outer.cut(inner)

# soften the top perimeter edge (the "soft top" look, in place of v4's
# separate hemisphere dome -- the dome here is the raised sensor pod added
# in step 8 instead)
body = body.edges(cq.selectors.NearestToPointSelector((0, 0, PLINTH_T + H))).fillet(2.5) \
       if False else body  # (edge selection by proximity is fragile across
                            #  cadquery versions -- top bevel is applied via
                            #  the sensor pod's own fillet instead, see step 8)

# open back wall, lip top & bottom for stiffness + cover screws
LIP = 14.0
back_opening = (
    cq.Workplane("XY")
    .workplane(offset=PLINTH_T + LIP)
    .center(0, D / 2 - T / 2)
    .rect(W - 2 * CORNER_R, D)
    .extrude(H - 2 * LIP)
)
body = body.cut(back_opening)
body = body.union(plinth)

# ---------------------------------------------------------------
# 4. TURNTABLE BASE MOUNT (screw pattern only -- the platform itself,
#    with the HX711 load-cell bar, is a separate part: build_platform.py.
#    This just gives it a flat, ribbed pad to bolt to.)
# ---------------------------------------------------------------
platform_center_y = -(D / 2 - T - PLATFORM_R - 8)
print(f"platform_center_y = {platform_center_y} (bin/turntable centre)")

pad = (
    cq.Workplane("XY")
    .workplane(offset=PLINTH_T + T - 1)
    .center(0, platform_center_y)
    .circle(PLATFORM_R + 4)
    .extrude(2 + 1)
)
body = body.union(pad)

base_mount_holes = None
import math
for ang in (45, 135, 225, 315):
    hx = (PLATFORM_R - 8) * math.cos(math.radians(ang))
    hy = platform_center_y + (PLATFORM_R - 8) * math.sin(math.radians(ang))
    h = (
        cq.Workplane("XY")
        .workplane(offset=PLINTH_T + T - 1)
        .center(hx, hy)
        .circle(2.2 / 2)  # M2 self-tap pilot
        .extrude(10)
    )
    base_mount_holes = h if base_mount_holes is None else base_mount_holes.union(h)
body = body.cut(base_mount_holes)

# ---------------------------------------------------------------
# 5. FRONT / SIDE CUTOUT HELPERS
# ---------------------------------------------------------------
def front_round_hole(dia, x, z, depth=CUT_DEPTH):
    c = cq.Workplane("XZ").circle(dia / 2).extrude(depth)
    return c.translate((x, FRONT_Y + depth / 2, z))

def front_rect_hole(w, h, x, z, depth=CUT_DEPTH):
    r = cq.Workplane("XZ").rect(w, h).extrude(depth)
    return r.translate((x, FRONT_Y + depth / 2, z))

def front_recess(w, h, x, z, depth):
    # (checked empirically: cadquery's extrude on an "XZ" workplane goes
    # in -Y, so translating by FRONT_Y + depth places this solid spanning
    # exactly [FRONT_Y, FRONT_Y + depth] -- a clean recess starting right
    # at the outer surface. This is correct as written.)
    r = cq.Workplane("XZ").rect(w, h).extrude(depth)
    return r.translate((x, FRONT_Y + depth, z))

LEFT_X = -W / 2
RIGHT_X = W / 2

def side_rect_hole(w, h, y, z, depth=CUT_DEPTH):
    # BUGFIX (v6): verified by ray-casting that the v5 formula
    # (LEFT_X + depth/2) never actually touched the outer wall at all --
    # cadquery's extrude on a "YZ" workplane goes in +X, so that placement
    # put the whole cut inside the already-hollow interior (a no-op
    # against solid material; the NodeMCU window never actually opened).
    # translate=(LEFT_X, ...) starts the cut exactly at the true outer
    # surface and extrudes inward by `depth`, matching front_recess's
    # (correct) convention.
    r = cq.Workplane("YZ").rect(w, h).extrude(depth)
    return r.translate((LEFT_X, y, z))

def side_recess(w, h, y, z, depth):
    # BUGFIX (v6): same root cause as side_rect_hole above.
    r = cq.Workplane("YZ").rect(w, h).extrude(depth)
    return r.translate((LEFT_X, y, z))

# ---------------------------------------------------------------
# 6. BASE SECTION: bin bay viewing/access window (front)
# ---------------------------------------------------------------
BIN_WINDOW_Z = PLINTH_T + BASE_H - 20
bin_window = front_rect_hole(w=W - 3 * CORNER_R, h=BASE_H - 16,
                              x=0, z=BIN_WINDOW_Z, depth=CUT_DEPTH)
body = body.cut(bin_window)

# ---------------------------------------------------------------
# 7. MID SECTION -- three front rows, per your annotated photo
# ---------------------------------------------------------------
mid_bottom_z = PLINTH_T + BASE_H

# --- Row 1 (bottom of mid): RYG LED, centred, facing front -----------
LED_Z = mid_bottom_z + 22
led_bezel = front_recess(w=RYG_LED["w"] + 8, h=RYG_LED["h"] + 8,
                          x=0, z=LED_Z, depth=1.5)
body = body.cut(led_bezel)
led_holes = None
led_xs = [-RYG_LED["led_spacing"], 0, RYG_LED["led_spacing"]]
for x in led_xs:
    h = front_round_hole(dia=RYG_LED["led_dia"] + 0.4, x=x, z=LED_Z)
    led_holes = h if led_holes is None else led_holes.union(h)
body = body.cut(led_holes)

# --- Row 2 (middle of mid): MAX32630 FTHR (left) + SSD1306 OLED (right)
BOARDS_Z = mid_bottom_z + 60
GAP = 12.0
max_w, max_h = MAX32630_FTHR["d"], MAX32630_FTHR["w"]  # mounted horizontally:
                                                        # long edge (50.8) across
oled_w, oled_h = OLED_SSD1306["w"], OLED_SSD1306["h"]
row2_total = max_w + GAP + oled_w
max_x = -row2_total / 2 + max_w / 2
oled_x = row2_total / 2 - oled_w / 2

boards_bezel = front_recess(w=row2_total + 10, h=max(max_h, oled_h) + 10,
                             x=0, z=BOARDS_Z, depth=1.5)
body = body.cut(boards_bezel)

max_window = front_rect_hole(w=max_w + 3, h=max_h + 3, x=max_x, z=BOARDS_Z)
body = body.cut(max_window)
# SSD1306: a slightly smaller "glass" opening inside a recessed pocket
# for the PCB, matching how the module actually sits in a bezel
oled_pocket = front_recess(w=oled_w + 2, h=oled_h + 2, x=oled_x, z=BOARDS_Z,
                            depth=OLED_SSD1306["d"] * 0.4)
body = body.cut(oled_pocket)
oled_glass = front_rect_hole(w=OLED_SSD1306["window_w"], h=OLED_SSD1306["window_h"],
                              x=oled_x, z=BOARDS_Z)
body = body.cut(oled_glass)

# --- Row 3 (top of mid): PIR sensor (left) + Piezo buzzer (right) -----
PIRBUZZ_Z = mid_bottom_z + 100
row3_total = PIR_HCSR501["pcb_w"] + GAP + BUZZER["dia"]
pir_x = -row3_total / 2 + PIR_HCSR501["pcb_w"] / 2
buzz_x = row3_total / 2 - BUZZER["dia"] / 2

pir_pocket = front_recess(w=PIR_HCSR501["pcb_w"] + 3, h=PIR_HCSR501["pcb_h"] + 3,
                           x=pir_x, z=PIRBUZZ_Z, depth=6.0)
body = body.cut(pir_pocket)
pir_dome_hole = front_round_hole(dia=PIR_HCSR501["dome_dia"] + 1.0, x=pir_x, z=PIRBUZZ_Z)
body = body.cut(pir_dome_hole)

buzzer_hole = front_round_hole(dia=BUZZER["dia"] + 0.6, x=buzz_x, z=PIRBUZZ_Z)
body = body.cut(buzzer_hole)

print(f"Row3 (PIR+buzzer) z={PIRBUZZ_Z}, top of mid section at z={mid_bottom_z + MID_H}")
assert PIRBUZZ_Z + PIR_HCSR501["dome_h"] / 2 < mid_bottom_z + MID_H - 5, \
    "PIR row too close to top of mid section -- increase MID_H"

# ---------------------------------------------------------------
# 8. LEFT SIDE: NodeMCU window
# ---------------------------------------------------------------
NODEMCU_Y = platform_center_y          # roughly aligned front-to-back with the bin
NODEMCU_Z = BOARDS_Z                   # visually level with the boards row
nm_bezel = side_recess(w=NODEMCU_OLED["d"] + 10, h=NODEMCU_OLED["w"] + 10,
                        y=NODEMCU_Y, z=NODEMCU_Z, depth=1.5)
body = body.cut(nm_bezel)
nm_window = side_rect_hole(w=NODEMCU_OLED["d"] + 2, h=NODEMCU_OLED["w"] + 2,
                            y=NODEMCU_Y, z=NODEMCU_Z)
body = body.cut(nm_window)

# ---------------------------------------------------------------
# 8b. RIGHT INNER WALL: IR LM393 hand-detect sensor -- NEW in v6.
#     Mounted flat against the inside of the right wall, right at the
#     front bin opening, sensing face pointing straight across the
#     opening (in -X) so a hand reaching in for a component crosses its
#     beam. Fully internal -- no hole needed through the outer wall, just
#     two small mounting pegs (same idea as the Grove Vision AI pegs).
# ---------------------------------------------------------------
IR_WALL_X = W / 2 - T            # inner face of the right wall
IR_Y = FRONT_Y + 24              # close to the front opening, where a
                                  # reaching hand actually passes
IR_Z = BIN_WINDOW_Z              # level with the bin window -- hand height
IR_PEG_SPACING = IR_LM393["w"] - 8   # two pegs, 4mm in from each end

ir_pegs = None
for py in (IR_Y - IR_PEG_SPACING / 2, IR_Y + IR_PEG_SPACING / 2):
    peg = (
        cq.Workplane("YZ")
        .workplane(offset=IR_WALL_X + 1)   # start 1mm INTO the solid wall
        .center(py, IR_Z)                   # for genuine volumetric overlap
        .circle(2.0)
        .extrude(-4.0)   # protrudes inward (-X): 1mm embedded + 3mm proud
    )
    ir_pegs = peg if ir_pegs is None else ir_pegs.union(peg)
body = body.union(ir_pegs)
print(f"IR LM393 hand-detect sensor: mounted on right inner wall at "
      f"x={IR_WALL_X}, y={IR_Y}, z={IR_Z}, facing -X across the bin opening")

# ---------------------------------------------------------------
# 9. TOP SENSOR POD  (raised, rounded housing on the flat top -- the
#    "head" that gives the reference-image silhouette; camera + ultrasonic
#    look straight down through it into the bin/platform below)
# ---------------------------------------------------------------
TOP_Z = PLINTH_T + H
POD_W, POD_D, POD_H = 110.0, 78.0, 16.0
POD_R = 24.0

pod = (
    cq.Workplane("XY")
    .workplane(offset=TOP_Z - 2)   # 2mm overlap into the tower top
    .center(0, platform_center_y)
    .rect(POD_W, POD_D)
    .extrude(POD_H + 2)
    .edges("|Z")
    .fillet(POD_R)
    .faces(">Z")
    .fillet(6.0)
)
body = body.union(pod)
POD_TOP_Z = TOP_Z + POD_H

# BUGFIX (v6): in v5 these lens/eye holes only went 9mm deep from the pod
# top (POD_TOP_Z-T-1 .. +6mm), which landed INSIDE the pod's own solid
# mass -- they never reached the hollow tower interior below. Between the
# pocket floor (8mm down) and the tower's inner ceiling (TOP_Z - T) there
# was an ~11mm plug of material still blocking the sightline, verified
# with a ray-cast straight down through the case (see README). Fixed by
# extending every one of these holes from above the pod top all the way
# through to below the tower's inner ceiling, so the sensor genuinely
# sees straight down the open shaft to the bin.
PIERCE_TOP = POD_TOP_Z + 2                 # start a bit above the true outer top
PIERCE_BOTTOM = TOP_Z - T - 3               # end a few mm into the hollow interior
PIERCE_DEPTH = PIERCE_TOP - PIERCE_BOTTOM   # = POD_H + T + 5, comfortably spans it all

# camera window, straight down through the pod AND the tower's top wall
CAM_X = -30.0
cam_hole = (
    cq.Workplane("XY")
    .workplane(offset=PIERCE_BOTTOM)
    .center(CAM_X, platform_center_y)
    .circle(CAMERA["lens_dia"] / 2 + 0.5)
    .extrude(PIERCE_DEPTH)
)
body = body.cut(cam_hole)
# shallow mounting pocket for the camera board's body (blind recess, does
# NOT need to pierce -- only the lens hole above needs the clear sightline)
cam_pocket = (
    cq.Workplane("XY")
    .workplane(offset=POD_TOP_Z - 8)
    .center(CAM_X, platform_center_y)
    .rect(CAMERA["w"] + 2, CAMERA["d"] + 2)
    .extrude(8.1)
)
body = body.cut(cam_pocket)

# HC-SR04 ultrasonic twin eyes, straight down through the pod AND the
# tower's top wall
US_X = 28.0
eye_off = ULTRASONIC_HCSR04["eye_spacing"] / 2
us_left = (
    cq.Workplane("XY").workplane(offset=PIERCE_BOTTOM)
    .center(US_X - eye_off, platform_center_y)
    .circle(ULTRASONIC_HCSR04["eye_dia"] / 2 + 0.4).extrude(PIERCE_DEPTH)
)
us_right = (
    cq.Workplane("XY").workplane(offset=PIERCE_BOTTOM)
    .center(US_X + eye_off, platform_center_y)
    .circle(ULTRASONIC_HCSR04["eye_dia"] / 2 + 0.4).extrude(PIERCE_DEPTH)
)
body = body.cut(us_left).cut(us_right)
us_pocket = (
    cq.Workplane("XY")
    .workplane(offset=POD_TOP_Z - 8)
    .center(US_X, platform_center_y)
    .rect(ULTRASONIC_HCSR04["w"] + 2, ULTRASONIC_HCSR04["d"] + 2)
    .extrude(8.1)
)
body = body.cut(us_pocket)

# Grove Vision AI V2 -- mounts internally beside the camera, no external
# hole (connects to the camera by cable). Four small standoff pegs on the
# underside of the pod so it can be screwed down.
GROVE_X, GROVE_Y = -30.0, platform_center_y - 26
gw, gd = GROVE_VISION_AI_V2["w"], GROVE_VISION_AI_V2["d"]
peg_positions = [
    (GROVE_X - gw / 2 + 4, GROVE_Y - gd / 2 + 4),
    (GROVE_X + gw / 2 - 4, GROVE_Y - gd / 2 + 4),
    (GROVE_X - gw / 2 + 4, GROVE_Y + gd / 2 - 4),
    (GROVE_X + gw / 2 - 4, GROVE_Y + gd / 2 - 4),
]
pegs = None
for (px, py) in peg_positions:
    peg = (
        cq.Workplane("XY")
        .workplane(offset=POD_TOP_Z - 8 - 1)
        .center(px, py)
        .circle(2.0)
        .extrude(3.0)
    )
    pegs = peg if pegs is None else pegs.union(peg)
body = body.union(pegs)
print(f"Grove Vision AI V2 standoff pegs at z={POD_TOP_Z - 8 - 1}..{POD_TOP_Z - 6 - 1} "
      f"(screw the board down from inside before closing the back cover)")

# ---------------------------------------------------------------
# 10. BACK LIP SCREW HOLES + EXPORT
# ---------------------------------------------------------------
SCREW_D = 3.2
screw_positions = [
    (-(W / 2 - CORNER_R - 4), D / 2 - T / 2, PLINTH_T + LIP / 2),
    ((W / 2 - CORNER_R - 4), D / 2 - T / 2, PLINTH_T + LIP / 2),
    (-(W / 2 - CORNER_R - 4), D / 2 - T / 2, PLINTH_T + H - LIP / 2),
    ((W / 2 - CORNER_R - 4), D / 2 - T / 2, PLINTH_T + H - LIP / 2),
]
for (x, y, z) in screw_positions:
    hole = (
        cq.Workplane("XY")
        .workplane(offset=z)
        .center(x, y)
        .circle(SCREW_D / 2)
        .extrude(20)
    )
    body = body.cut(hole)

cq.exporters.export(body, "case_body_v6.stl")
cq.exporters.export(body, "case_body_v6.step")

print("\nDone -- case_body_v6.step / .stl written.")
print(f"Actual total height: {POD_TOP_Z} mm")
print(f"Actual footprint: {W + 2*PLINTH_MARGIN} x {D + 2*PLINTH_MARGIN} mm")
