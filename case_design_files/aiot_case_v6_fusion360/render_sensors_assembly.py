"""
Sample rendered image with all sensors placed, matching your annotated
layout (claud_image.PNG). Real geometry (camera, Grove Vision AI V2,
ultrasonic, OLED, buzzer, NodeMCU) is the actual STEP models from
sensors.zip. PIR, MAX32630 FTHR, RYG LED and the load-cell bar are shown
as labelled placeholder blocks at their correct size/position (their real
CAD was SolidWorks-only / not supplied, see sensor_dims.py).

This is a sanity-check visual, not a manufacturing drawing -- for the real
interactive model, open the .step files in Fusion 360.
"""
import trimesh
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import sys
sys.path.insert(0, '.')
from sensor_dims import (CAMERA, GROVE_VISION_AI_V2, ULTRASONIC_HCSR04, OLED_SSD1306,
                          BUZZER, NODEMCU_OLED, PIR_HCSR501, MAX32630_FTHR, RYG_LED,
                          IR_LM393)

# ---- geometry constants, mirrored from build_case.py ---------------------
W, D, T, CORNER_R = 156.0, 140.0, 3.0, 20.0
PLINTH_T = 14.0
BASE_H, MID_H, HEAD_H = 92.0, 128.0, 26.0
H = BASE_H + MID_H + HEAD_H
FRONT_Y = -D / 2
LEFT_X = -W / 2
platform_center_y = -9.0
TOP_Z = PLINTH_T + H
POD_H = 16.0
POD_TOP_Z = TOP_Z + POD_H
CAM_X, US_X = -30.0, 28.0
GROVE_X, GROVE_Y = -30.0, platform_center_y - 26
mid_bottom_z = PLINTH_T + BASE_H
LED_Z = mid_bottom_z + 22
BOARDS_Z = mid_bottom_z + 60
PIRBUZZ_Z = mid_bottom_z + 100
GAP = 12.0
max_w, max_h = MAX32630_FTHR["d"], MAX32630_FTHR["w"]
oled_w, oled_h = OLED_SSD1306["w"], OLED_SSD1306["h"]
row2_total = max_w + GAP + oled_w
max_x = -row2_total / 2 + max_w / 2
oled_x = row2_total / 2 - oled_w / 2
row3_total = PIR_HCSR501["pcb_w"] + GAP + BUZZER["dia"]
pir_x = -row3_total / 2 + PIR_HCSR501["pcb_w"] / 2
buzz_x = row3_total / 2 - BUZZER["dia"] / 2

RIGHT_X = W / 2
IR_Y, IR_Z = FRONT_Y + 24, PLINTH_T + BASE_H - 20

# ---- load case + platform + bin (context, translucent) -------------------
case = trimesh.load('case_body_v6.stl')
platform = trimesh.load('loadcell_platform.stl')
platform.apply_translation((0, platform_center_y, PLINTH_T + T))
bin_ = trimesh.load('storage_bin_optional.stl')
bin_.apply_translation((0, platform_center_y - 7, PLINTH_T + T + 20.5))

parts = []  # (mesh, color_rgba, label, label_pos)

def add_real(name, stl_path, pos, rot_axis=None, rot_deg=0, color=(0.2,0.6,0.95,1.0), label=None):
    m = trimesh.load(stl_path)
    if len(m.faces) > 3000:
        m = m.convex_hull  # rendering speed only -- the real mesh is still in the .stl/.step files
    if rot_axis is not None:
        R = trimesh.transformations.rotation_matrix(np.radians(rot_deg), rot_axis)
        m.apply_transform(R)
    m.apply_translation(pos)
    parts.append((m, color, label or name, pos))

def add_box(name, size, pos, color, label=None):
    m = trimesh.creation.box(extents=size)
    m.apply_translation(pos)
    parts.append((m, color, label or name, pos))

# --- TOP: camera + ultrasonic sit on top of the pod, facing down through it
add_real('camera', 'sensor_stl/camera.stl', (CAM_X, platform_center_y, POD_TOP_Z + CAMERA['h']/2 - 2),
          color=(0.15,0.55,0.95,1.0), label='RPi Camera')
add_real('ultrasonic', 'sensor_stl/ultrasonic.stl', (US_X, platform_center_y, POD_TOP_Z + ULTRASONIC_HCSR04['h']/2 - 2),
          color=(0.95,0.55,0.15,1.0), label='HC-SR04 Ultrasonic')
add_real('grove_vision', 'sensor_stl/grove_vision.stl', (GROVE_X, GROVE_Y, POD_TOP_Z - 10),
          rot_axis=[1,0,0], rot_deg=180, color=(0.55,0.15,0.9,1.0), label='Grove Vision AI V2')

# --- MID row 3: PIR (left) + buzzer (right), front face ~y=FRONT_Y
add_box('pir', (PIR_HCSR501['pcb_w'], 8, PIR_HCSR501['pcb_h']),
        (pir_x, FRONT_Y + 4, PIRBUZZ_Z), color=(0.2,0.85,0.3,1.0), label='PIR HC-SR501')
