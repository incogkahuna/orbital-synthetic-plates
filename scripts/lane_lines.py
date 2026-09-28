"""Paint Sunset Blvd lane markings into each camera's view from the rig geometry (Unreal's road has none, so the AI
guessed and put the double yellow a lane off). Flat-road ray cast from the camera ring; cars (depth with traffic nearer
than the traffic-hidden depth) occlude the paint.
Cross-section, cm lateral from OUR lane centre (+ = right/kerb), matching cesium_c1_run / orbital_plates_rig:
  our lane 0, EB lane to our left -330, oncoming lanes -1000 / -1350, kerb +410.
usage: python lane_lines.py <cam> <geo> <geo_nc> <out_prefix> [--frames N]
writes <out_prefix>_lines.mp4 (lines on black, true colours) and <out_prefix>_depthlines.mp4 (depth with lines drawn)"""
import argparse, glob, math, os, subprocess
import numpy as np, cv2, imageio_ffmpeg

ap = argparse.ArgumentParser()
ap.add_argument("cam"); ap.add_argument("geo"); ap.add_argument("geo_nc"); ap.add_argument("out")
ap.add_argument("--frames", type=int, default=0); ap.add_argument("--check", type=int, default=-1)
ap.add_argument("--car_edges", type=float, default=0.0,
                help=">0: draw the Unreal beauty's edges inside each car (grille/lights vs trunk) at this brightness 0-1, "
                     "so the AI can tell which way a car faces (depth alone is front/back symmetric)")
a = ap.parse_args()
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

YAW = {f"C{i+1}": i * 45.0 for i in range(8)}[a.cam]          # UE yaw: 90 = right, 270 = left
H_CAM, OFF, HFOV, SW, SH = 165.0, 22.0, 65.0, 23.76, 13.365      # 15 cm spline lift + 150 cm eye height
SPEED, START, FPS = 1340.0, 20000.0, 24.0                        # cm/s, cm, frames/s
WHITE, YELLOW = (235, 235, 235), (40, 190, 235)                  # BGR
# (lateral cm, width cm, colour, dashed)
LINES = [(-165, 12, WHITE, True),                                # our lane | EB lane to our left
         (-660 - 12, 11, YELLOW, False), (-660 + 12, 11, YELLOW, False),   # double yellow centre line
         (-1175, 12, WHITE, True),                               # between the two oncoming lanes
         (165, 12, WHITE, False)]                                # parking-lane edge line
DASH, GAP = 300.0, 900.0                                         # 10 ft dash, 30 ft gap

dA = sorted(glob.glob(os.path.join(ROOT, "renders", f"Cesium_{a.cam}_{a.geo}_png", "depth_*.png")))
dB = sorted(glob.glob(os.path.join(ROOT, "renders", f"Cesium_{a.cam}_{a.geo_nc}_png", "depth_*.png")))
bt = sorted(glob.glob(os.path.join(ROOT, "renders", f"Beauty_{a.cam}_{a.geo}_png", "beauty_*.png"))) if a.car_edges else []
n = min(len(dA), len(dB), a.frames or 10 ** 9, len(bt) if a.car_edges else 10 ** 9)
W, H = cv2.imread(dA[0]).shape[1], cv2.imread(dA[0]).shape[0]

# per-pixel ground hit in rig space (x forward along the route, y right), fixed for the whole clip
u = (np.arange(W) + 0.5) / W * 2 - 1; v = (np.arange(H) + 0.5) / H * 2 - 1
uu, vv = np.meshgrid(u, v)
tx, ty = math.tan(math.radians(HFOV / 2)), math.tan(math.radians(HFOV / 2)) * SH / SW
right, up = uu * tx, -vv * ty
ps = math.radians(YAW)
dx = math.cos(ps) - right * math.sin(ps); dy = math.sin(ps) + right * math.cos(ps)
hit = up < -1e-3
t = np.where(hit, H_CAM / np.maximum(-up, 1e-3), 0)
gx = OFF * math.cos(ps) + t * dx; gy = OFF * math.sin(ps) + t * dy
dist = np.hypot(gx, gy); hit &= dist < 12000                    # paint out to 120 m
pix_cm = np.maximum(t * (2 * tx / W), 1e-3)                      # ground footprint of a pixel, for antialiasing


def paint(f):
    img = np.zeros((H, W, 3), np.float32)
    xs = gx + START + SPEED * f / FPS
    for y0, w, col, dashed in LINES:
        cover = np.clip((w / 2 - np.abs(gy - y0)) / pix_cm + 0.5, 0, 1) * hit
        if dashed:
            cover *= (np.mod(xs, DASH + GAP) < DASH)
        img = img * (1 - cover[..., None]) + np.array(col, np.float32) * cover[..., None]
    return img


def writer(path):
    return subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
                             "-s", f"{W}x{H}", "-r", "23.976", "-i", "-", "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", path],
                            stdin=subprocess.PIPE)


if a.check >= 0:   # one frame over the depth, for eyeballing
    d = cv2.imread(dA[a.check]); p = paint(a.check); m = p.max(2, keepdims=True) / 255
    cv2.imwrite(a.out + f"_check{a.check}.png", (d * (1 - m) + p * m).astype(np.uint8)); raise SystemExit
wl, wd = writer(a.out + "_lines.mp4"), writer(a.out + "_depthlines.mp4")
k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
for i in range(n):
    A = cv2.imread(dA[i], cv2.IMREAD_GRAYSCALE).astype(np.float32); B = cv2.imread(dB[i], cv2.IMREAD_GRAYSCALE).astype(np.float32)
    road = cv2.erode(((A - B) <= 3).astype(np.uint8), k).astype(np.float32)[..., None]   # no car in front of the road
    p = paint(i) * road
    m = p.max(2, keepdims=True) / 255
    wl.stdin.write(p.astype(np.uint8).tobytes())
    d = cv2.cvtColor(A.astype(np.uint8), cv2.COLOR_GRAY2BGR).astype(np.float32)
    if a.car_edges:
        car = cv2.dilate(((A - B) > 3).astype(np.uint8), k)
        e = cv2.Canny(cv2.GaussianBlur(cv2.cvtColor(cv2.imread(bt[i]), cv2.COLOR_BGR2GRAY), (3, 3), 0), 60, 140)
        e = (e > 0) & (cv2.erode(car, k) > 0)                  # inner detail only, not the silhouette
        d[e] = d[e] * (1 - a.car_edges) + 255 * a.car_edges
    wd.stdin.write((d * (1 - m) + p * m).astype(np.uint8).tobytes())
for w in (wl, wd):
    w.stdin.close(); w.wait()
print(f"wrote {a.out}_lines.mp4 / _depthlines.mp4: {n} frames")
