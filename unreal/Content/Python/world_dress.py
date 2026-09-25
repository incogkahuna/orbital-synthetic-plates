"""
world_dress.py — street dressing for the Cesium route (docs/UNREAL_WORLD_PLAN.md, layers 2-4).

Depth only sees shape, so everything here is simple geometry placed where it really is (refs/route_frontage.json,
from OpenStreetMap via scripts/osm_frontage.py) or where LA streets put it (rules below). Timeless or per-era only:
`era` = "1955" | "1980s" | "timeless" changes the awning / blade-sign / bus-shelter / news-rack mix.

Frame: x = metres along the route spline (east from La Brea), y = metres south of our lane (spline right vector).
Called from cesium_c1_run.build_and_render() after the kerbs and lamps; idempotent (clears Dress_* first).
"""
import json, math, os, random
import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
CUBE = "/Engine/BasicShapes/Cube"
CYL = "/Engine/BasicShapes/Cylinder"
SPH = "/Engine/BasicShapes/Sphere"

KERB_S, KERB_N = 4.1, -17.2          # our kerbs (m), cesium_c1_run.KERB_R_CM / KERB_L_CM
KERB_H = 0.22                         # sidewalk top above the lane (m), cesium_c1_run.KERB_H_CM
GF_H = 4.2                            # ground-floor storefront height (m)
# Palms dominate: primitive leaf-clump trees read as sign clusters to Wan (A/B v9d/v9e, 2026-09-24); leafy trees
# stay rare until real tree meshes come from Fab. Frond-crown palms read as palms.
ERA_MIX = {   # probabilities per era
    "1955":     {"awning": 0.60, "blade": 0.80, "shelter": 0.0, "racks": 2, "palm": 0.85, "wires": 0.25},
    "1980s":    {"awning": 0.35, "blade": 0.40, "shelter": 1.0, "racks": 3, "palm": 0.90, "wires": 0.15},
    "timeless": {"awning": 0.45, "blade": 0.55, "shelter": 0.5, "racks": 2, "palm": 0.85, "wires": 0.20},
}


