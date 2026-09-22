"""
AIoT Smart Inventory Bin -- case v5  (CadQuery, fully parametric)
=================================================================
Style follows the reference photo: a tower with an open bin bay in the
middle, an overhanging "head" on top that carries the electronics, and a
plinth/base that hides the load cell under the bin.

Run:   python build_case_v5.py         (needs:  pip install cadquery)
Out:   ./out/*.step  (open/edit in Fusion 360)   ./out/*.stl  (slice & print)

COORDINATE SYSTEM (all numbers in mm)
    X = left(-) / right(+), centred on the case
    Y = FRONT(0) -> BACK(+).  y = 0 is the front edge of the bin bay.
    Z = up.  z = 0 is the top surface of the base (where the tower sits).

Every size you might want to change is in the PARAMETERS block below.
Sensor sizes come from the GrabCAD models you supplied (measured), or from
the module datasheets where no STEP file was supplied (PIR, load cell,
MAX32630FTHR, buzzer module, RYG LED module) -- see README.
"""
import os
import cadquery as cq

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)

# =====================================================================
# PARAMETERS
# =====================================================================
T = 2.5            # wall thickness of tower / head
CLR = 0.25         # general fit clearance for plates that drop into openings

# ---- storage bin (pick-bin style, like the blue bin in your reference) ----
BIN_W, BIN_L, BIN_H = 90.0, 125.0, 70.0   # outer: width(X), length(Y), height at back
BIN_FRONT_H = 35.0                        # low front wall (the "scoop" opening)
BIN_SLOPE_L = 45.0                        # side walls rise from front height to full height over this length
BIN_WALL, BIN_FLOOR, BIN_R = 2.0, 2.4, 6.0

# ---- weight platform (sits on the load cell) ----
PLAT_RIM_GAP = 0.75                       # bin-to-rim clearance each side
PLAT_RIM_W, PLAT_RIM_H = 2.0, 3.0
PLAT_T = 5.0
PLAT_W = BIN_W + 2 * (PLAT_RIM_GAP + PLAT_RIM_W) + 1.0   # 96.5
PLAT_L = BIN_L + 2 * (PLAT_RIM_GAP + PLAT_RIM_W) + 1.0   # 131.5
PLAT_GAP = 3.0                            # free gap platform <-> pocket wall (must never touch!)

# ---- load cell (bar type, 75 x 12.7 x 12.7, 4 x M4, hole pitch 10 / 44 / 10) ----
LC_L, LC_S = 75.0, 12.7
LC_HOLES = (5.5, 15.5)                    # hole centres measured from each end
M4_CLR = 4.5
RISER_H = 6.0                             # base riser under fixed end
SPACER_H = 5.0                            # printed spacer under platform (loaded end)

# ---- base ----
BASE_H = 30.0
BASE_FLOOR = 3.0
BASE_MARGIN = 5.0                         # base sticks out this much around the tower
BASE_FRONT_EXT = 22.0                     # extra tray in front of the bay (reference look)
LIP_T, LIP_H = 5.0, 10.0                  # locating lip that the tower slides over
BACK_LIP_T = 7.0

# ---- derived plan layout ----
POCKET_W = PLAT_W + 2 * PLAT_GAP          # 102.5
POCKET_L = PLAT_L + 2 * PLAT_GAP          # 137.5
POCKET_Y0 = 4.0
POCKET_Y1 = POCKET_Y0 + POCKET_L
CY = (POCKET_Y0 + POCKET_Y1) / 2          # centre of platform / bin / load cell in Y
W = 2 * (POCKET_W / 2 + 2.0 + LIP_T + 0.3 + T)   # tower outer width  (~122)
W = round(W)
IN_X = W / 2 - T                          # inner half-width
D = POCKET_Y1 + 1.0 + BACK_LIP_T          # tower depth (bay front -> back face)
HOOD = 12.0                               # head overhangs the bay by this much

# ---- heights ----
POCKET_FLOOR_Z = -BASE_H + BASE_FLOOR
LC_Z0 = POCKET_FLOOR_Z + RISER_H          # load cell bottom
LC_Z1 = LC_Z0 + LC_S
PLAT_Z0 = LC_Z1 + SPACER_H                # platform underside
PLAT_Z1 = PLAT_Z0 + PLAT_T                # platform top (bin floor sits here)
BIN_TOP_Z = PLAT_Z1 + BIN_H
Z_C = 110.0                               # bay ceiling (underside of head)
FLOOR_T = T                               # head floor thickness
Z_F = Z_C + FLOOR_T                       # head floor top
H = 196.0                                 # tower height

# ---- outer rounding ----
R_V = 6.0       # vertical front edges & top edges of head
R_HOOD = 3.0    # hood lip edges
R_BAY = 4.0     # bay front vertical edges

