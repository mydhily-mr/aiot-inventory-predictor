"""
Sensor dimension reference — every number here is either:
  (A) MEASURED from the actual GrabCAD STEP file you supplied (sensors.zip),
      via cadquery's STEP importer + BoundingBox(), i.e. the real geometry, or
  (B) a STANDARD/DATASHEET value for a very common, well-documented module
      (used only where your file was SolidWorks-only (.SLDPRT) and could not
      be opened by the free tools available in this session — SLDPRT is a
      closed SolidWorks format; Fusion 360 CAN open it directly, unlike the
      script here, so these three are the ones worth double-checking first:
      HX711 load cell bar, HC-SR501 PIR, and the Plastic Bin Box).
  The PDF's own numbers were not used where they were inconsistent with the
  real files (e.g. HC-SR04 listed as 13x13x8cm in the PDF, but the actual
  STEP model measures 45.7 x 27.3 x 19.3mm — a normal HC-SR04 size; the PDF
  number looks like a shipping-box size, not the sensor itself).
All values in mm unless noted. "clearance" is what's added to the raw
dimension before cutting the pocket/hole so the real part slides in.
"""

# -- (A) MEASURED from STEP files in sensors.zip --------------------------
CAMERA = dict(source="MEASURED (PiCam_WideAngle v2.step)",
              w=32.1, d=32.1, h=28.2, lens_dia=15.0)

GROVE_VISION_AI_V2 = dict(source="MEASURED (Grove - Vision AI Module V2.step)",
              w=41.7, d=20.0, h=9.3)

ULTRASONIC_HCSR04 = dict(source="MEASURED (Ultrasonic sensor v24.step)",
              w=45.7, d=27.3, h=19.3,
              eye_dia=16.0, eye_spacing=26.0)   # standard HC-SR04 transducer spec, matches board width

OLED_SSD1306 = dict(source="MEASURED (Display_OLED_SSD1306_1.3inch.STEP)",
              w=35.7, d=11.4, h=34.0,           # PCB w x header-depth x PCB h
              window_w=30.0, window_h=16.0)     # visible glass cutout, smaller than PCB

BUZZER = dict(source="MEASURED (Passive Buzzer.step / ActiveBuzzer_TMB12A05.step)",
              dia=13.0, depth=15.0)

NODEMCU_OLED = dict(source="MEASURED (nodemcu wifi oled.stp)",
              w=57.8, d=31.5, h=10.0)           # h padded for USB port/components not in the flat STEP outline

IR_LM393 = dict(source="MEASURED (IR LM393.step)",
              w=42.3, d=14.1, h=8.5)            # mounted vertically on the inner
                                                 # wall, sensing face pointing
                                                 # across the bin opening --
                                                 # counts hand-in/hand-out events

# -- (B) Standard/datasheet values -- SLDPRT-only, verify in Fusion 360 ----
PIR_HCSR501 = dict(source="STANDARD HC-SR501 datasheet (SLDPRT could not be opened here)",
              pcb_w=32.0, pcb_h=24.0, dome_dia=23.0, dome_h=25.0, mount_hole_spacing=28.0)

LOAD_CELL_HX711_BAR = dict(source="STANDARD small bar/beam load cell, e.g. 1kg 'micro load cell' (SLDPRT could not be opened here)",
              length=55.0, section_w=12.7, section_h=6.35,
              hole_dia=4.3, hole_offset_from_end=7.5, hole_pair_spacing=10.0)

PLASTIC_BIN = dict(source="Estimated from reference photo proportions + PDF weight class (SLDPRT could not be opened here); sized to sit with clearance on the 90mm platter in build_platform.py",
              bottom_w=62.0, bottom_d=42.0, top_w=76.0, top_d=54.0, height=45.0)

# -- PDF-only parts (no CAD file supplied at all) --------------------------
MAX32630_FTHR = dict(source="PDF listing (0.9 x 2.0 in), no CAD file supplied",
              w=22.9, d=50.8, h=8.0)

RYG_LED = dict(source="PDF listing (56 x 21 x 11mm), no CAD file supplied",
              w=56.0, d=21.0, h=11.0, led_dia=5.0, led_spacing=15.0)
