import pytest

from tactin.workspace import Bench, Part, Slot


def make_bench() -> Bench:
    bench = Bench()
    bench.add_part(Part("led1", "led", x=130, y=-90, label="red 5mm"))
    bench.add_part(Part("r1", "resistor", x=170, y=-90, label="330Ω"))
    bench.add_slot(Slot("bb1", x=180, y=0, z=6))
    return bench


def test_find_by_kind_and_label():
    bench = make_bench()
    assert [p.id for p in bench.find(kind="resistor")] == ["r1"]
    assert [p.id for p in bench.find(label="330")] == ["r1"]
    assert bench.find(kind="capacitor") == []


def test_pick_then_place_updates_state():
    bench = make_bench()
    bench.mark_picked("led1")
    assert bench.held_part().id == "led1"
    assert "led1" not in [p.id for p in bench.available_parts()]
    bench.mark_placed(180, 0, 6, slot="bb1")
    assert bench.get_part("led1").placed
    assert bench.get_slot("bb1").occupied_by == "led1"
    assert bench.held_part() is None


def test_cannot_hold_two_parts():
    bench = make_bench()
    bench.mark_picked("led1")
    with pytest.raises(RuntimeError):
        bench.mark_picked("r1")


def test_place_with_nothing_held_raises():
    bench = make_bench()
    with pytest.raises(RuntimeError):
        bench.mark_placed(180, 0, 6)


def test_unknown_part_raises():
    bench = make_bench()
    with pytest.raises(KeyError):
        bench.get_part("nope")
