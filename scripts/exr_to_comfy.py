"""exr_to_comfy.py — S2→S3 prep. MRQ multilayer EXR sequence → depth + beauty
videos for the Comfy restyle graph. ONE fixed depth normalisation for the whole
sequence (and, in production, for all nine cameras) so tile 3 and tile 40 agree.
"""
import sys, glob, os
import numpy as np, OpenEXR, Imath, imageio.v3 as iio

src, out, W, H = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
NEAR_CM, FAR_CM = 100.0, 20000.0           # 1 m .. 200 m log range, near = white
FL = Imath.PixelType(Imath.PixelType.FLOAT)

def load(path):
    f = OpenEXR.InputFile(path); dw = f.header()['dataWindow']; w = dw.max.x + 1; h = dw.max.y + 1
    ch = lambda n: np.frombuffer(f.channel(n, FL), dtype=np.float32).reshape(h, w)
    beauty = np.stack([ch('R'), ch('G'), ch('B')], -1)
    depth = ch('FinalImageMovieRenderQueue_WorldDepth.R')
    return beauty, depth

def resize(img, W, H):
    from PIL import Image
    return np.asarray(Image.fromarray(img).resize((W, H), Image.LANCZOS))

def tonemap(x):                              # scene-linear -> display, cheap filmic
    x = np.clip(x, 0, None); x = x / (1 + x)
    return (np.clip(x, 0, 1) ** (1 / 2.2) * 255).astype(np.uint8)

files = sorted(glob.glob(os.path.join(src, '*.exr')))
dep, bea = [], []
for p in files:
    b, d = load(p)
    dn = 1.0 - (np.log(np.clip(d, NEAR_CM, FAR_CM)) - np.log(NEAR_CM)) / (np.log(FAR_CM) - np.log(NEAR_CM))
    dimg = (np.repeat(dn[..., None], 3, -1) * 255).astype(np.uint8)
    dep.append(resize(dimg, W, H)); bea.append(resize(tonemap(b), W, H))
os.makedirs(out, exist_ok=True)
iio.imwrite(os.path.join(out, 'depth.mp4'), np.stack(dep), fps=16, codec='libx264', quality=10, pixelformat='yuv420p', output_params=['-profile:v','high'])
iio.imwrite(os.path.join(out, 'beauty.mp4'), np.stack(bea), fps=16, codec='libx264', quality=10, pixelformat='yuv420p', output_params=['-profile:v','high'])
iio.imwrite(os.path.join(out, 'depth_f0.png'), dep[0]); iio.imwrite(os.path.join(out, 'beauty_f0.png'), bea[0])
print(f'{len(files)} frames -> {out}')