# ---- faceplate opening (front of head) ----
FP_X = W / 2 - R_V - 1.5                  # half width of opening (leaves a 1.5+ mm bezel)
FP_Z0, FP_Z1 = Z_C + R_HOOD + 1.0, H - R_V - 1.5
FP_T = 3.0
FP_Y0 = -HOOD                             # faceplate front face
FP_CZ = (FP_Z0 + FP_Z1) / 2

# ---- corner columns (hold faceplate AND back cover screws) ----
COL = 12.5
COL_BOT = (Z_F, Z_F + COL)
COL_TOP = (H - T - COL, H - T)
SCREW_X = FP_X - 3.8
SCREW_ZB, SCREW_ZT = FP_Z0 + 4.8, FP_Z1 - 4.8
M3_PILOT, M3_CLR = 2.5, 3.4
BACK_SCREW_X = 22.0          # back cover -> base lip screws (clear of the wire notch)

# ---- faceplate layout (u = X, v = Z - FP_CZ) ----
PIR_UV = (-35.3, 15.0)
OLED_UV = (1.0, 15.0)
BUZ_UV = (38.0, 20.0)
RYG_UV = (38.0, -19.0)
MAX_UV = (-14.0, -20.0)

# ---- head floor layout ----
CAM_Y = 64.0                   # camera lens position (over bin centre-ish)
US_Y = 110.0                   # HC-SR04 position
GROVE_Y, GROVE_Z = 118.0, 152.0   # Grove Vision AI V2 (on right side wall, board centre)
GROVE_STANDOFF, GROVE_SLOT = 6.0, 2.7
IR_X, IR_Y = 38.0, 4.4         # IR LED axis (hand-trigger, just inside bay front)
WIRE_SLOT = (-40.0, 143.0)     # wire pass-through from base to head

# ---- NodeMCU (on left side of head) ----
NODE_CY, NODE_CZ = 60.0, 151.5
NODE_STANDOFF = 4.0


# =====================================================================
# helpers
# =====================================================================
def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl_z(x, y, z0, z1, d):
    return cq.Workplane("XY").circle(d / 2).extrude(z1 - z0).translate((x, y, z0))


def cyl_y(x, z, y0, y1, d):
    return cq.Workplane("XZ").circle(d / 2).extrude(-(y1 - y0)).translate((x, y0, z))


def cyl_x(y, z, x0, x1, d):
    return cq.Workplane("YZ").circle(d / 2).extrude(x1 - x0).translate((x0, y, z))


def rbox_z(cx, cy, w, l, z0, z1, r):
    """box with rounded vertical edges"""
    return (cq.Workplane("XY").rect(w, l).extrude(z1 - z0)
            .edges("|Z").fillet(r).translate((cx, cy, z0)))


