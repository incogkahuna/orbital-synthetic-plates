# incremental: MRQ EXR seq -> depth_%06d.png + beauty_%06d.png (skips existing; safe to re-run)
# usage: python exr_to_png.py <exr_dir> <out_dir> <W> <H> [time_budget_s]
# then:  ffmpeg -framerate 24 -i depth_%06d.png -c:v libx264 -profile:v high -pix_fmt yuv420p -crf 14 depth.mp4
import sys, glob, os, time
import numpy as np, OpenEXR, Imath
from PIL import Image
src, out, W, H = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
budget = float(sys.argv[5]) if len(sys.argv) > 5 else 1e9
NEAR_CM, FAR_CM = 100.0, 20000.0       # ONE log normalisation, 1-200 m, for every frame and camera
FL = Imath.PixelType(Imath.PixelType.FLOAT)
os.makedirs(out, exist_ok=True); t0 = time.time(); n = 0
for i, p in enumerate(sorted(glob.glob(os.path.join(src, '*.exr')))):
    dp, bp = os.path.join(out, 'depth_%06d.png' % i), os.path.join(out, 'beauty_%06d.png' % i)
    if os.path.exists(dp) and os.path.exists(bp): continue
    if time.time() - t0 > budget: break
    f = OpenEXR.InputFile(p); dw = f.header()['dataWindow']; w = dw.max.x + 1; h = dw.max.y + 1
    ch = lambda c: np.frombuffer(f.channel(c, FL), dtype=np.float32).reshape(h, w)
    d = ch('FinalImageMovieRenderQueue_WorldDepth.R')
    dn = 1.0 - (np.log(np.clip(d, NEAR_CM, FAR_CM)) - np.log(NEAR_CM)) / (np.log(FAR_CM) - np.log(NEAR_CM))
    Image.fromarray((dn * 255).astype(np.uint8)).resize((W, H), Image.LANCZOS).convert('RGB').save(dp)
    b = np.stack([ch('R'), ch('G'), ch('B')], -1); b = np.clip(b, 0, None); b = b / (1 + b)
    Image.fromarray((np.clip(b, 0, 1) ** (1 / 2.2) * 255).astype(np.uint8)).resize((W, H), Image.LANCZOS).save(bp)
    n += 1
print('converted', n, 'total', len(glob.glob(os.path.join(out, 'depth_*.png'))))
