"""Analyse OSM data along the plate route: which buildings front Sunset Blvd, how far back, and what is on the
street, in the route's local frame (x = metres east along the lane from La Brea, y = metres south of the lane;
same frame as Cesium's georeference at LANE_START). Writes refs/route_frontage.json for the Unreal dressing script.
usage: python osm_frontage.py"""
import json, math, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANE_START = (-118.3440998, 34.0979128)   # lon, lat — right-hand lane centre at La Brea (cesium_c1_run.py)
LANE_END = (-118.3215900, 34.0979552)
M_LAT = 110950.0
M_LON = 111320.0 * math.cos(math.radians(LANE_START[1]))
ex, ny = (LANE_END[0] - LANE_START[0]) * M_LON, (LANE_END[1] - LANE_START[1]) * M_LAT
L = math.hypot(ex, ny); ux, uy = ex / L, ny / L          # along-route unit vector (east-north)


def local(lon, lat):
    e, n = (lon - LANE_START[0]) * M_LON, (lat - LANE_START[1]) * M_LAT
    return e * ux + n * uy, -(-e * uy + n * ux)          # (along, south-positive lateral)


osm = json.load(open(f"{ROOT}/refs/osm_sunset_labrea_gower.json", encoding="utf-8"))["elements"]
pois = json.load(open(f"{ROOT}/refs/osm_sunset_pois.json", encoding="utf-8"))["elements"]

# The OSM centreline is 6.6 m north of our lane (y = -6.6). Road edge ~ +/-15 m from the centreline.
CL = -6.6
front, furniture = [], []
for el in osm:
    t = el.get("tags", {})
    if el["type"] == "way" and "building" in t and el.get("geometry"):
        pts = [local(p["lon"], p["lat"]) for p in el["geometry"]]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        if max(xs) < -60 or min(xs) > L + 60:
            continue
        side = "S" if sum(ys) / len(ys) > CL else "N"
        # street-facing edge = the footprint vertex set closest to the centreline
        near = min(ys) - CL if side == "S" else CL - max(ys)
        if near > 45:                       # set back more than 45 m from the centreline: not a frontage
            continue
        # street face line: the footprint edge nearest the street, as its y and the x-span of vertices within
        # 1.5 m of it (so a stepped or angled footprint only gets dressing along the wall that actually fronts)
        face_y = min(ys) if side == "S" else max(ys)
        fx = [p[0] for p in pts if abs(p[1] - face_y) < 1.5]
        front.append({"id": el["id"], "side": side, "x0": round(min(xs), 1), "x1": round(max(xs), 1),
                      "face_y": round(face_y, 2), "face_x0": round(min(fx), 1), "face_x1": round(max(fx), 1),
                      "setback_m": round(near, 1), "levels": t.get("building:levels"), "height": t.get("height"),
                      "kind": t.get("building"), "name": t.get("name")})
    elif el["type"] == "node":
        x, y = local(el["lon"], el["lat"])
        if -60 < x < L + 60 and abs(y - CL) < 40:
            kind = (t.get("highway") or t.get("emergency") or t.get("amenity") or t.get("natural")
                    or t.get("advertising") or t.get("man_made") or t.get("power"))
            furniture.append({"kind": kind, "x": round(x, 1), "y": round(y, 1)})
# driveways / alleys / side streets: where a service or minor road crosses either sidewalk line
KERB_S, KERB_N = 4.1, -17.2        # our kerbs (m from our lane), cesium_c1_run.py
openings = []
for el in osm:
    t = el.get("tags", {})
    if el["type"] != "way" or "building" in t or not el.get("geometry"):
        continue
    hw = t.get("highway")
    if hw not in ("service", "residential", "tertiary", "secondary", "unclassified", "living_street"):
        continue
    pts = [local(p["lon"], p["lat"]) for p in el["geometry"]]
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        for side, ky in (("S", KERB_S + 2.5), ("N", KERB_N - 2.5)):
            if (ya - ky) * (yb - ky) < 0 and abs(yb - ya) > 1e-6:
                x = xa + (ky - ya) * (xb - xa) / (yb - ya)
                if -20 < x < L + 20:
                    openings.append({"side": side, "x": round(x, 1), "kind": hw,
                                     "half_w": 3.5 if hw == "service" else 8.0})
shops = []
for el in pois:
    t = el.get("tags", {})
    x, y = local(el["lon"], el["lat"])
    if -60 < x < L + 60 and abs(y - CL) < 45:
        shops.append({"x": round(x, 1), "y": round(y, 1), "side": "S" if y > CL else "N",
                      "kind": t.get("shop") or t.get("amenity") or t.get("office") or t.get("tourism")
                      or t.get("leisure") or t.get("craft"), "name": t.get("name")})

front.sort(key=lambda b: (b["side"], b["x0"]))
out = {"frame": "x east along lane from La Brea (m), y south of lane (m); OSM centreline at y=-6.6",
       "route_len_m": round(L, 1), "frontage": front, "furniture": furniture,
       "openings": sorted(openings, key=lambda o: (o["side"], o["x"])), "shops": sorted(shops, key=lambda s: s["x"])}
json.dump(out, open(f"{ROOT}/refs/route_frontage.json", "w"), indent=1)

for side in "NS":
    fb = [b for b in front if b["side"] == side]
    cover = sum(b["x1"] - b["x0"] for b in fb)
    sb = sorted(b["setback_m"] for b in fb)
    print(f"side {side}: {len(fb)} frontage buildings, ~{cover:.0f} m of footprint along {L:.0f} m, "
          f"setback median {sb[len(sb)//2] if sb else '-'} m, "
          f"levels given for {sum(1 for b in fb if b['levels'])}, heights for {sum(1 for b in fb if b['height'])}")
kinds = {}
for f in furniture:
    kinds[f["kind"]] = kinds.get(f["kind"], 0) + 1
print("sidewalk openings:", {s: sum(1 for o in openings if o["side"] == s) for s in "NS"}, "(service:",
      sum(1 for o in openings if o["kind"] == "service"), ")")
print("street furniture within 40 m:", dict(sorted(kinds.items(), key=lambda kv: -kv[1])))
sk = {}
for s in shops:
    sk[s["kind"]] = sk.get(s["kind"], 0) + 1
print(f"businesses within 45 m: {len(shops)};", dict(sorted(sk.items(), key=lambda kv: -kv[1])[:14]))