# =====================================================================
# 1. TOWER BODY  (sides + head, one print, printed lying on its BACK)
# =====================================================================
def make_body():
    # side profile in the Y-Z plane, extruded across X
    prof = (cq.Workplane("YZ")
            .polyline([(0, 0), (D, 0), (D, H), (-HOOD, H), (-HOOD, Z_C), (0, Z_C)]).close()
            .extrude(W).translate((-W / 2, 0, 0)))
    # --- rounding: pick edges by position ---
    pick = {"v": [], "h": []}
    for ed in prof.edges().vals():
        bb = ed.BoundingBox()
        c = ed.Center()
        if bb.zlen > 1 and bb.xlen < 1e-3 and bb.ylen < 1e-3:          # vertical edges
            if abs(c.y + HOOD) < 1e-3:
                pick["v"].append(ed)               # head front vertical edges
        elif bb.ylen > 1 and bb.xlen < 1e-3 and bb.zlen < 1e-3:        # edges along Y
            if abs(c.z - H) < 1e-3:
                pick["v"].append(ed)               # top side edges
            elif abs(c.z - Z_C) < 1e-3 and c.y < 0:
                pick["h"].append(ed)               # hood underside side edges
        elif bb.xlen > 1 and bb.ylen < 1e-3 and bb.zlen < 1e-3:        # edges along X
            if abs(c.y + HOOD) < 1e-3 and abs(c.z - H) < 1e-3:
                pick["v"].append(ed)               # top front edge
            elif abs(c.y + HOOD) < 1e-3 and abs(c.z - Z_C) < 1e-3:
                pick["h"].append(ed)               # hood lip
    from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
    mk = BRepFilletAPI_MakeFillet(prof.val().wrapped)
    for ed in pick["v"]:
        mk.Add(R_V, ed.wrapped)
    for ed in pick["h"]:
        mk.Add(R_HOOD, ed.wrapped)
    mk.Build()
    body = cq.Workplane("XY").add(cq.Shape.cast(mk.Shape()))

    # --- hollow it out (outer minus cavities; more robust than OCC shell) ---
    bay = box(-IN_X, IN_X, -HOOD - 5, D + 1, -1, Z_C)                        # bin bay, open front/back/bottom
    head = (cq.Workplane("XY").rect(2 * IN_X, D + 1 - (-HOOD + R_V)).extrude(H - T - Z_F)
            .edges("|Y").edges(">Z").fillet(R_V - T)
            .translate((0, (D + 1 + (-HOOD + R_V)) / 2, Z_F)))                  # head cavity
    opening = box(-FP_X, FP_X, -HOOD - 1, -HOOD + R_V + 0.5, FP_Z0, FP_Z1)     # faceplate opening
    body = body.cut(bay).cut(head).cut(opening)
    # 45-degree transition from the faceplate opening to the wider head cavity
    # (so the bezel prints without support when the body lies on its back)
    y_t = FP_Y0 + FP_T                     # behind the faceplate seat
    zc0 = (FP_Z0 + FP_Z1) / 2
    zc1 = (Z_F + H - T) / 2
    trans = (cq.Workplane("XZ").workplane(offset=-(y_t - 0.01)).center(0, zc0)
             .rect(2 * FP_X, FP_Z1 - FP_Z0)
             .workplane(offset=-5.0).center(0, zc1 - zc0).rect(2 * IN_X, (H - T) - Z_F).loft())
    body = body.cut(trans)
    # (the head floor is what is left between the bay cavity and the head cavity)

    # corner screw columns: a short block behind the faceplate (with a 45-degree
    # tapered end so it prints without support when the body lies on its back)
    # and a short block at the back for the back-cover screws.
    colfront = FP_Y0 + FP_T
    COL_LEN = 18.0
    for sx in (-1, 1):
        for (z0, z1, zin) in ((COL_BOT[0], COL_BOT[1], COL_BOT[1]), (COL_TOP[0], COL_TOP[1], COL_TOP[0])):
            x_wall, x_in = sx * (IN_X + 0.5), sx * (IN_X - COL)
            z_wall = (z0 - 0.5) if zin == z1 else (z1 + 0.5)
            xa, xb = sorted((x_wall, x_in)); za, zb = sorted((z_wall, zin))
            body = body.union(box(xa, xb, colfront, colfront + COL_LEN, za, zb))
            corner_dx = (x_wall - (xa + xb) / 2)
            corner_dz = (z_wall - (za + zb) / 2)
            taper = (cq.Workplane("XZ").rect(xb - xa, zb - za)
                     .workplane(offset=-COL).center(corner_dx, corner_dz).rect(0.4, 0.4).loft()
                     .translate(((xa + xb) / 2, colfront + COL_LEN, (za + zb) / 2)))
            body = body.union(taper)
            body = body.union(box(xa, xb, D - COL_LEN, D, za, zb))
    for sx in (-1, 1):
        for zc in (SCREW_ZB, SCREW_ZT):
            body = body.cut(cyl_y(sx * SCREW_X, zc, colfront - 1, colfront + 14, M3_PILOT))
            body = body.cut(cyl_y(sx * SCREW_X, zc, D - 14, D + 1, M3_PILOT))

    # --- side-wall screws into the base lip (2 per side) ---
    for sx in (-1, 1):
        for yy in (25.0, D - 30.0):
            xa, xb = sorted((sx * (W / 2 - 5), sx * (W / 2 + 1)))
            body = body.cut(cyl_x(yy, LIP_H / 2, xa, xb, M3_CLR))

    # --- head floor features ---
    # camera plate: 30x30 opening + 4 x M3 clearance holes
    body = body.cut(box(-15, 15, CAM_Y - 15, CAM_Y + 15, Z_C - 1, Z_F + 1))
    for dx in (-18, 18):
        for dy in (-18, 18):
            body = body.cut(cyl_z(dx, CAM_Y + dy, Z_C - 1, Z_F + 1, M3_CLR))

    # HC-SR04: two 20 mm holes at 23 mm pitch (fits 16mm cans @26 pitch AND 18mm cans @22 pitch)
    for dx in (-11.5, 11.5):
        body = body.cut(cyl_z(dx, US_Y, Z_C - 1, Z_F + 1, 20.0))
    #   side guides + 2.5 mm support ledges (the cans themselves locate the board front/back;
    #   no front/back walls so the body still prints without supports)
    fx, fy = 46.4 / 2, 21.2 / 2
    frame = (box(-fx - 1.6, -fx, US_Y - fy, US_Y + fy, Z_F, Z_F + 6)
             .union(box(fx, fx + 1.6, US_Y - fy, US_Y + fy, Z_F, Z_F + 6)))
    ledges = (box(-fx, -21.4, US_Y - fy, US_Y + fy, Z_F, Z_F + 2.5)
              .union(box(21.4, fx, US_Y - fy, US_Y + fy, Z_F, Z_F + 2.5)))
    body = body.union(frame).union(ledges)

    # IR LM393 (hand trigger): 2 LED holes + vertical tab with M3 hole.
    # PCB stands on edge (component side facing the centre), LEDs point straight down.
    for dy in (-3.4, 3.4):
        body = body.cut(cyl_z(IR_X, IR_Y + dy, Z_C - 1, Z_F + 1, 5.6))
    tab_x0 = IR_X + 3.1 + 1.5 + 1.2                # LED axis -> PCB front(3.1) -> PCB back(1.5) -> 1.2 gap for solder stubs
    ir_hole_z = Z_C + 8.4 + 24.3
    tab_top = ir_hole_z + 6
    tab = (cq.Workplane("YZ").polyline([(IR_Y - 7.5, Z_F), (IR_Y + 7.5 + (tab_top - Z_F), Z_F),
                                        (IR_Y + 7.5, tab_top), (IR_Y - 7.5, tab_top)]).close()
           .extrude(3).translate((tab_x0, 0, 0)))          # 45-degree gusset = no support needed
    tab = tab.union(cyl_x(IR_Y, ir_hole_z, tab_x0 - 1.2, tab_x0 + 0.1, 6.0))   # contact boss
    tab = tab.cut(cyl_x(IR_Y, ir_hole_z, tab_x0 - 2, tab_x0 + 4, M3_CLR))
    body = body.union(tab)

    # Grove Vision AI V2 on the RIGHT side wall: two L-shaped rails, board slides in
    # from the back (CSI connector end first, towards the camera), pins face the wall.
    gz0, gz1 = GROVE_Z - 10.3, GROVE_Z + 10.3          # board edges (+0.3 clearance)
    xb = IN_X - GROVE_STANDOFF                         # board back face (pin side)
    xf = xb - GROVE_SLOT                               # lip back face
    y_stop = GROVE_Y - 20.0 - 0.5
    y_lip = GROVE_Y - 11.0                     # lips stop short of the CSI connector at the front end
    for (blk, lip, bridge) in (((gz0 - 2.0, gz0 + 1.0), (gz0 - 2.0, gz0 + 1.0), (gz0 - 2.0, gz0)),
                               ((gz1 - 1.0, gz1 + 2.0), (gz1 - 1.0, gz1 + 2.0), (gz1, gz1 + 2.0))):
        body = body.union(box(xb, IN_X + 0.5, y_stop, D, *blk))        # stand-off rail (pins clear the wall)
        body = body.union(box(xf - 1.5, xf, y_lip, D, *lip))           # front lip
        body = body.union(box(xf - 1.5, xb, y_stop, D, *bridge))       # joins lip to rail
    body = body.union(box(xf - 1.5, IN_X + 0.5, y_stop - 2.0, y_stop, gz0 - 2.0, gz1 + 2.0))   # front stop

    # wire pass-through (base -> head)
    body = body.cut(box(WIRE_SLOT[0] - 9, WIRE_SLOT[0] + 9, WIRE_SLOT[1] - 4, WIRE_SLOT[1] + 4, Z_C - 1, Z_F + 1))

    # --- NodeMCU + 0.96" OLED on the LEFT side wall of the head ---
    for (my, mz) in node_holes():
        body = body.union(cyl_x(my, mz, -IN_X - 0.5, -IN_X + NODE_STANDOFF, 6.5))
        body = body.cut(cyl_x(my, mz, -IN_X - 0.2, -IN_X + NODE_STANDOFF + 1, M3_PILOT))
    gy0, gy1, gz0, gz1 = node_glass()
    body = body.cut(box(-W / 2 - 1, -IN_X + 1, gy0 + 0.6, gy1 - 0.6, gz0 + 0.6, gz1 - 0.6))
    return body


