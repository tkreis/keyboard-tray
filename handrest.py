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
TP_CORNER_R = 8.0  # measure yours; pocket corners follow this

# --- Rest ------------------------------------------------------------------
CLEARANCE = 0.4  # per side, around the trackpad
FLOOR = 2.0  # pocket floor under the trackpad
FRONT_MARGIN = 14.0  # rest surface in front of the trackpad
TOP_ROUND = 4.0  # radius on the top front and side edges
PLAN_CORNER = 10.0  # front corners seen from above

WIDTH = KB_WIDTH
POCKET_W = TP_WIDTH + 2 * CLEARANCE
POCKET_D = TP_DEPTH + 2 * CLEARANCE
DEPTH = FRONT_MARGIN + POCKET_D  # pocket is open at the back for cable and power switch

# Top surface is one plane matching the trackpad's slope, so it sits flush everywhere.
SLOPE = (TP_H_REAR - TP_H_FRONT) / TP_DEPTH
Z_FRONT = FLOOR + TP_H_FRONT - SLOPE * (FRONT_MARGIN + CLEARANCE)
Z_REAR = Z_FRONT + SLOPE * DEPTH

OVERSHOOT = 5.0  # how far cutting tools reach past the part so cuts are clean

# --- Bumpon recesses (under the side wings) --------------------------------
# Deep enough that common 10 mm x 2.5-3 mm bumpons stick out only ~0.5 mm,
# so the rest stays level with the keyboard.
FOOT_D = 10.5
FOOT_DEPTH = 2.5
FOOT_INSET = 15.0

# --- Split into a centre piece and two wings -------------------------------
# The seams run through the full-height wings, not the 2 mm pocket floor.
SPLIT_X = POCKET_W / 2 + 12.0  # 12 mm of solid wall beside the pocket
DOVETAIL_LEN = 8.0
DOVETAIL_NECK = 7.0
DOVETAIL_HEAD = 11.0
DOVETAIL_FIT = 0.15  # removed from each flank of the male tab
DOVETAIL_YS = (8.0, DEPTH * 0.45, DEPTH - 12.0)
WING_GAP = 10.0  # space between the wings when printed on one plate


def body():
    with BuildPart() as part:
        # Rounded front corners, square back corners. A rounded back corner would carry
        # the top fillet onto the back edge, which must stay square to stay flush.
        with BuildSketch():
            RectangleRounded(WIDTH, DEPTH, PLAN_CORNER, align=(Align.CENTER, Align.MIN))
            with Locations((0, DEPTH / 2)):
                Rectangle(WIDTH, DEPTH / 2, align=(Align.CENTER, Align.MIN))
        extrude(amount=Z_REAR + OVERSHOOT)

        # Sloped top: profile in the YZ plane, extruded across the full width.
        with BuildSketch(Plane.YZ):
            Polygon(
                (-1, Z_FRONT - SLOPE),
                (DEPTH + 1, Z_REAR + SLOPE),
                (DEPTH + 1, Z_REAR + 2 * OVERSHOOT),
                (-1, Z_REAR + 2 * OVERSHOOT),
                align=None,
            )
        extrude(amount=WIDTH, both=True, mode=Mode.SUBTRACT)

        # Round front and sides; the back edge stays square so it is flush up to the keyboard.
        top = part.faces().sort_by(Axis.Z)[-1]
        fillet([e for e in top.outer_wire().edges() if e.center().Y < DEPTH - 1], TOP_ROUND)

        # Trackpad pocket, open at the back.
        with BuildSketch(Plane.XY.offset(FLOOR)):
            with Locations((0, FRONT_MARGIN)):
                RectangleRounded(
                    POCKET_W, POCKET_D + 4 * OVERSHOOT, TP_CORNER_R + CLEARANCE, align=(Align.CENTER, Align.MIN)
                )
        extrude(amount=Z_REAR + OVERSHOOT, mode=Mode.SUBTRACT)

        # Bumpon recesses in the bottom.
        foot_x = WIDTH / 2 - FOOT_INSET
        with Locations(
            (-foot_x, FOOT_INSET), (foot_x, FOOT_INSET), (-foot_x, DEPTH - FOOT_INSET), (foot_x, DEPTH - FOOT_INSET)
        ):
            Cylinder(FOOT_D / 2, FOOT_DEPTH, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    return part.part


def centre_region(fit):
    """Space kept by the centre piece: |x| < SPLIT_X plus dovetail tabs reaching into each wing."""
    tall = Z_REAR + 4 * OVERSHOOT
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


def write_3mf(path, *shapes):
    mesher = Mesher()
    for i, shape in enumerate(shapes):
        mesher.add_shape(shape, part_number=f"{path.stem}_{i}")
    mesher.write(str(path))


def main():
    OUT_DIR.mkdir(exist_ok=True)
    for stale in ("left", "right"):
        for ext in ("stl", "3mf"):
            (OUT_DIR / f"handrest_{stale}.{ext}").unlink(missing_ok=True)

    parts = build_parts()
    export_step(parts["full"], str(OUT_DIR / "handrest_full.step"))
    for name, part in parts.items():
        export_stl(part, str(OUT_DIR / f"handrest_{name}.stl"))
        write_3mf(OUT_DIR / f"handrest_{name}.3mf", part)
    write_3mf(OUT_DIR / "handrest_wings.3mf", *wings_plate(parts))

    bb = parts["full"].bounding_box()
    print(f"size {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm")
    print(f"top surface {Z_FRONT:.2f} mm at front, {Z_REAR:.2f} mm at rear")
    for name, part in parts.items():
        b = part.bounding_box()
        print(f"{name:10} {b.size.X:6.1f} x {b.size.Y:5.1f} mm, valid={part.is_valid}")


if __name__ == "__main__":
    main()
