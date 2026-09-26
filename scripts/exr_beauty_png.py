"""Save the tone-mapped beauty (RGB) channels of an Unreal MRQ multilayer EXR sequence as 832x480 PNGs.
usage: python exr_beauty_png.py <exr_dir> <out_dir> [w h]"""
import glob, os, sys
import numpy as np, cv2, OpenEXR, Imath

src, dst = sys.argv[1], sys.argv[2]
W, H = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (832, 480)
os.makedirs(dst, exist_ok=True)
FL = Imath.PixelType(Imath.PixelType.FLOAT)
fs = sorted(glob.glob(os.path.join(src, "*.exr")))
for i, p in enumerate(fs):
    f = OpenEXR.InputFile(p); dw = f.header()["dataWindow"]; w, h = dw.max.x - dw.min.x + 1, dw.max.y - dw.min.y + 1
    rgb = np.stack([np.frombuffer(f.channel(c, FL), np.float32).reshape(h, w) for c in "RGB"], -1)
    rgb = np.nan_to_num(np.clip(rgb, 0, None))
    t = np.clip((rgb / (1 + rgb)) ** (1 / 2.2) * 255, 0, 255).astype(np.uint8)
    cv2.imwrite(os.path.join(dst, f"beauty_{i:06d}.png"), cv2.cvtColor(cv2.resize(t, (W, H), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2BGR))
print("saved", len(fs), "->", dst)