# NodeMCU model: PCB X -55.5..2.3, Y -2.5..29 (57.8 x 31.5), holes (-53.5|0.0 , 0.0|26.5),
# 0.96" OLED glass X -29.4..-4.7, Y 2.3..21.7, micro-USB at the X=+2.3 end.
NODE_MC = (-26.6, 13.25)


def node_map(xm, ym):
    """model (x,y) -> case (y,z) ; USB end points to the back, OLED faces outwards"""
    return NODE_CY + (xm - NODE_MC[0]), NODE_CZ - (ym - NODE_MC[1])


def node_holes():
    return [node_map(xm, ym) for xm in (-53.5, 0.0) for ym in (0.0, 26.5)]


def node_glass():
    y0, za = node_map(-29.4, 2.3)
    y1, zb = node_map(-4.7, 21.7)
    return y0, y1, min(za, zb), max(za, zb)


# =====================================================================
# 2. FACEPLATE (front of head) -- printed face-down, no supports
# =====================================================================
def make_faceplate(oled="1.3"):
    fw, fh = 2 * (FP_X - CLR), (FP_Z1 - FP_Z0) - 2 * CLR
    fp = (cq.Workplane("XZ").rect(fw, fh).extrude(-FP_T)
          .translate((0, FP_Y0, FP_CZ)))          # front face at y = FP_Y0
    Y0, Y1 = FP_Y0, FP_Y0 + FP_T

    def at(u, v):
        return u, FP_CZ + v

    def hole(u, v, d):
        x, z = at(u, v)
        return cyl_y(x, z, Y0 - 1, Y1 + 1, d)

    def back_box(u0, u1, v0, v1, h):
        x0, z0 = at(u0, v0); x1, z1 = at(u1, v1)
        return box(x0, x1, Y1 - 0.01, Y1 + h, z0, z1)

    def recess(u0, u1, v0, v1, depth):                     # pocket cut from the back
        x0, z0 = at(u0, v0); x1, z1 = at(u1, v1)
        return box(x0, x1, Y1 - depth, Y1 + 1, z0, z1)

    # corner screws
    for sx in (-1, 1):
        for zc in (SCREW_ZB, SCREW_ZT):
            fp = fp.cut(cyl_y(sx * SCREW_X, zc, Y0 - 1, Y1 + 1, M3_CLR))

    # --- PIR HC-SR501: dome through a 23.4 hole, PCB 32.3x24.3 in a frame ---
    u, v = PIR_UV
    fp = fp.cut(hole(u, v, 23.4))
    pf = back_box(u - 16.5 - 1.2, u + 16.5 + 1.2, v - 12.5 - 1.2, v + 12.5 + 1.2, 6).cut(
        back_box(u - 16.5, u + 16.5, v - 12.5, v + 12.5, 7))
    fp = fp.union(pf)

    # --- OLED ---
    u, v = OLED_UV
    if oled == "1.3":
        # measured from your GrabCAD model: PCB 35.7x34, glass 35x23 (1.7 thick),
        # active area 30.4x15.5, holes dia 3.1 at 30.4 x 28.6, header pins at the TOP
        gv0, gv1 = v - 12.4, v + 10.6          # glass
        av0, av1 = v - 6.9, v + 8.6            # active area
        fp = fp.cut(recess(u - 17.8, u + 17.8, gv0 - 0.3, gv1 + 0.3, 1.9))
        x0, z0 = at(u - 15.9, av0 - 0.5); x1, z1 = at(u + 15.9, av1 + 0.5)
        fp = fp.cut(box(x0, x1, Y0 - 1, Y1 + 1, z0, z1))
        fp = fp.cut(recess(u - 6.5, u + 6.5, v + 13.3, v + 16.8, 1.9))   # relief for header-pin stubs
        for hu in (-15.2, 15.2):
            for hv in (13.8, -14.8):
                fp = fp.cut(hole(u + hu, v + hv, 2.8))      # M2.5 screws from the front
    else:
        # 0.96" SSD1306 (27.3 x 27.8 PCB, glass ~26.7 x 19.3, active 21.7 x 10.9)
        gv0, gv1 = v - 11.0, v + 9.0
        fp = fp.cut(recess(u - 13.7, u + 13.7, gv0, gv1, 1.9))
        x0, z0 = at(u - 11.6, v - 5.5); x1, z1 = at(u + 11.6, v + 7.5)
        fp = fp.cut(box(x0, x1, Y0 - 1, Y1 + 1, z0, z1))
        # PCB locating frame (no holes -> hot glue at the corners)
        fp = fp.union(back_box(u - 14.1 - 1.6, u + 14.1 + 1.6, v - 14.3 - 1.6, v + 14.3 + 1.6, 3).cut(
            back_box(u - 14.1, u + 14.1, v - 14.3, v + 14.3, 4)))

    # --- buzzer module (12 mm buzzer, 13.3 wide PCB, pins pointing down) ---
    u, v = BUZ_UV
    fp = fp.cut(hole(u, v, 12.4))
    bf = back_box(u - 7.0 - 1.6, u + 7.0 + 1.6, v - 27.0, v + 7.5 + 1.6, 5).cut(
        back_box(u - 7.0, u + 7.0, v - 28.0, v + 7.5, 6))
    fp = fp.union(bf)

    # --- RYG traffic-light LED module: vertical slot, LEDs poke through ---
    u, v = RYG_UV
    x, z = at(u, v)
    fp = fp.cut(cq.Workplane("XZ").slot2D(32, 10, 90).extrude(-(FP_T + 2)).translate((x, Y0 - 1, z)))

    # --- MAX32630FTHR mounted on the FRONT (like the board in your reference) ---
    # Feather format 50.8 x 22.86; holes 45.72 x 17.78. Holes are slotted +/-1.5 mm in X
    # so they still line up if your board's holes are slightly different.
    u, v = MAX_UV
    x0, z0 = at(u - 20.5, v - 13); x1, z1 = at(u + 20.5, v + 13)
    fp = fp.cut(box(x0, x1, Y0 - 1, Y1 + 1, z0, z1))           # opening for header pins / Dupont plugs
    for hu in (-22.86, 22.86):
        for hv in (-8.89, 8.89):
            x, z = at(u + hu, v + hv)
            fp = fp.cut(cq.Workplane("XZ").slot2D(5.8, 2.8, 0).extrude(-(FP_T + 2)).translate((x, Y0 - 1, z)))
    return fp


