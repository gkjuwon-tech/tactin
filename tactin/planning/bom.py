"""Bill-of-materials model and loader.

A BOM is the hardware equivalent of a dependency manifest: it is the input
the engineer hands the bench ("here are the parts, go build"). We parse the
same YAML shape that KiCad-style exports and hand-written part lists use.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Part:
    ref: str  # designator, e.g. "R1"
    label: str  # detector class, e.g. "resistor_330"
    value: str = ""  # "330R", "10uF", ...
    package: str = ""  # "THT", "0805", "DIP-8"
    qty: int = 1
    mpn: str = ""  # manufacturer part number
    supplier: str = ""

    @property
    def is_smd(self) -> bool:
        pkg = self.package.lower()
        if not pkg:
            return False
        # Imperial chip sizes (0402, 0603, 0805, 1206, ...) start with a digit.
        if pkg[0].isdigit():
            return True
        smd_families = ("smd", "soic", "sot", "qfn", "qfp", "tssop", "bga", "sod", "dfn", "lga")
        return any(family in pkg for family in smd_families)


@dataclass
class BOM:
    name: str
    parts: list[Part] = field(default_factory=list)

    def total_qty(self) -> int:
        return sum(p.qty for p in self.parts)

    def labels(self) -> list[str]:
        return [p.label for p in self.parts]

    def smd_parts(self) -> list[Part]:
        return [p for p in self.parts if p.is_smd]


def load_bom(path: str | Path) -> BOM:
    data = yaml.safe_load(Path(path).read_text())
    parts = [
        Part(
            ref=str(p["ref"]),
            label=str(p["label"]),
            value=str(p.get("value", "")),
            package=str(p.get("package", "")),
            qty=int(p.get("qty", 1)),
            mpn=str(p.get("mpn", "")),
            supplier=str(p.get("supplier", "")),
        )
        for p in data.get("parts", [])
    ]
    return BOM(name=str(data.get("name", "untitled")), parts=parts)
