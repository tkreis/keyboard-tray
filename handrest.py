"""Hand rest that holds an Apple Magic Trackpad flush, centred in front of a NuPhy Air75 V2.

Run:  .venv/bin/python handrest.py
Out:  out/handrest_{full,left,right}.{stl,3mf}, out/handrest_full.step

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

# --- Devices ---------------------------------------------------------------
KB_WIDTH = 316.4  # NuPhy Air75 V2: 316.4 x 132.5 x 13.5

TP_WIDTH = 160.0  # Magic Trackpad: 160.0 x 114.9, 4.9 (front) to 10.9 (rear) tall
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

# --- Bumpon recesses (under the side wings only) ---------------------------
FOOT_D = 10.5
FOOT_DEPTH = 1.0
FOOT_INSET = 15.0

# --- Split for beds narrower than ~320 mm ----------------------------------
DOVETAIL_LEN = 8.0
DOVETAIL_NECK = 7.0
DOVETAIL_HEAD = 11.0
DOVETAIL_FIT = 0.15  # removed from each flank of the male tab
DOVETAIL_YS = (FRONT_MARGIN / 2, FRONT_MARGIN + POCKET_D * 0.3, FRONT_MARGIN + POCKET_D * 0.75)


def body():
    with BuildPart() as part:
        # Rounded front corners, square back corners. A rounded back corner would carry
        # the top fillet onto the back edge, which must stay square to stay flush.
        with BuildSketch():
            RectangleRounded(WIDTH, DEPTH, PLAN_CORNER, align=(Align.CENTER, Align.MIN))
            with Locations((0, DEPTH / 2)):
                Rectangle(WIDTH, DEPTH / 2, align=(Align.CENTER, Align.MIN))
        extrude(amount=Z_REAR + 5)

        # Sloped top: profile in the YZ plane, extruded across the full width.
        with BuildSketch(Plane.YZ):
            Polygon(
                (-1, Z_FRONT - SLOPE),
                (DEPTH + 1, Z_REAR + SLOPE),
                (DEPTH + 1, Z_REAR + 10),
                (-1, Z_REAR + 10),
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
                    POCKET_W, POCKET_D + 20, TP_CORNER_R + CLEARANCE, align=(Align.CENTER, Align.MIN)
                )
        extrude(amount=Z_REAR + 5, mode=Mode.SUBTRACT)

        # Bumpon recesses in the bottom.
        fx = WIDTH / 2 - FOOT_INSET
        with Locations(
            (-fx, FOOT_INSET), (fx, FOOT_INSET), (-fx, DEPTH - FOOT_INSET), (fx, DEPTH - FOOT_INSET)
        ):
            Cylinder(FOOT_D / 2, FOOT_DEPTH, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    return part.part


def dovetail_keep(fit):
    """Region kept by the left half: x < 0 plus dovetail tabs reaching into x > 0."""
    tall = Z_REAR + 20
    with BuildPart() as keep:
        with Locations((-WIDTH / 2 - 5, -5, -5)):
            Box(WIDTH / 2 + 5, DEPTH + 10, tall, align=(Align.MIN, Align.MIN, Align.MIN))
        n, h, L = DOVETAIL_NECK / 2 - fit, DOVETAIL_HEAD / 2 - fit, DOVETAIL_LEN - fit
        for y in DOVETAIL_YS:
            with BuildSketch(Plane.XY.offset(-5)):
                Polygon((-0.5, y - n), (L, y - h), (L, y + h), (-0.5, y + n), align=None)
            extrude(amount=tall)
    return keep.part


def main():
    out = Path(__file__).parent / "out"
    out.mkdir(exist_ok=True)

    full = body()
    left = full & dovetail_keep(DOVETAIL_FIT)
    right = full - dovetail_keep(0)

    export_step(full, str(out / "handrest_full.step"))
    for name, part in (("full", full), ("left", left), ("right", right)):
        export_stl(part, str(out / f"handrest_{name}.stl"))
        mesher = Mesher()
        mesher.add_shape(part, part_number=f"handrest_{name}")
        mesher.write(str(out / f"handrest_{name}.3mf"))

    bb = full.bounding_box()
    print(f"size {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm")
    print(f"top surface {Z_FRONT:.2f} mm at front, {Z_REAR:.2f} mm at rear")
    print(f"volume {full.volume / 1000:.0f} cm3")
    for name, p in (("left", left), ("right", right)):
        b = p.bounding_box()
        print(f"{name} half {b.size.X:.1f} x {b.size.Y:.1f} mm, valid={p.is_valid}")


if __name__ == "__main__":
    main()
