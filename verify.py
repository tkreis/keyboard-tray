"""Checks the built model against the device specs and Bambu Lab beds.

Run after handrest.py:  .venv/bin/python verify.py
Exits non-zero if any check fails.
"""

import sys

from build123d import Edge, import_stl

import handrest as h

# Bambu Lab build plates (X x Y mm), from bambulab.com tech specs.
BEDS = {"A1 mini": (180, 180), "A1 / P1S / P2S / X1C": (256, 256), "H2D": (325, 320)}
BED_MARGIN = 5.0  # keep this far off the plate edge

failures = []


def check(name, got, want, tol=0.05):
    ok = abs(got - want) <= tol
    print(f"{'ok  ' if ok else 'FAIL'} {name}: {got:.2f} (want {want:.2f})")
    if not ok:
        failures.append(name)


def hits_along(shape, start, end):
    """Sorted coordinates where a straight line enters and leaves the solid."""
    segments = shape.intersect(Edge.make_line(start, end))
    segments = segments if isinstance(segments, list) else [segments]
    axis = [i for i in range(3) if start[i] != end[i]][0]
    pts = []
    for e in segments or []:
        for v in e.vertices():
            pts.append(round((v.X, v.Y, v.Z)[axis], 3))
    return sorted(set(pts))


full = h.body()
left = full & h.dovetail_keep(h.DOVETAIL_FIT)
right = full - h.dovetail_keep(0)

print("== Pocket vs Magic Trackpad (160.0 x 114.9, 4.9-10.9 tall) ==")
y_mid = h.FRONT_MARGIN + h.POCKET_D / 2
xs = hits_along(full, (-200, y_mid, h.FLOOR + 1), (200, y_mid, h.FLOOR + 1))
check("pocket width", xs[2] - xs[1], h.TP_WIDTH + 2 * h.CLEARANCE)
ys = hits_along(full, (0, -10, h.FLOOR + 1), (0, 200, h.FLOOR + 1))
check("pocket starts behind front edge", ys[1], h.FRONT_MARGIN)
check("pocket depth (open back, trackpad depth + front clearance)", h.DEPTH - ys[1], h.TP_DEPTH + 2 * h.CLEARANCE)
zs = hits_along(full, (0, y_mid, -5), (0, y_mid, 50))
check("pocket floor", zs[-1], h.FLOOR)

print("== Flush top ==")
x_wing = h.TP_WIDTH / 2 + 30
y_tp_front = h.FRONT_MARGIN + h.CLEARANCE
y_tp_rear = y_tp_front + h.TP_DEPTH
for label, y, tp_h in (("front", y_tp_front, h.TP_H_FRONT), ("rear", y_tp_rear, h.TP_H_REAR)):
    zs = hits_along(full, (x_wing, y, -5), (x_wing, y, 50))
    check(f"rest top at trackpad {label} edge = floor + trackpad", zs[-1], h.FLOOR + tp_h, tol=0.01)

print("== Overall vs NuPhy Air75 V2 (316.4 wide) ==")
bb = full.bounding_box()
check("width", bb.size.X, h.KB_WIDTH)
check("depth", bb.size.Y, h.DEPTH)

print("== Split ==")
check("halves do not overlap (cm3)", (left & right).volume / 1000 if (left & right) else 0.0, 0.0)
gap = (full.volume - left.volume - right.volume) / 1000
print(f"info dovetail glue gap volume: {gap:.2f} cm3")
for name, p in (("left", left), ("right", right)):
    print(f"info {name} half valid={p.is_valid}, solids={len(p.solids())}")
    if not p.is_valid or len(p.solids()) != 1:
        failures.append(f"{name} solid")

print("== Exported files match model ==")
for name, p in (("full", full), ("left", left), ("right", right)):
    m = import_stl(f"out/handrest_{name}.stl").bounding_box()
    check(f"{name}.stl width", m.size.X, p.bounding_box().size.X, tol=0.01)
    check(f"{name}.stl depth", m.size.Y, p.bounding_box().size.Y, tol=0.01)

print("== Bambu Lab plate fit ==")
for bed, (bx, by) in BEDS.items():
    for name, p in (("full", full), ("left", left), ("right", right)):
        s = p.bounding_box().size
        fits = s.X + 2 * BED_MARGIN <= bx and s.Y + 2 * BED_MARGIN <= by
        print(f"{'fits' if fits else '  - '} {bed:22} {name:5} {s.X:6.1f} x {s.Y:5.1f}")

print("\nALL CHECKS PASSED" if not failures else f"\nFAILED: {failures}")
sys.exit(1 if failures else 0)
