"""Location-aware prompts: split a plate into N equal time segments and, for each, name the real places on Sunset Blvd
the camera actually sees then (OpenStreetMap, refs/route_landmarks_osm.json). LTX picks segment i's prompt for the context
windows centred in that segment (LTXVContextWindows split_conds_to_windows).
Front camera sees ~0-140 m ahead (north side on frame-left); rear sees ~0-140 m behind (north side on frame-right).
usage: python landmark_prompts.py <C1|C5> <seconds> <segments> <base_prompt.txt> <out.json>"""
import json, os, sys

cam, secs, nseg, base_p, out = sys.argv[1], float(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5]
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
L = json.load(open(os.path.join(ROOT, "refs", "route_landmarks_osm.json"), encoding="utf-8"))
START_M, SPEED = 200.0, 13.4                      # camera_start_cm / 100, speed_mps (cesium_c1_run / rig)
REACH = 140.0
SKIP = ("Building ", "Stage ", "Alley", "Kraut Law", "Psychiatry")
base = open(base_p, encoding="utf-8").read().strip()
streets = {k.replace("North ", "").replace("West ", ""): (v + 118.3440998) * 92190 for k, v in L["streets"].items()
           if not k.startswith(("Alley", "Walk", "West Sunset"))}
segs = []
for i in range(nseg):
    t0, t1 = secs * i / nseg, secs * (i + 1) / nseg
    x0, x1 = START_M + SPEED * t0, START_M + SPEED * t1
    lo, hi = (x0, x1 + REACH) if cam == "C1" else (x0 - REACH, x1)
    left, right, cross = [], [], []
    for x, name, side, kind, num in L["rows"]:
        if not name or name.startswith(SKIP) or not lo <= x <= hi:
            continue
        north = side.startswith("N")
        (left if north == (cam == "C1") else right).append(name)
    cross = [s for s, x in streets.items() if lo <= x <= hi]
    uniq = lambda xs: list(dict.fromkeys(xs))[:6]
    bits = []
    if cross:
        bits.append("We pass the intersection" + ("s" if len(cross) > 1 else "") + " with " + " and ".join(uniq(cross)) + ".")
    if left:
        bits.append("On the left side of the street: " + ", ".join(uniq(left)) + ", with their real lit signs and storefronts.")
    if right:
        bits.append("On the right side of the street: " + ", ".join(uniq(right)) + ", with their real lit signs and storefronts.")
    segs.append({"t0": round(t0, 1), "t1": round(t1, 1), "prompt": base + " " + " ".join(bits)})
json.dump(segs, open(out, "w", encoding="utf-8"), indent=1)
for s in segs:
    print(f"{s['t0']:5.1f}-{s['t1']:5.1f}s  {s['prompt'][len(base):][:230]}")
