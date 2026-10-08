"""Every Garmin tool gets complete MCP annotations, derived from its verb."""

import pytest

from garmin_mcp import (
    _ToolFilter,
    activity_analysis,
    activity_management,
    calendar_events,
    challenges,
    courses,
    data_management,
    devices,
    gear_management,
    health_wellness,
    nutrition,
    training,
    user_profile,
    weight_management,
    womens_health,
    workout_builders,
    workouts,
)
from garmin_mcp.annotations import annotations_for, classify, title_for

MODULES = [activity_analysis, activity_management, calendar_events, challenges, courses,
           data_management, devices, gear_management, health_wellness, nutrition, training,
           user_profile, weight_management, womens_health, workout_builders, workouts]


class RecordingApp:
    """Stand-in for FastMCP that records each tool's name and annotations."""

    def __init__(self):
        self.tools = {}

    def tool(self, *args, **kwargs):
        def decorator(fn):
            self.tools[kwargs.get("name") or fn.__name__] = kwargs.get("annotations")
            return fn

        return decorator


@pytest.fixture(scope="module")
def registered():
    app = RecordingApp()
    filt = _ToolFilter(app, set(), set())
    for module in MODULES:
        module.register_tools(filt)
    return app.tools


def test_all_tools_registered_with_annotations(registered):
    assert len(registered) > 100
    for name, ann in registered.items():
        assert ann is not None, name
        assert ann.title, name
        for hint in ("readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint"):
            assert getattr(ann, hint) is not None, (name, hint)


def test_every_tool_verb_has_a_rule(registered):
    unclassified = sorted(name for name in registered if classify(name) is None)
    assert unclassified == [], f"add these verbs/tools to annotations.py: {unclassified}"


@pytest.mark.parametrize("name,read_only,destructive,idempotent,open_world", [
    ("get_sleep_data", True, False, True, True),
    ("search_foods", True, False, True, True),
    ("download_workout", True, False, True, True),
    ("download_activity_file", False, False, True, True),
    ("create_run_workout", False, False, False, True),
    ("log_food", False, False, False, True),
    ("set_activity_name", False, True, True, True),
    ("delete_workout", False, True, True, True),
    ("unschedule_workout", False, True, True, True),
    ("set_fit_download_dir", False, False, True, False),
])
def test_classification(name, read_only, destructive, idempotent, open_world):
    ann = annotations_for(name)
    assert (ann.readOnlyHint, ann.destructiveHint, ann.idempotentHint, ann.openWorldHint) == (
        read_only, destructive, idempotent, open_world)


def test_unknown_verb_gets_cautious_annotations():
    ann = annotations_for("frobnicate_everything")
    assert ann.readOnlyHint is False and ann.destructiveHint is True


def test_titles():
    assert title_for("get_hrv_data") == "Get HRV data"
    assert title_for("get_vo2max_trend") == "Get VO2 max trend"
    assert title_for("download_course_gpx") == "Download course GPX"


def test_module_annotations_are_not_overridden():
    app = RecordingApp()
    filt = _ToolFilter(app, set(), set())
    own = annotations_for("delete_workout")

    def get_x():
        return None

    filt.tool(annotations=own)(get_x)
    assert app.tools["get_x"] is own
