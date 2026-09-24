import unreal
for cls in ("CesiumSampleHeightMostDetailedAsyncAction", "Cesium3DTileset", "CesiumGeoreference", "CesiumSampleHeightResult"):
    c = getattr(unreal, cls, None)
    names = [n for n in dir(c) if not n.startswith("_") and any(k in n.lower() for k in ("height", "sample", "origin", "transform", "activate", "on_"))] if c else "MISSING"
    unreal.log(f"[APIDUMP] {cls}: {names}")
