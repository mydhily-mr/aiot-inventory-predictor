"""
Places every sensor (your GrabCAD models where available, simple accurate-size
blocks where you had no STEP file) into the case, checks for collisions, and
exports a full assembly STEP you can open in Fusion 360 to see how it all fits.
"""
import os, math, sys
import cadquery as cq
from cadquery import Location, Vector
import build_case_v5 as B

SRC = os.environ.get("SENSOR_DIR", "sensors_extracted")   # folder with your unzipped GrabCAD sensor folders
OUT = B.OUT


def imp(rel):
    return cq.importers.importStep(os.path.join(SRC, rel))


def M(wp, rot=(), trans=(0, 0, 0)):
    """rotate (list of (axis, deg)) about origin, then translate"""
    s = wp.val() if isinstance(wp, cq.Workplane) else wp
    s = cq.Compound.makeCompound([x for x in (wp.vals() if isinstance(wp, cq.Workplane) else [wp])])
    for ax, ang in rot:
        axis = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[ax]
        s = s.rotate(Vector(0, 0, 0), Vector(*axis), ang)
    return s.translate(Vector(*trans))


def xform(shape, R, t):
    """apply rotation matrix R (3x3, rows) + translation t"""
    from OCP.gp import gp_Trsf
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    tr = gp_Trsf()
    tr.SetValues(R[0][0], R[0][1], R[0][2], t[0],
                 R[1][0], R[1][1], R[1][2], t[1],
                 R[2][0], R[2][1], R[2][2], t[2])
    return cq.Shape.cast(BRepBuilderAPI_Transform(shape.wrapped, tr, True).Shape())


def bx(x0, x1, y0, y1, z0, z1):
    return B.box(x0, x1, y0, y1, z0, z1).val()


def cz(x, y, z0, z1, d):
    return B.cyl_z(x, y, z0, z1, d).val()


def cy(x, z, y0, y1, d):
    return B.cyl_y(x, z, y0, y1, d).val()


