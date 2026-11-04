"""
Polygon tool used to label the training tiles.
Run it with `python mask_tool.py` after setting IMAGE_PATH.

Left click: vertex | Right click: close and fill polygon
v: vegetation (1) | n: no vegetation (0) | r: reset | s: save and quit | q: quit without saving
Saves mask_<quad>_Rxx_Cxx.tif (int8): 1 = vegetation, 0 = no vegetation, -1 = unlabeled
"""
import os
import re
import numpy as np
import rasterio
import cv2
import tkinter as tk

from config import trainImagesFolder, trainMasksFolder

# Tile to label (change only this line)
IMAGE_PATH = str(trainImagesFolder / 'C3' / 'Sentinel_Monterrey_15x15_R05_C05.tif')
OUTPUT_DIR = str(trainMasksFolder)
os.makedirs(OUTPUT_DIR, exist_ok=True)

root = tk.Tk()
screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()
root.destroy()

with rasterio.open(IMAGE_PATH) as src:
    bands_data = src.read()      # (bands, H, W)
    profile = src.profile

# Band order: B2, B3, B4, B8, B8A, B11, B12
B2, B3, B4, B8, B8A, B11, B12 = bands_data.astype(np.float32)

scale = 10000.0
B2 /= scale
B3 /= scale
B4 /= scale

rgb_raw = np.dstack([B4, B3, B2])   # (H, W, 3)
p99 = np.percentile(rgb_raw, 99)
rgb_raw = np.clip(rgb_raw / (p99 + 1e-6), 0, 1)
rgb_raw_255 = (rgb_raw * 255).astype(np.uint8)

H, W = rgb_raw_255.shape[:2]

CANVAS_W = screen_w
CANVAS_H = screen_h

LEFT_MARGIN   = 180
RIGHT_MARGIN  = 180
TOP_MARGIN    = 150
BOTTOM_MARGIN = 150

inner_w = CANVAS_W - LEFT_MARGIN - RIGHT_MARGIN
inner_h = CANVAS_H - TOP_MARGIN - BOTTOM_MARGIN

scale_w = inner_w / W
scale_h = inner_h / H
scale_img = min(scale_w, scale_h)

disp_w = int(W * scale_img)
disp_h = int(H * scale_img)

sx = W / disp_w
sy = H / disp_h

x0 = LEFT_MARGIN + (inner_w - disp_w) // 2
y0 = TOP_MARGIN + (inner_h - disp_h) // 2
x1 = x0 + disp_w
y1 = y0 + disp_h

yMask = np.full((H, W), -1, dtype=np.int8)   # -1 = unlabeled, 1 = veg, 0 = no veg
current_class = 1 
current_poly_orig = []  

view_canvas = None 