add_real('buzzer', 'sensor_stl/buzzer.stl', (buzz_x, FRONT_Y + 8, PIRBUZZ_Z),
          rot_axis=[1,0,0], rot_deg=90, color=(0.85,0.2,0.2,1.0), label='Piezo Buzzer')

# --- MID row 2: MAX32630 FTHR (left) + OLED (right), front face
add_box('max32630', (max_w, 6, max_h), (max_x, FRONT_Y + 3, BOARDS_Z),
        color=(0.9,0.6,0.1,1.0), label='MAX32630 FTHR')
add_real('oled', 'sensor_stl/oled.stl', (oled_x, FRONT_Y + 6, BOARDS_Z),
          color=(0.1,0.2,0.85,1.0), label='SSD1306 OLED')

# --- MID row 1: RYG LED, centred, front face
add_box('ryg_led', (RYG_LED['w'], 6, RYG_LED['h']), (0, FRONT_Y + 3, LED_Z),
        color=(0.9,0.75,0.1,1.0), label='RYG LED')

# --- LEFT side: NodeMCU
add_real('nodemcu', 'sensor_stl/nodemcu.stl', (LEFT_X + 1, platform_center_y, BOARDS_Z),
          rot_axis=[0,1,0], rot_deg=90, color=(0.15,0.75,0.75,1.0), label='NodeMCU ESP8266')

# --- Load-cell bar, shown at the platform (visual placeholder box, the
#     platform mesh already models the mounting blocks)
add_box('loadcell_bar', (12.7, 55, 6.35),
        (0, platform_center_y, PLINTH_T + T + 12), color=(0.6,0.6,0.6,1.0), label='HX711 Load Cell')

# --- IR LM393 hand-detect sensor, mounted on the right inner wall at the
#     bin opening, sensing face pointing across the opening (-X)
add_box('ir_sensor', (IR_LM393['d'], IR_LM393['w'], IR_LM393['h']),
        (RIGHT_X - 6, IR_Y, IR_Z), color=(0.9,0.2,0.6,1.0), label='IR LM393 (hand detect)')

print("Sensor placements:")
for m, c, label, pos in parts:
    print(f"  {label:22s} at {tuple(round(p,1) for p in pos)}")

# ---------------------------------------------------------------
# Render
# ---------------------------------------------------------------
def render(ax, elev, azim, title, show_case=True, case_alpha=0.12):
    if show_case:
        pc = Poly3DCollection(case.triangles, alpha=case_alpha, facecolor=(0.6,0.6,0.65),
                               edgecolor=None, linewidths=0)
        ax.add_collection3d(pc)
        pcp = Poly3DCollection(platform.triangles, alpha=0.5, facecolor=(0.75,0.75,0.8),
                                edgecolor=None, linewidths=0)
        ax.add_collection3d(pcp)
        pcb = Poly3DCollection(bin_.triangles, alpha=0.55, facecolor=(0.2,0.3,0.85),
                                edgecolor=None, linewidths=0)
        ax.add_collection3d(pcb)
    for m, color, label, pos in parts:
        pc = Poly3DCollection(m.triangles, alpha=1.0, facecolor=color[:3], edgecolor=(0.1,0.1,0.1), linewidths=0.15)
        ax.add_collection3d(pc)
    allpts = np.vstack([case.vertices] + [m.vertices for m, *_ in parts])
    mins, maxs = allpts.min(axis=0), allpts.max(axis=0)
    ctr = (mins + maxs) / 2
    rng = (maxs - mins).max() / 2 * 1.08
    ax.set_xlim(ctr[0]-rng, ctr[0]+rng)
    ax.set_ylim(ctr[1]-rng, ctr[1]+rng)
    ax.set_zlim(max(0, ctr[2]-rng), ctr[2]+rng)
    ax.set_box_aspect((1,1,1))
    ax.view_init(elev=elev, azim=azim)
    ax.set_title(title, fontsize=11)
    ax.set_axis_off()
    try:
        ax.dist = 6.2   # zoom the mplot3d camera in to fill the frame
    except Exception:
        pass

fig = plt.figure(figsize=(11, 7))
ax1 = fig.add_subplot(121, projection='3d')
render(ax1, elev=14, azim=-62, title='Exploded/labelled iso view (case shown translucent)')
ax2 = fig.add_subplot(122, projection='3d')
render(ax2, elev=8, azim=-90, title='Front view (case translucent)')
plt.subplots_adjust(left=0.0, right=1.0, top=0.95, bottom=0.1, wspace=-0.05)

# legend
handles = []
labels_seen = []
for m, color, label, pos in parts:
    if label in labels_seen:
        continue
    labels_seen.append(label)
    handles.append(plt.Line2D([0], [0], marker='s', color='w', markerfacecolor=color[:3], markersize=12))
fig.legend(handles, labels_seen, loc='lower center', ncol=5, fontsize=9, frameon=False)
plt.savefig('sensors_placed_preview_v6.png', dpi=150, pad_inches=0.15)
print("\nwrote sensors_placed_preview_v6.png")