# =====================================================================
# 3. BACK COVER -- printed flat
# =====================================================================
def make_back_cover():
    t = 2.5
    bc = (cq.Workplane("XZ").center(0, H / 2).rect(W, H).extrude(-t)
          .edges("|Y").edges(">Z").fillet(R_V - 0.01)
          .translate((0, D, 0)))
    for sx in (-1, 1):
        for zc in (SCREW_ZB, SCREW_ZT):
            bc = bc.cut(cyl_y(sx * SCREW_X, zc, D - 1, D + t + 1, M3_CLR))
        bc = bc.cut(cyl_y(sx * BACK_SCREW_X, LIP_H / 2, D - 1, D + t + 1, M3_CLR))
    # USB cable entry (head) + cable entry low (optional external power)
    bc = bc.cut(cq.Workplane("XZ").slot2D(16, 10, 0).extrude(-(t + 2)).translate((28, D - 1, Z_F + 20)))
    bc = bc.cut(cq.Workplane("XZ").slot2D(16, 10, 0).extrude(-(t + 2)).translate((-28, D - 1, Z_F + 20)))
    # vents in the head area
    for i in range(7):
        x = -30 + i * 10
        bc = bc.cut(cq.Workplane("XZ").slot2D(30, 4, 90).extrude(-(t + 2)).translate((x, D - 1, Z_F + 55)))
    return bc