def sensors():
    S = {}
    FPB = B.FP_Y0 + B.FP_T              # faceplate back face (y)
    # ---- OLED 1.3" (GrabCAD) : rotate 180 about X -> glass faces front, pins on top
    u, v = B.OLED_UV
    S["OLED 1.3in (GrabCAD)"] = M(imp("oled-display-ssd1306-1-3inch-1/Display_OLED_SSD1306_1.3inch.STEP"),
                                  [("x", 180)], (u, FPB + 1.2, B.FP_CZ + v))
    # ---- NodeMCU + OLED (GrabCAD): model x->case y, model y-> -case z, model z-> -case x
    nm = imp("nodemcu-esp8266-development-board-with-0-96-inch-oled-display-1/nodemcu wifi oled.stp")
    # rotation that maps (xm,ym,zm) -> (-zm, xm, -ym): rotate -90 about z? do it explicitly:
    s = M(nm, [("x", 90)])            # (x, y, z) -> (x, -z, y)
    s = s.rotate(Vector(0, 0, 0), Vector(0, 0, 1), 90)   # (x, y, z) -> (-y, x, z)  => (z_m, x_m, y_m)
    s = s.rotate(Vector(0, 0, 0), Vector(0, 1, 0), 180)  # (x, y, z) -> (-x, y, -z) => (-z_m, x_m, -y_m)
    mc = B.NODE_MC
    S["NodeMCU + 0.96in OLED (GrabCAD)"] = s.translate(Vector(-B.IN_X + B.NODE_STANDOFF + 39.1,
                                                              B.NODE_CY - mc[0], B.NODE_CZ + mc[1]))
    # ---- Grove Vision AI V2 (GrabCAD) in its cradle, PCB bottom 6 mm above the floor
    g = imp("grove-vision-ai-module-v2-2/Grove - Vision AI Module V2 .step")
    g = cq.Compound.makeCompound(g.vals())
    S["Grove Vision AI V2 (GrabCAD)"] = xform(g, [[0, 0, -1], [-1, 0, 0], [0, 1, 0]],
                                              (B.IN_X - B.GROVE_STANDOFF, B.GROVE_Y, B.GROVE_Z))
    # ---- IR LM393 (GrabCAD): LEDs point down; PCB faces front
    ir = cq.Compound.makeCompound(imp("ir-lm393-1/IR LM393.step").vals())
    S["IR LM393 (GrabCAD)"] = xform(ir, [[0, 0, -1], [0, -1, 0], [-1, 0, 0]],
                                    (B.IR_X + 4.6, B.IR_Y - 86.9, B.Z_C + 161.1))
    # ---- HC-SR04: accurate block model (your GrabCAD STEP is 38 MB - too heavy for the assembly)
    zp = B.Z_F + 2.5
    hc = [bx(-22.85, 22.85, B.US_Y - 10.1, B.US_Y + 10.1, zp, zp + 1.6),
          cz(-11.0, B.US_Y, zp - 14.3, zp, 18.0), cz(11.0, B.US_Y, zp - 14.3, zp, 18.0),
          bx(-5, 5, B.US_Y + 7.5, B.US_Y + 10.1, zp - 2.0, zp),                   # crystal
          bx(-5, 5, B.US_Y + 10.1, B.US_Y + 16.1, zp - 1.5, zp + 1.0)]            # header pins
    S["HC-SR04 (block)"] = cq.Compound.makeCompound(hc)
    # ---- Pi camera OV5647 v1.3 (block): lens down through the camera plate
    zc = B.Z_F + 3.0 + 4.0
    cam = [bx(-12.5, 12.5, B.CAM_Y - 9.46, B.CAM_Y + 14.54, zc, zc + 1.0),
           bx(-4.25, 4.25, B.CAM_Y - 4.25, B.CAM_Y + 4.25, zc - 5.0, zc),
           cz(0, B.CAM_Y, zc - 6.5, zc - 5.0, 7.0),
           bx(-10.5, 10.5, B.CAM_Y + 9.5, B.CAM_Y + 14.54, zc + 1.0, zc + 3.5)]   # FPC connector (back side)
    S["Pi camera OV5647 (block)"] = cq.Compound.makeCompound(cam)
    # ---- PIR HC-SR501 (block): 32.3x24.3 PCB, 24x24 lens base, dia 23 dome
    u, v = B.PIR_UV; x, z = u, B.FP_CZ + v
    dome = cq.Solid.makeSphere(11.5).translate(Vector(x, FPB - 1.0, z))
    dome = dome.intersect(bx(x - 12, x + 12, FPB - 13, FPB - 1.0, z - 12, z + 12))
    pir = [bx(x - 12, x + 12, FPB, FPB + 1.5, z - 12, z + 12),                     # lens flange
           bx(x - 16.15, x + 16.15, FPB + 1.5, FPB + 2.7, z - 12.15, z + 12.15),  # PCB
           bx(x - 10, x + 10, FPB + 2.7, FPB + 12.0, z - 8, z + 8),               # parts on the back
           dome]
    S["PIR HC-SR501 (block)"] = cq.Compound.makeCompound(pir)
    # ---- buzzer module (block): can 12 x 9.5 pokes through, PCB 13.3 x 26 behind, pins down
    u, v = B.BUZ_UV; x, z = u, B.FP_CZ + v
    bz = [cy(x, z, FPB - 9.5, FPB, 12.0),
          bx(x - 6.65, x + 6.65, FPB, FPB + 1.6, z - 19.0, z + 7.0),
          bx(x - 3.8, x + 3.8, FPB + 1.6, FPB + 4.1, z - 27, z - 19)]
    S["Buzzer module (block)"] = cq.Compound.makeCompound(bz)
    # ---- RYG LED module (block, 3 x 5 mm LEDs @ 10 mm)
    u, v = B.RYG_UV; x, z = u, B.FP_CZ + v
    ryg = [bx(x - 5.5, x + 5.5, FPB, FPB + 1.6, z - 17, z + 17)]
    for dz in (-10, 0, 10):
        ryg.append(cy(x, z + dz, FPB - 8.6, FPB, 5.0))
    S["RYG LED module (block)"] = cq.Compound.makeCompound(ryg)
    # ---- MAX32630FTHR on the front on 4 mm standoffs (block)
    u, v = B.MAX_UV; x, z = u, B.FP_CZ + v
    y_board_back = B.FP_Y0 - 4.0
    mx = [bx(x - 25.4, x + 25.4, y_board_back - 1.6, y_board_back, z - 11.43, z + 11.43),
          bx(x - 20.3, x + 20.3, y_board_back - 1.6 - 4.5, y_board_back - 1.6, z + 6, z + 11),  # USB/parts
          bx(x - 20.3, x + 20.3, y_board_back, FPB + 6.0, z + 8.9, z + 11.4),                  # header row
          bx(x - 20.3, x + 20.3, y_board_back, FPB + 6.0, z - 11.4, z - 8.9)]                  # header row
    S["MAX32630FTHR (block)"] = cq.Compound.makeCompound(mx)
    # ---- load cell + HX711 (block)
    S["Load cell 75x12.7 (block)"] = bx(-6.35, 6.35, B.CY - 37.5, B.CY + 37.5, B.LC_Z0, B.LC_Z1)
    S["HX711 (block)"] = cq.Compound.makeCompound(
        [bx(33 - 10.5, 33 + 10.5, B.CY + 12 - 17, B.CY + 12 + 17, B.POCKET_FLOOR_Z, B.POCKET_FLOOR_Z + 1.6),
         bx(33 - 8, 33 + 8, B.CY + 12 - 14, B.CY + 12 + 14, B.POCKET_FLOOR_Z + 1.6, B.POCKET_FLOOR_Z + 12.0)])
    return S