def build_display_canvas():
    """
    Screen-size canvas with:
    - centered image
    - painted mask
    - title, instructions, axes and ticks
    """

    vis_raw = rgb_raw_255.copy()
    green = np.array([0, 255, 0], np.uint8)
    red   = np.array([0, 0, 255], np.uint8)
    vis_raw[yMask == 1] = 0.5 * vis_raw[yMask == 1] + 0.5 * green
    vis_raw[yMask == 0] = 0.5 * vis_raw[yMask == 0] + 0.5 * red

    for i in range(len(current_poly_orig) - 1):
        cv2.line(
            vis_raw,
            current_poly_orig[i],
            current_poly_orig[i + 1],
            (0, 255, 0) if current_class == 1 else (0, 0, 255),
            1
        )

    vis_img = cv2.resize(vis_raw, (disp_w, disp_h), interpolation=cv2.INTER_AREA)

    canvas = np.zeros((CANVAS_H, CANVAS_W, 3), dtype=np.uint8)

    canvas[y0:y1, x0:x1] = vis_img

    overlay = canvas.copy()
    cv2.rectangle(overlay, (0, 0), (CANVAS_W, TOP_MARGIN), (0, 0, 0), -1)
    canvas = cv2.addWeighted(overlay, 0.4, canvas, 0.6, 0)

    title = os.path.basename(IMAGE_PATH)
    mode_text = f"Mode: {'VEGETATION (1)' if current_class == 1 else 'NO VEGETATION (0)'}"
    inst1 = "Left click: vertex | Right click: close polygon"
    inst2 = "Keys: v=veg, n=no-veg, r=reset, s=save, q=quit"

    cv2.putText(canvas, title, (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(canvas, mode_text, (20, 65),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(canvas, inst1, (20, 95),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (220, 220, 220), 1, cv2.LINE_AA)
    cv2.putText(canvas, inst2, (20, 120),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (220, 220, 220), 1, cv2.LINE_AA)

    num_ticks = 6

    y_axis_line = y1 + 30
    cv2.line(canvas, (x0, y_axis_line), (x1, y_axis_line), (200, 200, 200), 1)
    for i in range(num_ticks + 1):
        t = i / num_ticks
        col_orig = int(t * (W - 1))
        x_tick = x0 + int(t * disp_w)
        cv2.line(canvas, (x_tick, y_axis_line - 6), (x_tick, y_axis_line + 6), (200, 200, 200), 1)
        cv2.putText(canvas, str(col_orig), (x_tick - 25, y_axis_line + 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1, cv2.LINE_AA)
    cv2.putText(canvas, "columns (x)", (x0 + disp_w//2 - 80, y_axis_line + 45),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1, cv2.LINE_AA)

    x_axis_line = x0 - 30
    cv2.line(canvas, (x_axis_line, y0), (x_axis_line, y1), (200, 200, 200), 1)
    for i in range(num_ticks + 1):
        t = i / num_ticks
        row_orig = int(t * (H - 1))
        y_tick = y0 + int(t * disp_h)
        cv2.line(canvas, (x_axis_line - 6, y_tick), (x_axis_line + 6, y_tick), (200, 200, 200), 1)
        cv2.putText(canvas, str(row_orig), (x_axis_line - 75, y_tick + 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1, cv2.LINE_AA)
    cv2.putText(canvas, "rows (y)", (x_axis_line - 80, y0 + disp_h//2),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1, cv2.LINE_AA)

    return canvas

def on_mouse(event, x_disp, y_disp, flags, param):
    """
    Mouse callback: receives coordinates on the full canvas and converts them
    to coordinates of the original image when they are inside it.
    """
    global current_poly_orig, yMask, current_class, view_canvas

    if not (x0 <= x_disp < x1 and y0 <= y_disp < y1):
        return

    x_in = x_disp - x0
    y_in = y_disp - y0

    x = int(x_in * sx)
    y = int(y_in * sy)
    x = max(0, min(W - 1, x))
    y = max(0, min(H - 1, y))

    if event == cv2.EVENT_LBUTTONDOWN:
        current_poly_orig.append((x, y))
        view_canvas = build_display_canvas()

    elif event == cv2.EVENT_RBUTTONDOWN:
        if len(current_poly_orig) >= 3:
            pts = np.array(current_poly_orig, np.int32).reshape((-1, 1, 2))
            if current_class == 1:
                cv2.fillPoly(yMask, [pts], 1)
            else:
                cv2.fillPoly(yMask, [pts], 0)
        current_poly_orig = []
        view_canvas = build_display_canvas()

view_canvas = build_display_canvas()
cv2.namedWindow('annot', cv2.WINDOW_NORMAL)
cv2.setWindowProperty('annot', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cv2.setMouseCallback('annot', on_mouse)

print("\n===== LABELING TOOL =====")
print(" - LEFT click: add a vertex to the current polygon")
print(" - RIGHT click: close and fill the polygon")
print(" - Key 'v': VEGETATION mode (1)")
print(" - Key 'n': NO VEGETATION mode (0)")
print(" - Key 'r': reset the whole mask")
print(" - Key 's': SAVE and quit")
print(" - Key 'q': quit WITHOUT saving (yMask all -1)")
print("===================================\n")

running = True
while running:
    cv2.imshow('annot', view_canvas)
    k = cv2.waitKey(20) & 0xFF

    if cv2.getWindowProperty('annot', cv2.WND_PROP_VISIBLE) < 1:
        print("Window closed with the X, quitting without saving.")
        yMask[:] = -1
        running = False
        break

    if k in (ord('v'), ord('V')):
        current_class = 1
        view_canvas = build_display_canvas()
        print("Mode: vegetation (1)")
    elif k in (ord('n'), ord('N')):
        current_class = 0
        view_canvas = build_display_canvas()
        print("Mode: no vegetation (0)")
    elif k in (ord('r'), ord('R')):
        print("Resetting mask...")
        yMask[:] = -1
        current_poly_orig = []
        view_canvas = build_display_canvas()
    elif k in (ord('s'), ord('S')):
        print("Key 's': saving and closing the tool...")
        running = False
        break
    elif k in (ord('q'), ord('Q')):
        print("Key 'q': quitting WITHOUT saving (yMask all -1).")
        yMask[:] = -1
        running = False
        break

print("Closing OpenCV window...")
cv2.destroyWindow('annot')
cv2.waitKey(1)
print("Window closed.")

fname = os.path.basename(IMAGE_PATH)
parent_dir = os.path.basename(os.path.dirname(IMAGE_PATH))

quad = parent_dir.upper() if parent_dir.upper().startswith('C') else ""

row_norm = ""
col_norm = ""

m = re.search(r'_(R\d+)_(C\d+)\.tif$', fname, re.IGNORECASE)
if m:
    row_norm = m.group(1).upper()  # e.g. R01
    col_norm = m.group(2).upper()  # e.g. C09
else:
    print("Could not read R/C from the file name, using a generic name.")

parts = ["mask"]
if quad:
    parts.append(quad)
if row_norm:
    parts.append(row_norm)
if col_norm:
    parts.append(col_norm)

filename = "_".join(parts) + ".tif"
OUTPUT_MASK_PATH = os.path.join(OUTPUT_DIR, filename)

mask_profile = profile.copy()
mask_profile.update(count=1, dtype='int8', nodata=-1)

with rasterio.open(OUTPUT_MASK_PATH, 'w', **mask_profile) as dst:
    dst.write(yMask, 1)

print("\nMask saved in:")
print(OUTPUT_MASK_PATH)
print("Values: 1 = vegetation, 0 = no vegetation, -1 = unlabeled")

import numpy as np
import rasterio
import matplotlib.pyplot as plt

MASK_PATH  = OUTPUT_MASK_PATH

with rasterio.open(IMAGE_PATH) as src:
    bands = src.read().astype(np.float32)  # (bands, H, W)

B2, B3, B4, B8, B8A, B11, B12 = bands

scale = 10000.0
B2 /= scale; B3 /= scale; B4 /= scale

rgb = np.dstack([B4, B3, B2])
p99 = np.percentile(rgb, 99)
rgb = np.clip(rgb / (p99 + 1e-6), 0, 1)

with rasterio.open(MASK_PATH) as m:
    yMask = m.read(1)  # 1=veg, 0=no veg, -1=unlabeled

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

axes[0].imshow(rgb)
axes[0].set_title("RGB")
axes[0].axis('off')

# Mask only
# -1 = gray, 0 = black, 1 = green
mask_vis = np.zeros((*yMask.shape, 3), dtype=float)
mask_vis[yMask == -1] = [0.5, 0.5, 0.5]  # gray
mask_vis[yMask == 0]  = [0, 0, 0]        # black
mask_vis[yMask == 1]  = [0, 1, 0]        # green

axes[1].imshow(mask_vis)
axes[1].set_title("Mask (1=green, 0=black, -1=gray)")
axes[1].axis('off')

axes[2].imshow(rgb)
axes[2].imshow(mask_vis, alpha=0.4)
axes[2].set_title("RGB + mask")
axes[2].axis('off')

plt.tight_layout()
plt.show()