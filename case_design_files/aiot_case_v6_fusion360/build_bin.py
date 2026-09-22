"""
OPTIONAL printable storage bin.

You already supplied a real "Plastic Bin Box" CAD part in sensors.zip --
that's SolidWorks-only (.SLDPRT) so it couldn't be measured directly in
this session (see sensor_dims.py / README). If you have that physical bin
already, use IT (open the .SLDPRT straight into Fusion 360 -- Fusion reads
SolidWorks parts natively) and skip this file.

This script exists so you have a drop-in, ready-to-print bin TONIGHT even
if you don't have the real part handy: a shallow tapered tray sized to sit
on the 90mm platter from build_platform.py with clearance on every corner,
with finger-pull notches so it lifts out through the front bin window.

Run: python3 build_bin.py
"""
import cadquery as cq
import math
from sensor_dims import PLASTIC_BIN as BIN

BOT_W, BOT_D = BIN["bottom_w"], BIN["bottom_d"]
TOP_W, TOP_D = BIN["top_w"], BIN["top_d"]
HEIGHT = BIN["height"]
WALL_T = 2.0
FLOOR_T = 2.0
FILLET_R = 4.0

PLATTER_D = 90.0  # must match build_platform.py

outer = cq.Workplane("XY").workplane().rect(BOT_W, BOT_D).workplane(offset=HEIGHT).rect(TOP_W, TOP_D)
outer_solid = cq.Workplane("XY").rect(BOT_W, BOT_D).workplane(offset=HEIGHT).rect(TOP_W, TOP_D).loft(ruled=True)

inner_solid = (
    cq.Workplane("XY")
    .workplane(offset=FLOOR_T)
    .rect(BOT_W - 2 * WALL_T, BOT_D - 2 * WALL_T)
    .workplane(offset=HEIGHT - FLOOR_T)
    .rect(TOP_W - 2 * WALL_T, TOP_D - 2 * WALL_T)
    .loft(ruled=True)
)
# extend the cavity a few mm past the outer top face so the cut fully
# opens the rim instead of leaving exactly-coincident top faces (which
# OCC can turn into a degenerate / non-manifold mesh on export)
inner_topcap = (
    cq.Workplane("XY")
    .workplane(offset=HEIGHT - 0.01)
    .rect(TOP_W - 2 * WALL_T, TOP_D - 2 * WALL_T)
    .extrude(5)
)
inner_solid = inner_solid.union(inner_topcap)

bin_body = outer_solid.cut(inner_solid)

# finger-pull handle notches on the two short (D-facing) end walls
notch_w, notch_h = 22.0, 9.0
for sign in (-1, 1):
    notch = (
        cq.Workplane("XZ")
        .rect(notch_w, notch_h)
        .extrude(WALL_T + 4)
        .translate((0, sign * (TOP_D / 2) - (sign * (WALL_T + 2)), HEIGHT - notch_h / 2 - 4))
        .rotate((0, 0, 0), (0, 0, 1), 0)
    )
    # position along Y at the end wall
    notch = (
        cq.Workplane("YZ")
        .rect(notch_w, notch_h)
        .extrude(WALL_T + 4)
        .translate((sign * (TOP_D / 2 - (WALL_T + 2) / 2), 0, HEIGHT - notch_h / 2 - 3))
    )
    bin_body = bin_body.cut(notch)

try:
    bin_body = bin_body.faces(">Z").edges().fillet(1.2)
except Exception:
    pass  # rim fillet is cosmetic only; skip if the loft geometry rejects it

cq.exporters.export(bin_body, "storage_bin_optional.stl")
cq.exporters.export(bin_body, "storage_bin_optional.step")

diag = math.hypot(BOT_W, BOT_D) / 2
margin = PLATTER_D / 2 - diag
print(f"Done -- storage_bin_optional.step / .stl written.")
print(f"Bin bottom {BOT_W}x{BOT_D}mm, top {TOP_W}x{TOP_D}mm, height {HEIGHT}mm")
print(f"Platform clearance: bin bottom half-diagonal {diag:.1f}mm vs platter radius "
      f"{PLATTER_D/2}mm -> {margin:.1f}mm margin on each corner")
assert margin > 2, "Bin footprint too close to the platter edge -- shrink BOT_W/BOT_D"
