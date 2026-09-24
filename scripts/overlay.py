"""Overlay depth-derived edges (red) on a generated still to check perspective match.
usage: python overlay.py <depth_png> <still_png> <out_png>"""
import sys, numpy as np
from PIL import Image, ImageFilter
d = Image.open(sys.argv[1]).convert("L").resize((832, 480))
e = np.array(d.filter(ImageFilter.FIND_EDGES)) > 6
s = np.array(Image.open(sys.argv[2]).convert("RGB").resize((832, 480))).copy()
s[e] = [255, 0, 0]
Image.fromarray(s).save(sys.argv[3])
