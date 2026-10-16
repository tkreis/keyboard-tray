"""Checks the built model against the device specs and Bambu Lab beds.

Run after handrest.py:  .venv/bin/python verify.py
Exits non-zero if any check fails.
"""

import sys

from build123d import Edge, import_stl

import handrest as hr

# Bambu Lab build plates (X x Y mm), from bambulab.com tech specs.
BEDS = {"A1 mini": (180, 180), "A1 / P1S / P2S / X1C": (256, 256), "H2D": (325, 320)}
BED_MARGIN = 5.0  # keep this far off the plate edge
MIN_SEAM_HEIGHT = 5.0  # seams must run through solid wing, not the 2 mm pocket floor


def probe(shape, axis, **fixed):
    """Sorted coordinates along `axis` where a line through `fixed` enters and leaves the solid."""
    start = {"x": -400.0, "y": -400.0, "z": -400.0, **fixed}
    end = {**start, axis: 400.0}
    found = shape.intersect(Edge.make_line(tuple(start.values()), tuple(end.values())))
    edges = found if isinstance(found, list) else [found] if found else []
    index = "xyz".index(axis)
    return sorted({round((v.X, v.Y, v.Z)[index], 3) for e in edges for v in e.vertices()})


def main():
    failures = []

    def check(name, got, want, tol=0.05):
        ok = abs(got - want) <= tol
        print(f"{'ok  ' if ok else 'FAIL'} {name}: {got:.2f} (want {want:.2f})")
        if not ok:
            failures.append(name)

    def at_least(name, got, minimum):
        ok = got >= minimum
        print(f"{'ok  ' if ok else 'FAIL'} {name}: {got:.2f} (min {minimum:.2f})")
        if not ok:
            failures.append(name)

    parts = hr.build_parts()
    full = parts["full"]

    print(f"== Pocket vs Magic Trackpad ({hr.TP_WIDTH} x {hr.TP_DEPTH}, {hr.TP_H_FRONT}-{hr.TP_H_REAR} tall) ==")
    y_mid = hr.FRONT_MARGIN + hr.POCKET_D / 2
    xs = probe(full, "x", y=y_mid, z=hr.FLOOR + 1)
    check("pocket width", xs[2] - xs[1], hr.TP_WIDTH + 2 * hr.CLEARANCE)
    ys = probe(full, "y", x=0, z=hr.FLOOR + 1)
    check("pocket starts behind front edge", ys[1], hr.FRONT_MARGIN)
    check("pocket depth (open back)", hr.DEPTH - ys[1], hr.TP_DEPTH + 2 * hr.CLEARANCE)
    check("pocket floor", probe(full, "z", x=0, y=y_mid)[-1], hr.FLOOR)
    # A point on the front-left corner arc, 45 degrees round from its centre.
    r = hr.TP_CORNER_R + hr.CLEARANCE
    arc_y = hr.FRONT_MARGIN + r - r * 0.5**0.5
    arc_x = -hr.POCKET_W / 2 + r - r * 0.5**0.5
    xs = probe(full, "x", y=arc_y, z=hr.FLOOR + 1)
    check("pocket corner radius (point on 45 deg arc)", xs[1], arc_x, tol=0.02)

    print("== Flush top ==")
    x_wing = hr.TP_WIDTH / 2 + 30
    y_tp_front = hr.FRONT_MARGIN + hr.CLEARANCE
    for label, y, tp_h in (("front", y_tp_front, hr.TP_H_FRONT), ("rear", y_tp_front + hr.TP_DEPTH, hr.TP_H_REAR)):
        top = probe(full, "z", x=x_wing, y=y)[-1]
        check(f"rest top at trackpad {label} edge = floor + trackpad", top, hr.FLOOR + tp_h, tol=0.01)

    print(f"== Overall vs NuPhy Air75 V2 ({hr.KB_WIDTH} x {hr.KB_DEPTH} x {hr.KB_HEIGHT}) ==")
    bb = full.bounding_box()
    check("width", bb.size.X, hr.KB_WIDTH)
    check("depth", bb.size.Y, hr.DEPTH)
    at_least("keyboard is taller than the rest's back edge", hr.KB_HEIGHT - hr.Z_REAR, 0.0)

    print("== Split ==")
    pieces = {k: v for k, v in parts.items() if k != "full"}
    names = list(pieces)
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            overlap = pieces[a] & pieces[b]
            check(f"{a} and {b} do not overlap (cm3)", overlap.volume / 1000 if overlap else 0.0, 0.0)
    for name, p in pieces.items():
        ok = p.is_valid and len(p.solids()) == 1
        print(f"{'ok  ' if ok else 'FAIL'} {name} is one valid solid")
        if not ok:
            failures.append(f"{name} solid")
    for side in (-1, 1):
        for y in hr.DOVETAIL_YS:
            height = probe(full, "z", x=side * hr.SPLIT_X, y=y)[-1]
            at_least(f"seam height at x={side * hr.SPLIT_X:.1f}, y={y:.1f}", height, MIN_SEAM_HEIGHT)
    print(f"info dovetail glue gap volume: {(full.volume - sum(p.volume for p in pieces.values())) / 1000:.2f} cm3")

    print("== Exported files match model ==")
    for name, p in parts.items():
        mesh = import_stl(str(hr.OUT_DIR / f"handrest_{name}.stl")).bounding_box()
        check(f"{name}.stl width", mesh.size.X, p.bounding_box().size.X, tol=0.01)
        check(f"{name}.stl depth", mesh.size.Y, p.bounding_box().size.Y, tol=0.01)

    print("== Bambu Lab plate fit ==")
    left, right = hr.wings_plate(parts)
    plates = {**pieces, "wings (one plate)": left.fuse(right)}
    for bed, (bx, by) in BEDS.items():
        for name, p in plates.items():
            s = p.bounding_box().size
            fits = s.X + 2 * BED_MARGIN <= bx and s.Y + 2 * BED_MARGIN <= by
            print(f"{'fits' if fits else '  - '} {bed:22} {name:18} {s.X:6.1f} x {s.Y:5.1f}")
            if bed.startswith("A1 /") and not fits:
                failures.append(f"{name} on 256 mm plate")

    print("\nALL CHECKS PASSED" if not failures else f"\nFAILED: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
