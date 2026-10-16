"""Hand rest that holds an Apple Magic Trackpad flush, centred in front of a NuPhy Air75 V2.

Run:  .venv/bin/python handrest.py
Out:  out/handrest_{full,centre,wing_left,wing_right}.{stl,3mf}, out/handrest_wings.3mf,
      out/handrest_full.step

All dimensions in mm. X = width, Y = depth (0 = front edge), Z = up.
"""

from pathlib import Path

from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    BuildSketch,
    Cylinder,
    Locations,
    Mesher,
    Mode,
    Plane,
    Polygon,
    Rectangle,
    RectangleRounded,
    insert,
    extrude,
    export_step,
    export_stl,
    fillet,
)

OUT_DIR = Path(__file__).parent / "out"

# --- Devices ---------------------------------------------------------------
KB_WIDTH = 316.4  # NuPhy Air75 V2
KB_DEPTH = 132.5
KB_HEIGHT = 13.5

TP_WIDTH = 160.0  # Magic Trackpad
TP_DEPTH = 114.9
TP_H_FRONT = 4.9
TP_H_REAR = 10.9
TP_CORNER_R = 8.625  # pocket corner (8.75) minus CLEARANCE; 2021+ and USB-C models, 2015 ones are ~5 mm

# --- Rest ------------------------------------------------------------------
# The trackpad cage follows a fit-tested community tray (KeyboardAndTrackpadTray.stl):
# flat 13 mm top, pocket 160.25 x 114.56 mm with 8.75 mm corners, floor sloped with the
# trackpad so its surface sits level and flush, 5.24 mm back wall with a power-switch notch,
# 130 x 90 mm floor cutout.
TOP_H = 13.0  # flat top of the whole rest
CLEARANCE = 0.125  # per side, around the trackpad
POCKET_D = 114.56  # as fit-tested; Apple lists the trackpad as 114.9 deep
BACK_WALL = 5.24
SWITCH_NOTCH_X = 69.13  # half-round relief in the back wall for the power switch
SWITCH_NOTCH_R = 2.5
SWITCH_NOTCH_DEPTH = 10.99  # below the top, as in the reference
FLOOR_CUTOUT_W = 130.0  # lightening hole under the trackpad; also lets you push it out
FLOOR_CUTOUT_D = 90.0
FLOOR_CUTOUT_R = 15.0
FLOOR_CUTOUT_INSET = 12.18  # from the front of the pocket
CABLE_SLOT_W = 16.0  # gap in the back wall for the USB-C plug
FRONT_MARGIN = 14.0  # rest surface in front of the trackpad
TOP_ROUND = 4.0  # radius on the top front and side edges
PLAN_CORNER = 10.0  # front corners seen from above

WIDTH = KB_WIDTH
POCKET_W = TP_WIDTH + 2 * CLEARANCE
POCKET_R = TP_CORNER_R + CLEARANCE
POCKET_REAR = FRONT_MARGIN + POCKET_D
DEPTH = POCKET_REAR + BACK_WALL

# Pocket floor: a plane under the trackpad's sloped bottom, with the trackpad pushed
# against the front wall. Its top then sits exactly at TOP_H.
SLOPE = (TP_H_REAR - TP_H_FRONT) / TP_DEPTH
TP_Y = FRONT_MARGIN + CLEARANCE  # front edge of the trackpad


def floor_z(y):
    return TOP_H - TP_H_FRONT - SLOPE * (y - TP_Y)


OVERSHOOT = 5.0  # how far cutting tools reach past the part so cuts are clean

# --- Bumpon recesses (under the side wings) --------------------------------
# Common 10 mm bumpons are 2.5-3 mm tall, so they stick out 0.5-1 mm.
FOOT_D = 10.5
FOOT_DEPTH = 2.0  # keeps the top at 13.5-14 mm, level with the keyboard
FOOT_INSET = 15.0

# --- Split into a centre piece and two wings -------------------------------
# The seams run through the full-height wings, not the thin pocket floor.
SPLIT_X = POCKET_W / 2 + 12.0  # 12 mm of solid wall beside the pocket
DOVETAIL_LEN = 8.0
DOVETAIL_NECK = 7.0
DOVETAIL_HEAD = 11.0
DOVETAIL_FIT = 0.15  # removed from each flank of the male tab
DOVETAIL_YS = (14.0, DEPTH * 0.5, DEPTH - 14.0)  # >= 8 mm of wing wall around each socket
WING_GAP = 10.0  # space between the wings when printed on one plate


