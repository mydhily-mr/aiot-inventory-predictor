"""
Ground-truth check for every sensor opening in case_body_v6.stl: ray-cast
from well outside the case straight at each one and confirm the ray
actually reaches the hollow interior (or clear air on the far side for the
horizontal ones), instead of trusting that a boolean cut "looked right" in
a screenshot. This is how the v5 -> v6 bugs (top camera/ultrasonic holes
and the NodeMCU side window not actually piercing the wall) were found and
then confirmed fixed. Run this again any time you change hole positions in
build_case.py.

Needs: pip install trimesh rtree
Run:   python3 verify_openings.py
"""
import trimesh
import numpy as np

m = trimesh.load('case_body_v6.stl')

W, D, T = 156.0, 140.0, 3.0
FRONT_Y, LEFT_X, RIGHT_X = -70.0, -78.0, 78.0
platform_center_y = -9.0
mid_bottom_z = 14 + 92
LED_Z = mid_bottom_z + 22
BOARDS_Z = mid_bottom_z + 60
PIRBUZZ_Z = mid_bottom_z + 100
pir_x, buzz_x = -12.5, 22.0
max_x, oled_x = -23.85, 31.4
POD_TOP_Z = 276.0
CAM_X, US_X, eye_off = -30.0, 28.0, 13.0

def cast(name, origin, direction):
    locs, ridx, tidx = m.ray.intersects_location(np.array([origin]), np.array([direction]))
    n = len(locs)
    axis = 2 if direction[2] != 0 else (0 if direction[0] != 0 else 1)
    vals = sorted(locs[:, axis].tolist(), reverse=(direction[axis] < 0)) if n else []
    print(f"{name:35s}: {n} hits, in travel order -> {[round(v,1) for v in vals]}")
    return n, vals

print("=== TOP (vertical rays from far above, straight down) ===")
print("Expect: only the floor slab hits (~19, ~0) -- nothing else, meaning")
print("the pod + top wall are fully open above the hollow shaft.\n")
cast('camera lens hole', (CAM_X, platform_center_y, POD_TOP_Z+50), (0,0,-1))
cast('ultrasonic left eye', (US_X-eye_off, platform_center_y, POD_TOP_Z+50), (0,0,-1))
cast('ultrasonic right eye', (US_X+eye_off, platform_center_y, POD_TOP_Z+50), (0,0,-1))

print("\n=== FRONT (horizontal rays from far in front, through the case and out the open back) ===")
print("Expect: 0 hits -- fully open front-to-back.\n")
cast('PIR dome hole', (pir_x, FRONT_Y-50, PIRBUZZ_Z), (0,1,0))
cast('buzzer hole', (buzz_x, FRONT_Y-50, PIRBUZZ_Z), (0,1,0))
cast('MAX32630 window', (max_x, FRONT_Y-50, BOARDS_Z), (0,1,0))
cast('OLED glass window', (oled_x, FRONT_Y-50, BOARDS_Z), (0,1,0))
cast('RYG LED holes (centre)', (0, FRONT_Y-50, LED_Z), (0,1,0))
cast('bin window', (0, FRONT_Y-50, 86), (0,1,0))

print("\n=== LEFT SIDE (horizontal ray from far left, straight across) ===")
print("Expect: no hit on the left wall (only the far/right wall at 75,78).\n")
cast('NodeMCU window', (LEFT_X-50, platform_center_y, BOARDS_Z), (1,0,0))
