from pathlib import Path

from tactin.planning import AssemblyPlan, AssemblyStep, load_bom

BLINKY = Path(__file__).resolve().parents[1] / "bom" / "blinky.yaml"


def test_load_blinky_bom():
    bom = load_bom(BLINKY)
    assert bom.name == "esp32-blinky"
    assert bom.total_qty() == 5
    assert "led_red" in bom.labels()


def test_smd_classification():
    bom = load_bom(BLINKY)
    # the blinky example is all through-hole / modules
    assert bom.smd_parts() == []


def test_plan_validation_catches_double_pick():
    plan = AssemblyPlan(
        "bad",
        [AssemblyStep("pick", "led_red"), AssemblyStep("pick", "resistor_330")],
    )
    problems = plan.validate(["led_red", "resistor_330"])
    assert any("already holding" in p for p in problems)


def test_valid_plan_has_no_problems():
    plan = AssemblyPlan(
        "good",
        [AssemblyStep("pick", "led_red"), AssemblyStep("place", "led_red")],
    )
    assert plan.validate(["led_red"]) == []