# =====================================================================
# 4. BASE (plinth + load-cell pocket) -- printed upright
# =====================================================================
def make_base():
    bx = W / 2 + BASE_MARGIN
    by0, by1 = -BASE_FRONT_EXT, D + 2.5 + BASE_MARGIN
    base = rbox_z(0, (by0 + by1) / 2, 2 * bx, by1 - by0, -BASE_H, 0, 8.0)
    base = base.faces(">Z").edges().chamfer(1.5)
    # pocket for platform + load cell + HX711
    base = base.cut(box(-POCKET_W / 2, POCKET_W / 2, POCKET_Y0, POCKET_Y1, POCKET_FLOOR_Z, 1))
    # U-shaped locating lip (left, right, back) that the tower slides over
    lo = IN_X - 0.3
    lip = (box(-lo, lo, 0, D, 0, LIP_H)
           .cut(box(-lo + LIP_T, lo - LIP_T, -1, D - BACK_LIP_T, -1, LIP_H + 1)))
    lip = lip.cut(box(-lo + LIP_T - 0.1, lo - LIP_T + 0.1, -1, POCKET_Y1 + 0.5, -1, LIP_H + 1))
    base = base.union(lip)
    # lip screw holes: sides (from tower walls) and back (from back cover)
    for sx in (-1, 1):
        for yy in (25.0, D - 30.0):
            xa, xb = sorted((sx * (lo - LIP_T - 1), sx * (lo + 1)))
            base = base.cut(cyl_x(yy, LIP_H / 2, xa, xb, M3_PILOT))
        base = base.cut(cyl_y(sx * BACK_SCREW_X, LIP_H / 2, D - 12, D + 1, M3_PILOT))
    # wire notch through back lip
    base = base.cut(box(WIRE_SLOT[0] - 5, WIRE_SLOT[0] + 5, POCKET_Y1 - 1, D + 1, 1.5, LIP_H + 1))
    # load-cell riser under the FIXED (back, wire) end
    ly1 = CY + LC_L / 2
    riser = box(-7.5, 7.5, ly1 - 21, ly1 + 0.5, POCKET_FLOOR_Z - 0.01, LC_Z0)
    base = base.union(riser)
    for hy in LC_HOLES:
        yy = ly1 - hy
        base = base.cut(cyl_z(0, yy, -BASE_H - 1, LC_Z0 + 1, M4_CLR))
        base = base.cut(cyl_z(0, yy, -BASE_H - 1, -BASE_H + 4.0, 8.2))     # counterbore for M4 head
    # HX711 locating frame (board ~34 x 21) beside the load cell
    HXX, HXY = 33.0, CY + 12.0                     # board 21 x 34, long side along Y
    hx = box(HXX - 12.1, HXX + 12.1, HXY - 18.6, HXY + 18.6, POCKET_FLOOR_Z - 0.01, POCKET_FLOOR_Z + 4).cut(
        box(HXX - 10.9, HXX + 10.9, HXY - 17.4, HXY + 17.4, POCKET_FLOOR_Z, POCKET_FLOOR_Z + 5))
    hx = hx.cut(box(HXX - 7, HXX + 7, HXY - 20, HXY - 16, POCKET_FLOOR_Z + 1, POCKET_FLOOR_Z + 5))  # wire gaps
    hx = hx.cut(box(HXX - 7, HXX + 7, HXY + 16, HXY + 20, POCKET_FLOOR_Z + 1, POCKET_FLOOR_Z + 5))
    base = base.union(hx)
    # rubber-feet recesses
    for sx in (-1, 1):
        for yy in (by0 + 14, by1 - 14):
            base = base.cut(cyl_z(sx * (bx - 14), yy, -BASE_H - 1, -BASE_H + 1.0, 12.5))
    return base