def main():
    parts = {k: f().val() if len(f().solids().vals()) == 1 else cq.Compound.makeCompound(f().solids().vals())
             for k, f in B.all_parts().items()}
    fitted = ["01_tower_body", "02_base", "03_faceplate_oled1.3in", "04_back_cover", "05_weigh_platform",
              "06_loadcell_spacer", "07_camera_plate_std_OV5647", "08_storage_bin"]
    S = sensors()
    print("\n=== sensor vs printed-part collisions (volume mm3) ===")
    bad = 0
    for sn, ss in S.items():
        for pn in fitted:
            try:
                v = sum(sol.intersect(parts[pn]).Volume() for sol in ss.Solids()
                        if sol.BoundingBox().xmax > parts[pn].BoundingBox().xmin - 1)
            except Exception as e:
                v = -1
            if v > 0.5:
                bad += 1
                print(f"  COLLISION  {sn:34s} x {pn:28s} {v:8.1f}")
    print("\n=== printed part vs printed part (volume mm3) ===")
    for i, a in enumerate(fitted):
        for b in fitted[i + 1:]:
            v = parts[a].intersect(parts[b]).Volume()
            if v > 0.5:
                bad += 1
                print(f"  COLLISION  {a:28s} x {b:28s} {v:8.1f}")
    print("\n=== sensor vs sensor ===")
    names = list(S)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            v = sum(sa.intersect(sb).Volume() for sa in S[a].Solids() for sb in S[b].Solids())
            if v > 0.5:
                bad += 1
                print(f"  COLLISION  {a:30s} x {b:30s} {v:8.1f}")
    # gaps that MUST exist for the scale to work
    plat = parts["05_weigh_platform"]
    for pn in ("02_base", "01_tower_body", "04_back_cover"):
        d = plat.distance(parts[pn]) if hasattr(plat, "distance") else None
        print(f"  platform clearance to {pn}: {d:.2f} mm" if d is not None else "")
    binp = parts["08_storage_bin"]
    for pn in ("02_base", "01_tower_body", "04_back_cover"):
        print(f"  bin clearance to {pn}: {binp.distance(parts[pn]):.2f} mm")
    print(f"\nTOTAL collisions: {bad}")
    if "--export" in sys.argv:
        colors = {"01_tower_body": (0.22, 0.24, 0.27), "02_base": (0.30, 0.32, 0.35),
                  "03_faceplate_oled1.3in": (0.12, 0.12, 0.14), "04_back_cover": (0.35, 0.35, 0.38),
                  "05_weigh_platform": (0.85, 0.75, 0.55), "06_loadcell_spacer": (0.9, 0.6, 0.2),
                  "07_camera_plate_std_OV5647": (0.9, 0.5, 0.1), "08_storage_bin": (0.1, 0.45, 0.85)}
        asm = cq.Assembly(name="AIoT_inventory_case_v5")
        for pn in fitted:
            asm.add(parts[pn], name=pn, color=cq.Color(*colors[pn], 1.0))
        for sn, ss in S.items():
            nm = "".join(c if c.isalnum() else "_" for c in sn)
            asm.add(ss, name="SENSOR_" + nm, color=cq.Color(0.1, 0.55, 0.25, 1.0))
        asm.save(os.path.join(OUT, "00_FULL_ASSEMBLY_with_sensors.step"))
        asm2 = cq.Assembly(name="AIoT_case_v5_printed_parts")
        for pn in fitted:
            asm2.add(parts[pn], name=pn, color=cq.Color(*colors[pn], 1.0))
        asm2.save(os.path.join(OUT, "00_CASE_ASSEMBLY_printed_parts_only.step"))
        # sensors as one STL for renders
        cq.exporters.export(cq.Workplane().add(cq.Compound.makeCompound(list(S.values()))),
                            os.path.join(OUT, "_sensors_preview.stl"), tolerance=0.05, angularTolerance=0.3)
        print("assembly exported")


if __name__ == "__main__":
    main()