def body():
    with BuildPart() as part:
        # Rounded front corners, square back corners. A rounded back corner would carry
        # the top fillet onto the back edge, which must stay square to stay flush.
        with BuildSketch():
            RectangleRounded(WIDTH, DEPTH, PLAN_CORNER, align=(Align.CENTER, Align.MIN))
            with Locations((0, DEPTH / 2)):
                Rectangle(WIDTH, DEPTH / 2, align=(Align.CENTER, Align.MIN))
        extrude(amount=TOP_H)

        # Round front and sides; the back edge stays square so it is flush up to the keyboard.
        top = part.faces().sort_by(Axis.Z)[-1]
        fillet([e for e in top.outer_wire().edges() if e.center().Y < DEPTH - 1], TOP_ROUND)

        insert(pocket(), mode=Mode.SUBTRACT)

        # Bumpon recesses in the bottom.
        foot_x = WIDTH / 2 - FOOT_INSET
        with Locations(
            (-foot_x, FOOT_INSET), (foot_x, FOOT_INSET), (-foot_x, DEPTH - FOOT_INSET), (foot_x, DEPTH - FOOT_INSET)
        ):
            Cylinder(FOOT_D / 2, FOOT_DEPTH, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    return part.part


def pocket():
    """Space cut for the trackpad: pocket above the sloped floor, floor cutout, switch notch, cable slot."""
    with BuildPart() as tool:
        with BuildSketch():
            with Locations((0, FRONT_MARGIN)):
                RectangleRounded(POCKET_W, POCKET_D, POCKET_R, align=(Align.CENTER, Align.MIN))
        extrude(amount=TOP_H + OVERSHOOT)
        with BuildSketch(Plane.YZ):
            Polygon(
                (FRONT_MARGIN - OVERSHOOT, floor_z(FRONT_MARGIN - OVERSHOOT)),
                (POCKET_REAR + OVERSHOOT, floor_z(POCKET_REAR + OVERSHOOT)),
                (POCKET_REAR + OVERSHOOT, -OVERSHOOT),
                (FRONT_MARGIN - OVERSHOOT, -OVERSHOOT),
                align=None,
            )
        extrude(amount=POCKET_W, both=True, mode=Mode.SUBTRACT)

        with BuildSketch(Plane.XY.offset(-OVERSHOOT)):
            with Locations((0, FRONT_MARGIN + FLOOR_CUTOUT_INSET)):
                RectangleRounded(FLOOR_CUTOUT_W, FLOOR_CUTOUT_D, FLOOR_CUTOUT_R, align=(Align.CENTER, Align.MIN))
        extrude(amount=TOP_H + 2 * OVERSHOOT)

        with Locations((0, POCKET_REAR, floor_z(POCKET_REAR))):
            Box(CABLE_SLOT_W, BACK_WALL + OVERSHOOT, TOP_H, align=(Align.CENTER, Align.MIN, Align.MIN))
        with Locations((SWITCH_NOTCH_X, POCKET_REAR, TOP_H - SWITCH_NOTCH_DEPTH)):
            Cylinder(SWITCH_NOTCH_R, TOP_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return tool.part


def centre_region(fit):
    """Space kept by the centre piece: |x| < SPLIT_X plus dovetail tabs reaching into each wing."""
    tall = TOP_H + 2 * OVERSHOOT  # from -OVERSHOOT to above the top
    with BuildPart() as region:
        with Locations((0, -OVERSHOOT, -OVERSHOOT)):
            Box(2 * SPLIT_X, DEPTH + 2 * OVERSHOOT, tall, align=(Align.CENTER, Align.MIN, Align.MIN))
        neck = DOVETAIL_NECK / 2 - fit
        head = DOVETAIL_HEAD / 2 - fit
        reach = DOVETAIL_LEN - fit
        for side in (-1, 1):
            root, tip = side * (SPLIT_X - 0.5), side * (SPLIT_X + reach)
            for y in DOVETAIL_YS:
                with BuildSketch(Plane.XY.offset(-OVERSHOOT)):
                    Polygon((root, y - neck), (tip, y - head), (tip, y + head), (root, y + neck), align=None)
                extrude(amount=tall)
    return region.part


def build_parts():
    """Full rest plus the three printable pieces, keyed by output name."""
    full = body()
    centre = full & centre_region(DOVETAIL_FIT)
    wings = sorted((full - centre_region(0)).solids(), key=lambda s: s.center().X)
    return {"full": full, "centre": centre, "wing_left": wings[0], "wing_right": wings[1]}


def wings_plate(parts):
    """Both wings side by side, so they print together on one plate."""
    left, right = parts["wing_left"], parts["wing_right"]
    shift = left.bounding_box().max.X + WING_GAP - right.bounding_box().min.X
    return left, right.translate((shift, 0, 0))


def write_3mf(path, shapes, names):
    mesher = Mesher()
    for shape, name in zip(shapes, names):
        mesher.add_shape(shape, part_number=name)
    mesher.write(str(path))


def main():
    OUT_DIR.mkdir(exist_ok=True)
    parts = build_parts()
    export_step(parts["full"], str(OUT_DIR / "handrest_full.step"))
    for name, part in parts.items():
        export_stl(part, str(OUT_DIR / f"handrest_{name}.stl"))
        write_3mf(OUT_DIR / f"handrest_{name}.3mf", [part], [f"handrest_{name}"])
    write_3mf(OUT_DIR / "handrest_wings.3mf", wings_plate(parts), ["handrest_wing_left", "handrest_wing_right"])

    bb = parts["full"].bounding_box()
    print(f"size {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm")
    print(f"flat top at {TOP_H:.2f} mm, pocket floor {TOP_H - floor_z(TP_Y):.2f}-{TOP_H - floor_z(POCKET_REAR):.2f} mm deep")
    for name, part in parts.items():
        b = part.bounding_box()
        print(f"{name:10} {b.size.X:6.1f} x {b.size.Y:5.1f} mm, valid={part.is_valid}")


if __name__ == "__main__":
    main()