class Dresser:
    def __init__(self, spl, data, era, seed, intersections_m, log):
        self.spl, self.d, self.era, self.log = spl, data, era, log
        self.mix = ERA_MIX.get(era, ERA_MIX["timeless"])
        self.rnd = random.Random(seed)
        self.total_m = spl.get_spline_length() / 100.0
        self.meshes = {k: unreal.load_asset(k) for k in (CUBE, CYL, SPH)}
        self.n = 0
        self.cross = intersections_m
        self.openings = data.get("openings", [])
        self.bus = [(f["x"], "S" if f["y"] > -6.6 else "N") for f in data["furniture"] if f["kind"] == "bus_stop"]

    # ---- placement helpers -------------------------------------------------------------------------------
    def at(self, x_m, y_m, z_m=0.0):
        d = max(0.0, min(x_m * 100.0, self.total_m * 100.0))
        W = unreal.SplineCoordinateSpace.WORLD
        p = self.spl.get_location_at_distance_along_spline(d, W)
        r = self.spl.get_right_vector_at_distance_along_spline(d, W)
        yaw = self.spl.get_rotation_at_distance_along_spline(d, W).yaw
        return unreal.Vector(p.x + r.x * y_m * 100, p.y + r.y * y_m * 100, p.z + z_m * 100), yaw

    def put(self, kind, mesh, x, y, z, size_m, yaw_off=0.0, roll=0.0, pitch=0.0):
        """Spawn a primitive centred at (x, y, z) in route space; size in metres along (route, lateral, up)."""
        loc, yaw = self.at(x, y, z)
        a = EAS.spawn_actor_from_class(unreal.StaticMeshActor, loc, unreal.Rotator(roll, pitch, yaw + yaw_off))
        a.set_actor_label(f"Dress_{kind}_{self.n:05d}"); self.n += 1
        a.static_mesh_component.set_static_mesh(self.meshes[mesh])
        a.set_actor_scale3d(unreal.Vector(size_m[0], size_m[1], size_m[2]))
        a.set_folder_path(f"Dressing/{kind}")
        return a

    def blocked(self, x, side, pad=0.0):
        if x < 2 or x > self.total_m - 2:
            return True
        if any(abs(x - m) < 8.0 + 3.0 + pad for m in self.cross):
            return True
        if any(o["side"] == side and abs(x - o["x"]) < o["half_w"] + 1.0 + pad for o in self.openings):
            return True
        return any(s == side and abs(x - bx) < 6.0 + pad for bx, s in self.bus)

    # ---- layer 2: storefront band --------------------------------------------------------------------------
    def storefronts(self):
        count = {"bays": 0, "awnings": 0, "signs": 0, "cornices": 0}
        for b in self.d["frontage"]:
            x0, x1, fy, side = b["face_x0"], b["face_x1"], b["face_y"], b["side"]
            if x1 - x0 < 4.0 or x1 < 0 or x0 > self.total_m:
                continue
            out = -1.0 if side == "S" else 1.0          # direction from the facade toward the street
            x = max(x0, 0.5)
            while x < min(x1, self.total_m) - 3.0:
                w = min(self.rnd.uniform(5.0, 9.0), min(x1, self.total_m) - x)
                cx = x + w / 2
                # pilaster at the bay start + bulkhead under the shop window
                self.put("Pilaster", CUBE, x + 0.22, fy + out * 0.12, KERH(GF_H / 2), (0.45, 0.25, GF_H))
                self.put("Bulkhead", CUBE, cx, fy + out * 0.06, KERH(0.3), (w - 0.5, 0.12, 0.6))
                if self.rnd.random() < self.mix["awning"]:
                    dep = self.rnd.uniform(1.2, 2.2)
                    self.put("Awning", CUBE, cx, fy + out * dep / 2, KERH(self.rnd.uniform(2.8, 3.1)),
                             (w - 0.6, dep, 0.12), roll=-out * 14.0)
                    count["awnings"] += 1
                if self.rnd.random() < 0.6:
                    self.put("SignBoard", CUBE, cx, fy + out * 0.1, KERH(self.rnd.uniform(3.5, 4.0)),
                             (w * self.rnd.uniform(0.7, 0.9), 0.18, self.rnd.uniform(0.8, 1.2)))
                    count["signs"] += 1
                count["bays"] += 1
                x += w
            h = float(b["height"]) if b.get("height") else None
            if h and h > GF_H + 1.5:                    # cornice / parapet cap along the roofline
                self.put("Cornice", CUBE, (x0 + x1) / 2, fy + out * 0.25, KERH(h - 0.35),
                         (x1 - x0, 0.5, 0.35))
                count["cornices"] += 1
        # blade signs at real businesses, sticking out over the sidewalk
        blades = 0
        for s in self.d["shops"]:
            if self.rnd.random() > self.mix["blade"]:
                continue
            fr = [b for b in self.d["frontage"] if b["side"] == s["side"] and b["face_x0"] - 1 <= s["x"] <= b["face_x1"] + 1]
            if not fr:
                continue
            fy = fr[0]["face_y"]; out = -1.0 if s["side"] == "S" else 1.0
            self.put("BladeSign", CUBE, s["x"], fy + out * 0.75, KERH(self.rnd.uniform(4.2, 5.2)),
                     (0.15, 1.2, self.rnd.uniform(1.6, 2.6)))
            blades += 1
        self.log(f"dress storefronts: {count}, blade signs {blades}")

    # ---- layer 3: kerb & sidewalk furniture -----------------------------------------------------------------
    def sidewalks(self):
        c = {"trees": 0, "palms": 0, "meters": 0, "hydrants": 0, "bus": 0, "corners": 0}
        for side, kerb, inward in (("S", KERB_S, 1.0), ("N", KERB_N, -1.0)):
            ty = kerb + inward * 1.2                     # tree / pole line, 1.2 m in from the kerb
            my = kerb + inward * 0.45                    # meter line
            trees = []
            x = self.rnd.uniform(4, 10)
            while x < self.total_m:
                if not self.blocked(x, side):
                    if self.rnd.random() < self.mix["palm"]:
                        # palm: tall thin trunk + a spiky crown of drooping fronds (a disc read as a street lamp;
                        # a head sphere read as a globe sign - Danny 2026-09-24: no spheres anywhere)
                        h = self.rnd.uniform(14, 20)
                        self.put("PalmTrunk", CYL, x, ty, KERH(h / 2), (0.4, 0.4, h))
                        for k in range(9):
                            yaw = k * 40.0 + self.rnd.uniform(-12, 12)
                            L, droop = self.rnd.uniform(2.6, 3.4), self.rnd.uniform(18, 38)
                            dx = math.cos(math.radians(yaw)) * L * 0.45
                            dy = math.sin(math.radians(yaw)) * L * 0.45
                            self.put("PalmFrond", CUBE, x + dx, ty + dy, KERH(h - 0.35), (L, 0.45, 0.06),
                                     yaw_off=yaw, pitch=-droop)
                        c["palms"] += 1
                    else:
                        # no leafy street trees until real tree meshes (Fab): every primitive leaf clump, round or
                        # clumpy, came back from Wan as a cluster of globe / neon signs (v9d-v11, Danny 2026-09-24).
                        # The slot stays empty - a gap in the palm row.
                        x += self.rnd.uniform(11, 15)
                        continue
                    trees.append(x)
                x += self.rnd.uniform(11, 15)
            x = 3.0
            while x < self.total_m:
                if not self.blocked(x, side, 1.0) and all(abs(x - t) > 1.5 for t in trees):
                    self.put("Meter", CYL, x, my, KERH(0.55), (0.07, 0.07, 1.1))
                    self.put("MeterHead", CUBE, x, my, KERH(1.25), (0.18, 0.14, 0.32))
                    c["meters"] += 1
                x += 6.5
            x = self.rnd.uniform(30, 90)
            while x < self.total_m:                      # hydrants ~ every 90-110 m
                if not self.blocked(x, side):
                    self.put("Hydrant", CYL, x, kerb + inward * 0.6, KERH(0.38), (0.28, 0.28, 0.75))
                    self.put("HydrantCap", CYL, x, kerb + inward * 0.6, KERH(0.8), (0.24, 0.24, 0.1))
                    c["hydrants"] += 1
                x += self.rnd.uniform(90, 110)
        # real bus stops: bench at the back of the sidewalk, sign pole at the kerb, 1980s shelters
        fy = {"S": 8.9, "N": -21.6}
        for bx, side in self.bus:
            if not 0 < bx < self.total_m:
                continue
            kerb, inward = (KERB_S, 1.0) if side == "S" else (KERB_N, -1.0)
            back = fy[side] - inward * 1.0
            self.put("BusSign", CYL, bx + 3.0, kerb + inward * 0.5, KERH(1.5), (0.08, 0.08, 3.0))
            self.put("BusSignPlate", CUBE, bx + 3.0, kerb + inward * 0.5, KERH(2.7), (0.05, 0.5, 0.7))
            self.put("BusBench", CUBE, bx, back, KERH(0.45), (2.0, 0.5, 0.1))
            self.put("BusBenchBack", CUBE, bx, back + inward * 0.25, KERH(0.8), (2.0, 0.08, 0.6))
            if self.rnd.random() < self.mix["shelter"]:
                self.put("ShelterRoof", CUBE, bx, back, KERH(2.5), (3.6, 1.7, 0.1))
                self.put("ShelterBack", CUBE, bx, back + inward * 0.8, KERH(1.25), (3.6, 0.05, 2.1))
            c["bus"] += 1
        # street corners: bin, mailbox, news racks, just past each crossing
        for m in self.cross:
            for side, kerb, inward in (("S", KERB_S, 1.0), ("N", KERB_N, -1.0)):
                for sgn in (-1, 1):
                    x = m + sgn * 12.0
                    if not 2 < x < self.total_m - 2:
                        continue
                    y = kerb + inward * 1.0
                    self.put("Bin", CYL, x, y, KERH(0.47), (0.55, 0.55, 0.95))
                    if sgn > 0:
                        self.put("Mailbox", CUBE, x + 1.4, y, KERH(0.6), (0.5, 0.5, 1.2))
                        for k in range(self.mix["racks"]):
                            self.put("NewsRack", CUBE, x + 2.4 + k * 0.55, y, KERH(0.5), (0.45, 0.4, 1.0))
                    c["corners"] += 1
        self.log(f"dress sidewalks: {c}")

    # ---- overhead wires: occasional only (Danny, R3 2026-09-24) ----------------------------------------------
    def wires(self):
        """Some blocks get a line of wooden utility poles with three wires on ONE side; most blocks get none."""
        edges = [0.0] + list(self.cross) + [self.total_m]
        blocks, poles = 0, 0
        # an exact share of the eligible blocks, not a coin flip per block: v12 rolled 7 of 14 at p = 0.3
        spans = [(a, b) for a, b in zip(edges, edges[1:]) if b - a >= 60]
        wired = set(self.rnd.sample(range(len(spans)), round(self.mix["wires"] * len(spans)))) if spans else set()
        for i, (a, b) in enumerate(spans):
            if i not in wired:
                continue
            side, kerb, inward = (("S", KERB_S, 1.0), ("N", KERB_N, -1.0))[self.rnd.random() < 0.5]
            y = kerb + inward * 0.7
            xs, x = [], a + 12.0
            while x < b - 12.0:
                if not self.blocked(x, side):
                    xs.append(x)
                x += self.rnd.uniform(38.0, 45.0)
            if len(xs) < 2:
                continue
            for x in xs:
                self.put("UtilityPole", CYL, x, y, KERH(5.5), (0.3, 0.3, 11.0))
                self.put("UtilityCrossarm", CUBE, x, y, KERH(10.3), (0.12, 2.2, 0.12))
                poles += 1
            for x0, x1 in zip(xs, xs[1:]):
                for dy in (-0.9, 0.0, 0.9):
                    self.put("UtilityWire", CUBE, (x0 + x1) / 2, y + dy, KERH(10.4), (x1 - x0, 0.05, 0.05))
            blocks += 1
        self.log(f"dress wires: {blocks} of {len(edges) - 1} blocks, {poles} poles")

    def no_park_m(self):
        """Stretches of our (south) kerb where cars can't park: driveways, bus stops, hydrant zones, crossings."""
        zones = [(o["x"] - o["half_w"] - 1.0, o["x"] + o["half_w"] + 1.0) for o in self.openings if o["side"] == "S"]
        zones += [(bx - 12.0, bx + 6.0) for bx, s in self.bus if s == "S"]
        zones += [(m - 12.0, m + 12.0) for m in self.cross]
        return zones


def KERH(z_m):
    """Height above the sidewalk surface (sidewalk top is KERB_H above the lane spline)."""
    return KERB_H + z_m


def clear():
    n = 0
    for a in EAS.get_all_level_actors():
        if a.get_actor_label().startswith("Dress_"):
            EAS.destroy_actor(a); n += 1
    return n


def dress(spl, era="timeless", seed=1978, intersections_m=(), log=print):
    root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))   # repo root from unreal/Content/Python
    path = os.environ.get("ORBITAL_FRONTAGE", os.path.join(root, "refs", "route_frontage.json"))
    data = json.load(open(path, encoding="utf-8"))
    log(f"dress: cleared {clear()} old actors; era {era}, seed {seed}, data {os.path.basename(path)}")
    d = Dresser(spl, data, era, seed, list(intersections_m), log)
    d.storefronts()
    d.sidewalks()
    d.wires()
    log(f"dress: {d.n} actors")
    return d.no_park_m()
