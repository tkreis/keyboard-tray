"""Renders previews into renders/. Run after handrest.py:  .venv/bin/python render.py

The trackpad and keyboard are simple stand-ins built from their published dimensions.
"""

from pathlib import Path

import pyvista as pv
from build123d import Align, BuildPart, BuildSketch, Locations, Mode, Plane, Polygon, RectangleRounded, extrude, export_stl

import handrest as h

STL = h.OUT_DIR

OUT = Path(__file__).parent / "renders"
TMP = OUT / "_trackpad.stl"

KB_GAP = 3.0  # keyboard sits just behind the rest

REST = "#d9d6cf"
TRACKPAD = "#f4f4f2"
KEYBOARD = "#4a4d52"
KEYCAP = "#6b6f75"


def trackpad_mesh():
    y0 = h.FRONT_MARGIN + h.CLEARANCE
    with BuildPart() as tp:
        with BuildSketch(Plane.XY.offset(h.FLOOR)):
            with Locations((0, y0)):
                RectangleRounded(h.TP_WIDTH, h.TP_DEPTH, h.TP_CORNER_R, align=(Align.CENTER, Align.MIN))
        extrude(amount=h.TP_H_REAR)
        with BuildSketch(Plane.YZ):
            Polygon(
                (y0 - 1, h.FLOOR + h.TP_H_FRONT - h.SLOPE),
                (y0 + h.TP_DEPTH + 1, h.FLOOR + h.TP_H_REAR + h.SLOPE),
                (y0 + h.TP_DEPTH + 1, 40),
                (y0 - 1, 40),
                align=None,
            )
        extrude(amount=h.TP_WIDTH, both=True, mode=Mode.SUBTRACT)
    export_stl(tp.part, str(TMP))
    mesh = pv.read(str(TMP))
    TMP.unlink()
    return mesh


def keyboard_meshes():
    y0 = h.DEPTH + KB_GAP
    base = pv.Box((-h.KB_WIDTH / 2, h.KB_WIDTH / 2, y0, y0 + h.KB_DEPTH, 0, h.KB_HEIGHT - 4))
    caps = []
    pitch = 19.05
    cols, rows = 16, 6
    x_start = -h.KB_WIDTH / 2 + 6
    for r in range(rows):
        y = y0 + 6 + r * (h.KB_DEPTH - 12) / rows
        for c in range(cols):
            x = x_start + c * pitch
            if x + pitch - 2 > h.KB_WIDTH / 2 - 4:
                break
            caps.append(pv.Box((x + 1, x + pitch - 1, y + 1, y + (h.KB_DEPTH - 12) / rows - 1, h.KB_HEIGHT - 4, h.KB_HEIGHT)))
    return base, pv.merge(caps)


def shot(meshes, path, camera, size=(1600, 1000), parallel=False):
    p = pv.Plotter(off_screen=True, window_size=size)
    if parallel:
        p.enable_parallel_projection()
    p.set_background("#f7f7f8", top="#e3e6ea")
    for mesh, color in meshes:
        p.add_mesh(mesh, color=color, smooth_shading=False, specular=0.25, specular_power=20)
    p.camera_position = camera
    if parallel:
        p.camera.parallel_scale = 40
    p.enable_anti_aliasing("ssaa")
    p.screenshot(str(path))
    p.close()


def main():
    OUT.mkdir(exist_ok=True)
    rest = pv.read(str(STL / "handrest_full.stl"))
    centre = pv.read(str(STL / "handrest_centre.stl"))
    wing_left = pv.read(str(STL / "handrest_wing_left.stl")).translate((-20, 0, 0))
    wing_right = pv.read(str(STL / "handrest_wing_right.stl")).translate((20, 0, 0))
    pad = trackpad_mesh()
    kb, caps = keyboard_meshes()
    desk = pv.Plane(center=(0, 100, -0.2), i_size=3000, j_size=3000)

    setup = [(desk, "#ffffff"), (rest, REST), (pad, TRACKPAD), (kb, KEYBOARD), (caps, KEYCAP)]
    shot(setup, OUT / "setup.png", [(-230, -330, 260), (0, 90, 0), (0, 0, 1)])
    shot([(desk, "#ffffff"), (rest, REST)], OUT / "rest.png", [(-200, -300, 240), (0, 65, 0), (0, 0, 1)])
    shot(
        [(desk, "#ffffff"), (rest, REST), (pad, TRACKPAD)],
        OUT / "flush_closeup.png",
        [(-150, -70, 45), (-85, 25, 6), (0, 0, 1)],
    )
    shot([(rest, REST), (pad, TRACKPAD), (kb, KEYBOARD), (caps, KEYCAP)], OUT / "side.png", [(-600, 130, 10), (0, 130, 10), (0, 0, 1)], size=(1600, 400), parallel=True)
    shot(
        [(desk, "#ffffff"), (centre, REST), (wing_left, "#c9c5bc"), (wing_right, "#c9c5bc")],
        OUT / "pieces.png",
        [(-120, -300, 300), (0, 65, 0), (0, 0, 1)],
    )
    print("\n".join(str(p) for p in sorted(OUT.glob("*.png"))))


if __name__ == "__main__":
    main()
