<img src="assets/icon.svg" width="64" height="64" alt="">

# Handrest

3D-printable palm rest that sits centred in front of a NuPhy Air75 V2 and holds an
Apple Magic Trackpad flush with its surface, like the lower half of a MacBook.

- Same width as the keyboard: 316.4 x 133.8 mm, with a flat top 13 mm high.
- The trackpad sits in a cage copied from a fit-tested community tray. Its pocket is 160.25 x 114.56 mm
  with 2.575 mm corners for the pre-2021 trackpad, and 0.125 mm side clearance. Apple lists the trackpad as 114.9 mm deep, so the
  pocket is 0.34 mm shorter than that figure; this matches the reference tray, which fits.
- The pocket floor slopes with the trackpad's wedge shape, so the trackpad's surface is level and flush with the top.
- A 5.24 mm wall closes the back of the pocket. A 16 mm slot in it leaves room for the Lightning plug, and a
  2.5 mm half-round notch near the back right corner clears the power switch, as in the reference.
- A 130 x 90 mm hole in the pocket floor saves plastic and lets you push the trackpad out from below.
- The 14 mm strip in front of the trackpad is the palm rest. Its top front and side edges are rounded with a 4 mm radius;
  seen from above, the front corners have a 10 mm radius.
- The back edge is square, so the rest stays flush right up to the keyboard.
- Four 10.5 x 2 mm recesses underneath take 10 mm rubber bumpons (2.5-3 mm tall). They stick out 0.5-1 mm,
  which puts the top at 13.5-14 mm, level with the 13.5 mm keyboard.

![Setup](renders/setup.png)
![Side](renders/side.png)

## Print on a Bambu Lab printer

The rest prints as three pieces: a centre piece that holds the trackpad, and two side wings.
The seams run through the solid 13 mm wings, outside the trackpad cage.
You need a 256 mm plate (A1, P1S, P2S, X1C, H2D). The centre piece is too wide for the A1 mini.

| Plate | File | Size (mm) |
|---|---|---|
| 1 | `out/handrest_centre.3mf` | 199.9 x 133.8 x 13.0 |
| 2 | `out/handrest_wings.3mf` (both wings) | 142.2 x 133.8 x 13.0 |

1. In Bambu Studio, open `handrest_centre.3mf`. Leave it flat side down, as it loads.
2. Slice with 0.20 mm layers, 3 walls and 15 % infill, with no supports. Use PLA or PETG.
3. Print it, then do the same with `handrest_wings.3mf`.
4. Slide each wing onto the centre piece from above. Glue the dovetails with CA or PLA glue.
5. Press four 10 mm bumpons into the recesses underneath.
6. Press the trackpad straight down into the pocket.

`handrest_wing_left.3mf` and `handrest_wing_right.3mf` hold one wing each, if you want to print them separately.
STL versions of every part are also in `out/`.

![Pieces](renders/pieces.png)

## Change dimensions

Edit the constants at the top of `handrest.py`, then rebuild, verify and render:

```sh
uv venv -p 3.11 .venv && uv pip install -p .venv build123d pyvista
.venv/bin/python handrest.py   # writes out/
.venv/bin/python verify.py     # checks pocket, flush top, seams, plate fit
.venv/bin/python render.py     # writes renders/
```

The pocket fit is copied from a fit-tested community tray: 160.25 mm wide
(`CLEARANCE = 0.125`, `POCKET_D = 114.56`). If the trackpad is too long for the pocket, raise `POCKET_D`.
The corners are set for the 2015 (pre-2021) trackpad, which has sharp corners. They come from a second tray:
the 2.575 mm pocket corner radius (`TP_CORNER_R = 2.45` plus `CLEARANCE`) is measured from the
"< 2020, Small corner radii" profile of Jerrod H's "Magic Tray" on MakerWorld (model 1060135), whose pocket
is 160.8 x 115.7 mm. The corners are not fit-tested in this pocket. For trackpads from 2021 onwards (Lightning and USB-C),
set `TP_CORNER_R = 8.625` to get the reference tray's 8.75 mm corners. 0.125 mm is tight for FDM; if your printer runs wide and the trackpad will not drop in, raise `CLEARANCE`.
