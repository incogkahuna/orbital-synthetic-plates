import sys, os, unreal
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import orbital_plates_rig as rig
rig.CONFIG["duration_s"] = 30.0
MARK = os.path.join(unreal.Paths.project_saved_dir(), "c1_status.txt")
def mark(s):
    open(MARK, "a").write(s + "\n"); unreal.log("[C1TEST] " + s)
state = {"ticks": 0, "h": None, "ex": None}
def finished(executor, success):
    mark(f"render finished success={success}")
    unreal.SystemLibrary.quit_editor()
def go():
    try:
        unreal.EditorLevelLibrary.new_level("/Game/OrbitalPlates/PlatesMain")
        rig.main()
        mark("rig built + level saved")
        q = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem).get_queue()
        for j in q.get_jobs():
            j.set_is_enabled(j.job_name == "SEQ_PlateRing_C1")
        qs = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
        ex = qs.render_queue_with_executor(unreal.MoviePipelinePIEExecutor)
        state["ex"] = ex
        ex.on_executor_finished_delegate.add_callable(finished)
        mark("render started")
    except Exception as e:
        import traceback; mark("ERROR " + traceback.format_exc())
def tick(dt):
    state["ticks"] += 1
    if state["ticks"] == 300:
        unreal.unregister_slate_post_tick_callback(state["h"])
        go()
state["h"] = unreal.register_slate_post_tick_callback(tick)