# =====================================================================
# 5. PLATFORM (on load cell) + spacer -- printed flat
# =====================================================================
def make_platform():
    p = rbox_z(0, CY, PLAT_W, PLAT_L, PLAT_Z0, PLAT_Z1, 5.0)
    rim_o = rbox_z(0, CY, PLAT_W, PLAT_L, PLAT_Z1 - 0.01, PLAT_Z1 + PLAT_RIM_H, 5.0)
    rim_i = rbox_z(0, CY, BIN_W + 2 * PLAT_RIM_GAP, BIN_L + 2 * PLAT_RIM_GAP,
                   PLAT_Z1 - 1, PLAT_Z1 + PLAT_RIM_H + 1, BIN_R + PLAT_RIM_GAP)
    p = p.union(rim_o.cut(rim_i))
    ly0 = CY - LC_L / 2
    for hy in LC_HOLES:
        yy = ly0 + hy
        p = p.cut(cyl_z(0, yy, PLAT_Z0 - 1, PLAT_Z1 + 1, M4_CLR))
        # countersink (90 deg, M4 flat head dia 8)
        cs = cq.Solid.makeCone(2.25, 4.85, 2.6, cq.Vector(0, yy, PLAT_Z1 - 2.6), cq.Vector(0, 0, 1))
        p = p.cut(cq.Workplane("XY").add(cs))
    return p


def make_spacer():
    ly0 = CY - LC_L / 2
    s = box(-LC_S / 2, LC_S / 2, ly0, ly0 + 20.5, LC_Z1, PLAT_Z0)
    for hy in LC_HOLES:
        s = s.cut(cyl_z(0, ly0 + hy, LC_Z1 - 1, PLAT_Z0 + 1, M4_CLR))
    return s


# =====================================================================
# 6. CAMERA PLATES (two versions) -- printed flat, standoffs up
# =====================================================================
def make_camera_plate(kind="std"):
    t = 3.0
    pl = rbox_z(0, CAM_Y, 44, 44, Z_F, Z_F + t, 4.0)
    for dx in (-18, 18):
        for dy in (-18, 18):
            pl = pl.cut(cyl_z(dx, CAM_Y + dy, Z_F - 1, Z_F + t + 1, M3_CLR))
    if kind == "std":
        # Raspberry Pi camera OV5647 v1.3 style (your PDF photo / Grove kit camera):
        # 25 x 24 PCB, M2 holes 21 x 12.5, lens 8.5x8.5 block.  Lens is centred on the plate.
        pl = pl.cut(cyl_z(0, CAM_Y, Z_F - 1, Z_F + t + 1, 12.8))
        so = 4.0
        for hx in (-10.5, 10.5):
            for hy in (-7.46, 5.04):          # ribbon connector end faces +Y (towards the Grove board)
                pl = pl.union(cyl_z(hx, CAM_Y + hy, Z_F + t - 0.01, Z_F + t + so, 4.5))
                pl = pl.cut(cyl_z(hx, CAM_Y + hy, Z_F + t - 1, Z_F + t + so + 1, 1.8))
    else:
        # wide-angle OV5647 (your GrabCAD model): 32.1 x 32.1 PCB, holes dia 2.5 at 27.1 x 27.1,
        # lens ring dia 21.5 goes through the plate.
        pl = pl.cut(cyl_z(0, CAM_Y, Z_F - 1, Z_F + t + 1, 23.0))
        so = 3.0
        for hx in (-13.55, 13.55):
            for hy in (-13.55, 13.55):
                pl = pl.union(cyl_z(hx, CAM_Y + hy, Z_F + t - 0.01, Z_F + t + so, 5.0))
                pl = pl.cut(cyl_z(hx, CAM_Y + hy, Z_F + t - 1, Z_F + t + so + 1, 2.2))
    return pl


