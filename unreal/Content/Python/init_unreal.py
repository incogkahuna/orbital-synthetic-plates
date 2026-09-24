# One-shot hook: if Saved/run_c1.flag exists, delete it and run run_c1_test (build rig + render C1 + quit).
import os, unreal
_flag = os.path.join(unreal.Paths.project_saved_dir(), "run_c1.flag")
if os.path.exists(_flag):
    os.remove(_flag)
    import run_c1_test
# One-shot hook: Saved/run_cesium_c1.flag -> cesium_c1_run (Cesium route + rig + C1 render + quit).
_cflag = os.path.join(unreal.Paths.project_saved_dir(), "run_cesium_c1.flag")
if os.path.exists(_cflag):
    os.remove(_cflag)
    import sys; sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import cesium_c1_run
# One-shot hook: Saved/run_rig_capture.flag -> rig_capture (pitch-deck screenshot of PlateRig on a car proxy; never saves).
_rflag = os.path.join(unreal.Paths.project_saved_dir(), "run_rig_capture.flag")
if os.path.exists(_rflag):
    os.remove(_rflag)
    import sys; sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import rig_capture
# One-shot hook: Saved/run_city_capture.flag -> city_capture (pitch-deck aerial wides of the Cesium city; never saves).
_wflag = os.path.join(unreal.Paths.project_saved_dir(), "run_city_capture.flag")
if os.path.exists(_wflag):
    os.remove(_wflag)
    import sys; sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import city_capture
# One-shot hook: Saved/run_color_capture.flag -> color_capture (dusk + tinted pitch wides; never saves).
_kflag = os.path.join(unreal.Paths.project_saved_dir(), "run_color_capture.flag")
if os.path.exists(_kflag):
    os.remove(_kflag)
    import sys; sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import color_capture
