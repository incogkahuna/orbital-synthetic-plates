"""Magnific API video upscale: upload a local clip to Magnific's own storage, run an upscaler, download the result.
Key: MAGNIFIC_API_KEY (Windows user env var; never printed). Docs: https://docs.magnific.com
usage: python magnific_upscale.py <clip.mp4> <out_dir> precision|topaz [--resolution 1k] [--strength 60] [--sharpen 20]
                                  [--model starlight_precise_2_5] [--noise 0]"""
import argparse, json, os, sys, time, urllib.request

ap = argparse.ArgumentParser()
ap.add_argument("clip"); ap.add_argument("out_dir"); ap.add_argument("engine", choices=["precision", "topaz"])
ap.add_argument("--resolution", default="1k"); ap.add_argument("--strength", type=int, default=60)
ap.add_argument("--sharpen", type=int, default=0); ap.add_argument("--model", default="starlight_precise_2_5")
ap.add_argument("--noise", type=float, default=0.0); ap.add_argument("--tag", default="")
a = ap.parse_args()

KEY = os.environ.get("MAGNIFIC_API_KEY")
if not KEY:
    try:
        import winreg
        KEY = winreg.QueryValueEx(winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment"), "MAGNIFIC_API_KEY")[0]
    except OSError:
        sys.exit("MAGNIFIC_API_KEY not set")
API = "https://api.magnific.com"


def call(method, path, body=None):
    req = urllib.request.Request(API + path, data=json.dumps(body).encode() if body is not None else None, method=method,
                                 headers={"x-magnific-api-key": KEY, "Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e:
        sys.exit(f"{method} {path} -> HTTP {e.code}: {e.read().decode()[:500]}")


def log(s):
    print(time.strftime("%H:%M:%S"), s, flush=True)


os.makedirs(a.out_dir, exist_ok=True)
# 1. upload to Magnific storage (short-lived signed PUT, asset_url readable for 24 h)
r = call("POST", "/v1/ai/uploads/request-url", {"files": [{"content_type": "video/mp4"}]})
f = (r.get("data") or r)["files"][0] if isinstance(r, dict) else r[0]
data = open(a.clip, "rb").read()
put = urllib.request.Request(f["upload_url"], data=data, method="PUT", headers=f.get("headers") or {"Content-Type": "video/mp4"})
urllib.request.urlopen(put, timeout=600)
log(f"uploaded {os.path.basename(a.clip)} ({len(data) / 1e6:.1f} MB) as {f['file_id']}")

# 2. submit
if a.engine == "precision":
    path = "/v1/ai/video-upscaler-precision"
    body = {"video": f["asset_url"], "resolution": a.resolution, "strength": a.strength, "sharpen": a.sharpen,
            "smart_grain": 0, "output_format": "h264"}          # no grain: plates look like life, not film
else:
    path = "/v1/ai/video-upscaler-topaz"
    body = {"video": f["file_id"], "enhancement_model": a.model, "resolution": a.resolution, "noise": a.noise}
r = call("POST", path, body)
task = r["data"]["task_id"]; log(f"{a.engine} task {task} {r['data']['status']} {json.dumps(body | {'video': '<upload>'})}")

# 3. poll
t0 = time.time()
while True:
    time.sleep(20)
    d = call("GET", f"{path}/{task}")["data"]
    if d["status"] in ("COMPLETED", "FAILED"):
        break
    if time.time() - t0 > 3600:
        sys.exit(f"timed out, task {task} still {d['status']}")
if d["status"] == "FAILED":
    sys.exit(f"FAILED: {json.dumps(d)[:500]}")
log(f"completed in {time.time() - t0:.0f}s")

# 4. download
base = os.path.splitext(os.path.basename(a.clip))[0]
for i, url in enumerate(d.get("generated") or []):
    out = os.path.join(a.out_dir, f"{base}_magnific_{a.engine}{('_' + a.tag) if a.tag else ''}_{a.resolution}{'' if i == 0 else '_' + str(i)}.mp4")
    urllib.request.urlretrieve(url, out)
    log(f"DONE {out}")
with open(os.path.join(a.out_dir, "runs.jsonl"), "a") as fh:
    fh.write(json.dumps({"time": time.strftime("%Y-%m-%d %H:%M"), "clip": os.path.basename(a.clip), "engine": a.engine,
                         "task": task, "params": body | {"video": "<upload>"}, "seconds": round(time.time() - t0)}) + "\n")