# =====================================================================
# 7. STORAGE BIN (pick-bin with low front, like the reference) -- printed upright
# =====================================================================
def make_bin():
    y0 = CY - BIN_L / 2
    z0 = PLAT_Z1
    outer = rbox_z(0, CY, BIN_W, BIN_L, z0, z0 + BIN_H, BIN_R)
    inner = rbox_z(0, CY, BIN_W - 2 * BIN_WALL, BIN_L - 2 * BIN_WALL, z0 + BIN_FLOOR, z0 + BIN_H + 1,
                   BIN_R - BIN_WALL)
    b = outer.cut(inner)
    # sloped cut: front wall low, rising to full height at BIN_SLOPE_L
    wedge = (cq.Workplane("YZ")
             .polyline([(y0 - 1, z0 + BIN_FRONT_H), (y0 + BIN_SLOPE_L, z0 + BIN_H + 0.01),
                        (y0 - 1, z0 + BIN_H + 5)]).close()
             .extrude(BIN_W + 2).translate((-BIN_W / 2 - 1, 0, 0)))
    b = b.cut(wedge)
    # round the top of the front wall a little (finger grip)
    # label window on the front wall
    b = b.cut(box(-25, 25, y0 - 1, y0 + 0.7, z0 + 8, z0 + 24))
    # small drain/tare holes? no - keep solid floor. Add 4 feet pads so it sits flat on the rim floor
    return b


# =====================================================================
# 8. SMALL PARTS: 4 standoff tubes for the front-mounted MAX32630FTHR
# =====================================================================
def make_small_parts():
    parts = None
    for i in range(4):
        tube = cyl_z(i * 9.0, 0, 0, 4.0, 5.0).cut(cyl_z(i * 9.0, 0, -1, 5.0, 2.8))
        parts = tube if parts is None else parts.union(tube)
    return parts


def all_parts():
    return {
        "01_tower_body": make_body,
        "02_base": make_base,
        "03_faceplate_oled1.3in": lambda: make_faceplate("1.3"),
        "03b_faceplate_oled0.96in_ALT": lambda: make_faceplate("0.96"),
        "04_back_cover": make_back_cover,
        "05_weigh_platform": make_platform,
        "06_loadcell_spacer": make_spacer,
        "07_camera_plate_std_OV5647": lambda: make_camera_plate("std"),
        "07b_camera_plate_wide_ALT": lambda: make_camera_plate("wide"),
        "08_storage_bin": make_bin,
        "09_MAX32630_standoffs_x4": make_small_parts,
    }


# how each part should lie on the print bed: list of (axis, degrees) rotations
PRINT_ORIENT = {
    "01_tower_body": [("x", -90)],        # lying on its open BACK -> no supports
    "03_faceplate_oled1.3in": [("x", 90)],  # front face down
    "03b_faceplate_oled0.96in_ALT": [("x", 90)],
    "04_back_cover": [("x", 90)],         # flat
}


def export_print_ready(name, wp):
    d = os.path.join(OUT, "print_ready_STL")
    os.makedirs(d, exist_ok=True)
    s = wp.val() if len(wp.solids().vals()) == 1 else cq.Compound.makeCompound(wp.solids().vals())
    for ax, ang in PRINT_ORIENT.get(name, []):
        axis = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[ax]
        s = s.rotate(cq.Vector(0, 0, 0), cq.Vector(*axis), ang)
    bb = s.BoundingBox()
    s = s.translate(cq.Vector(-(bb.xmin + bb.xmax) / 2, -(bb.ymin + bb.ymax) / 2, -bb.zmin))
    path = os.path.join(d, name + ".stl")
    cq.exporters.export(cq.Workplane().add(s), path, tolerance=0.02, angularTolerance=0.15)
    try:
        import trimesh
        m = trimesh.load(path)
        keep = [b for b in m.split(only_watertight=False) if len(b.faces) > 8]
        trimesh.util.concatenate(keep).export(path)
    except ImportError:
        pass
    bb = s.BoundingBox()
    return bb.xlen, bb.ylen, bb.zlen


if __name__ == "__main__":
    import time
    print(f"Tower W x D x H = {W} x {D:.1f} (+{HOOD} hood) x {H}")
    print(f"Platform {PLAT_W} x {PLAT_L}, top z={PLAT_Z1:.2f}; bin top z={BIN_TOP_Z:.2f}; ceiling z={Z_C}")
    parts = all_parts()
    built = {}
    for name, fn in parts.items():
        t = time.time()
        wp = fn()
        built[name] = wp
        s = wp.val()
        print(f"{name:34s} valid={s.isValid()} solids={len(wp.solids().vals())} vol={s.Volume()/1000:.1f}cm3  {time.time()-t:.1f}s")
        cq.exporters.export(wp, os.path.join(OUT, name + ".step"))
        stl = os.path.join(OUT, name + ".stl")
        cq.exporters.export(wp, stl, tolerance=0.02, angularTolerance=0.15)
        try:   # drop stray sliver triangles the tessellator sometimes leaves at fillet corners
            import trimesh
            m = trimesh.load(stl)
            keep = [b for b in m.split(only_watertight=False) if len(b.faces) > 8]
            trimesh.util.concatenate(keep).export(stl)
        except ImportError:
            pass
        sz = export_print_ready(name, wp)
        print(f"{'':34s} print size on bed: {sz[0]:.0f} x {sz[1]:.0f} mm, height {sz[2]:.0f} mm")
