"""
HX711 load-cell turntable platform — the round two-tier base seen in your
image_reference.jpeg (the "Weight Measurement" panel: a round platform on
a load-cell bar, small HX711 amp board visible on the side).

This prints as ONE part: a base flange (screws down into the 4 pilot holes
build_case.py already cut into the case floor, radius PLATFORM_R-8 = 42mm)
carrying a FIXED block (anchors one end of your physical load-cell bar) and
a FREE block (holds the bar's other, load-bearing end and carries the round
platter the storage bin actually rests on). The gap between the two blocks
is sized to your load-cell bar's length so the bar can flex under load like
a normal cantilever scale.

The load-cell bar itself, its HX711 breakout, and its screws are YOUR real
parts (load-cell-hx711-sensor-de-peso...zip) -- SolidWorks-only (.SLDPRT),
so they couldn't be measured directly here (see sensor_dims.py). The bar
dimensions below are the standard "1kg micro load cell" size used in most
HX711 tutorial kits. If your physical part's length or hole spacing is
different, it's a 3-line edit in sensor_dims.py -- everything here reads
from there.

Run: python3 build_platform.py
"""
import cadquery as cq
from sensor_dims import LOAD_CELL_HX711_BAR as BAR

PLATFORM_R = 50.0          # must match build_case.py
FLANGE_R = PLATFORM_R + 4  # matches the case's mounting pad
FLANGE_T = 2.5

BLOCK_H = 9.0               # height of each end block above the flange
BLOCK_W = BAR["section_w"] + 6
BLOCK_D = 14.0               # how far each block extends along the bar axis

BAR_GAP = BAR["length"] - 2 * (BLOCK_D - 3)   # clear span between blocks
                                               # (blocks overlap the bar ends
                                               # by 3mm for screw purchase)

PLATTER_D = 90.0
PLATTER_T = 3.0
RISER_H = 6.0   # extra height on the FREE block up to the platter underside

import math
print(f"Bar length {BAR['length']}mm -> block-to-block gap = {BAR_GAP:.1f}mm")

# --- base flange, screws to the case floor ---------------------------
flange = cq.Workplane("XY").circle(FLANGE_R).extrude(FLANGE_T)
mount_holes = None
for ang in (45, 135, 225, 315):
    hx = (PLATFORM_R - 8) * math.cos(math.radians(ang))
    hy = (PLATFORM_R - 8) * math.sin(math.radians(ang))
    h = cq.Workplane("XY").workplane(offset=-1).center(hx, hy).circle(2.4 / 2).extrude(FLANGE_T + 2)
    mount_holes = h if mount_holes is None else mount_holes.union(h)
flange = flange.cut(mount_holes)

# bar runs along Y: fixed block at -Y (back/anchor), free block at +Y
# (front, load side -- this is where the platter + bin sit)
fixed_y = -(BAR_GAP / 2 + BLOCK_D / 2)
free_y = (BAR_GAP / 2 + BLOCK_D / 2)

def end_block(y_center, height):
    blk = (
        cq.Workplane("XY")
        .workplane(offset=FLANGE_T - 0.5)
        .center(0, y_center)
        .rect(BLOCK_W, BLOCK_D)
        .extrude(height + 0.5)
        .edges("|Z").fillet(1.5)
    )
    # slot pocket for the bar to seat into (open toward the gap)
    slot = (
        cq.Workplane("XY")
        .workplane(offset=FLANGE_T + height - 3.5)
        .center(0, y_center + (BLOCK_D / 4 if y_center < 0 else -BLOCK_D / 4))
        .rect(BAR["section_w"] + 0.6, BLOCK_D)
        .extrude(4)
    )
    blk = blk.cut(slot)
    # two mounting holes for the bar's screws, per hole_pair_spacing
    holes = None
    for hx in (-BAR["hole_pair_spacing"] / 2, BAR["hole_pair_spacing"] / 2):
        h = (
            cq.Workplane("XY")
            .workplane(offset=FLANGE_T - 1)
            .center(hx, y_center)
            .circle(BAR["hole_dia"] / 2)
            .extrude(height + 4)
        )
        holes = h if holes is None else holes.union(h)
    blk = blk.cut(holes)
    return blk

fixed_block = end_block(fixed_y, BLOCK_H)
free_block = end_block(free_y, BLOCK_H + RISER_H)

platform = flange.union(fixed_block).union(free_block)

# platter disc on top of the free block, offset so it's centred over the
# free block but big enough for the storage bin to sit on
platter = (
    cq.Workplane("XY")
    .workplane(offset=FLANGE_T + BLOCK_H + RISER_H - 0.5)
    .center(0, free_y - BLOCK_D / 2)
    .circle(PLATTER_D / 2)
    .extrude(PLATTER_T + 0.5)
)
# a few weight-saving / grip holes in the platter (optional, matches the
# ribbed platter look in the reference photo)
grip = None
for ang in range(0, 360, 45):
    gx = 30 * math.cos(math.radians(ang))
    gy = free_y - BLOCK_D / 2 + 30 * math.sin(math.radians(ang))
    g = (
        cq.Workplane("XY")
        .workplane(offset=FLANGE_T + BLOCK_H + RISER_H - 1)
        .center(gx, gy)
        .circle(4)
        .extrude(PLATTER_T + 2)
    )
    grip = g if grip is None else grip.union(g)
platter = platter.cut(grip)

platform = platform.union(platter)

cq.exporters.export(platform, "loadcell_platform.stl")
cq.exporters.export(platform, "loadcell_platform.step")
print("Done -- loadcell_platform.step / .stl written.")
print(f"Overall footprint: dia {2*FLANGE_R}mm, platter top at z="
      f"{FLANGE_T + BLOCK_H + RISER_H + PLATTER_T:.1f}mm above the case floor")
