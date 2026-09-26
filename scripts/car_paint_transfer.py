"""Pin car paint colour to Unreal so every camera agrees (cross-camera matching, 2026-09-26).
Car mask = pixels where the with-cars depth is nearer than the same world rendered with traffic hidden. Inside the
mask, keep the Wan frame's lightness (dusk light, reflections, headlights) and take the chroma (a*, b* in Lab) from
Unreal's beauty render of the Dekogon car's actual paint. Very bright pixels (headlights) keep Wan's own colour.
usage: python car_paint_transfer.py <wan.mp4> <cam> <geo_cars> <geo_nocars> <out.mp4> [--frames N] [--chroma 0.9]"""
import argparse, glob, os
import numpy as np, cv2

ap = argparse.ArgumentParser()
ap.add_argument("wan"); ap.add_argument("cam"); ap.add_argument("geo"); ap.add_argument("geo_nc"); ap.add_argument("out")
ap.add_argument("--frames", type=int, default=0); ap.add_argument("--chroma", type=float, default=0.9)
ap.add_argument("--thr", type=float, default=3.0, help="depth PNG levels a car must be nearer by")
ap.add_argument("--preview", default="")
a = ap.parse_args()
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
dA = sorted(glob.glob(os.path.join(ROOT, "renders", f"Cesium_{a.cam}_{a.geo}_png", "depth_*.png")))
dB = sorted(glob.glob(os.path.join(ROOT, "renders", f"Cesium_{a.cam}_{a.geo_nc}_png", "depth_*.png")))
bt = sorted(glob.glob(os.path.join(ROOT, "renders", f"Beauty_{a.cam}_{a.geo}_png", "beauty_*.png")))
cap = cv2.VideoCapture(a.wan)
n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); n = min(n, a.frames) if a.frames else n
n = min(n, len(dA), len(dB), len(bt))
W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
vw = cv2.VideoWriter(a.out, cv2.VideoWriter_fourcc(*"mp4v"), 24000 / 1001, (W, H))
k3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
cover = []
for i in range(n):
    ok, w = cap.read()
    if not ok:
        break
    A = cv2.resize(cv2.imread(dA[i], cv2.IMREAD_GRAYSCALE), (W, H)).astype(np.float32)   # white = near
    B = cv2.resize(cv2.imread(dB[i], cv2.IMREAD_GRAYSCALE), (W, H)).astype(np.float32)
    m = ((A - B) > a.thr).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k3); m = cv2.dilate(m, k3, iterations=1)
    mf = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.5)
    cover.append(float(m.mean()))
    beauty = cv2.resize(cv2.imread(bt[i]), (W, H))
    wl = cv2.cvtColor(w, cv2.COLOR_BGR2LAB).astype(np.float32)
    bl = cv2.cvtColor(beauty, cv2.COLOR_BGR2LAB).astype(np.float32)
    head = np.clip((wl[..., 0] - 200.0) / 40.0, 0, 1)            # keep headlight / highlight colour from Wan
    wgt = (mf * (1 - head) * a.chroma)[..., None]
    out = wl.copy()
    out[..., 1:] = wl[..., 1:] * (1 - wgt) + bl[..., 1:] * wgt
    res = cv2.cvtColor(np.clip(out, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)
    vw.write(res)
    if a.preview and i in (24, n // 2):
        cv2.imwrite(a.preview.replace(".png", f"_{i}.png"), np.concatenate([w, beauty, cv2.cvtColor(m * 255, cv2.COLOR_GRAY2BGR), res], 1))
vw.release()
print(f"wrote {a.out}: {n} frames, car mask covers {100 * np.mean(cover):.1f}% of the frame on average")
