"""Apply the run_era.py sky / colour locks after the fact to a finished run's frames (quick look, no GPU).
In a real run the locked frames also seed the next window, so this understates the effect on drift.
usage: python stabilise_offline.py <frames_dir> <depth_png_dir> <out_mp4> [skymode 1|2] [blur]"""
import sys, glob, os, subprocess, shutil
import numpy as np, cv2
from PIL import Image, ImageFilter

fdir, ddir, out = sys.argv[1:4]
mode = sys.argv[4] if len(sys.argv) > 4 else "2"
k = float(sys.argv[5]) if len(sys.argv) > 5 else 18.0
frames = sorted(glob.glob(f"{fdir}/*.png")); depth = sorted(glob.glob(f"{ddir}/depth_*.png"))
sky_plate = np.zeros((480, 832, 3), np.float32); seen = np.zeros((480, 832), bool); ref = None; sref = None
tmp = out + "_frames"; os.makedirs(tmp, exist_ok=True)
for i, f in enumerate(frames):
    a = np.asarray(Image.open(f).convert("RGB"), np.float32)
    d = np.asarray(Image.open(depth[i]).convert("L"), np.float32)
    mi = Image.fromarray(((d <= 6) * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(2))
    m = np.asarray(mi, np.float32) / 255.0
    g = m < 0.5
    mu, sd = a[g].mean(0), a[g].std(0) + 1e-3
    if ref is None:
        ref = (mu, sd)
    else:
        a = np.where(g[..., None], (a - mu) / sd * ref[1] + ref[0], a)
    if mode == "3":
        s = m > 0.99
        if s.sum() > 500:
            smu, ssd = a[s].mean(0), a[s].std(0) + 1e-3
            if sref is None: sref = (smu, ssd)
            else: a = np.where((m > 0.5)[..., None], (a - smu) / ssd * sref[1] + sref[0], a)
        wm = cv2.GaussianBlur(m, (0, 0), k) + 1e-4
        low = cv2.GaussianBlur(a * m[..., None], (0, 0), k) / wm[..., None]
        new = (m > 0.99) & ~seen; sky_plate[new] = low[new]; seen[new] = True
        upd = (m > 0.5) & seen; sky_plate[upd] = 0.96 * sky_plate[upd] + 0.04 * low[upd]
        kk = (m * seen)[..., None]; a = a * (1 - kk) + (a - low + sky_plate) * kk
    elif mode == "2":
        wm = cv2.GaussianBlur(m, (0, 0), k) + 1e-4
        low = cv2.GaussianBlur(a * m[..., None], (0, 0), k) / wm[..., None]
        new = (m > 0.99) & ~seen; sky_plate[new] = low[new]; seen[new] = True
        kk = (m * seen)[..., None]; a = a * (1 - kk) + (a - low + sky_plate) * kk
    else:
        new = (m > 0.99) & ~seen; sky_plate[new] = a[new]; seen[new] = True
        kk = (m * seen)[..., None]; a = a * (1 - kk) + sky_plate * kk
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(f"{tmp}/{i:06d}.png")
ff = shutil.which("ffmpeg")
subprocess.run([ff, "-y", "-loglevel", "error", "-framerate", "24000/1001", "-i", f"{tmp}/%06d.png", "-c:v", "libx264",
                "-pix_fmt", "yuv420p", "-crf", "14", out], check=True)
print("wrote", out, len(frames), "frames")
