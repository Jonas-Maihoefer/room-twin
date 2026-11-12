"""Bounds-driven fitting; source bounds and target extents share one coordinate unit."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


class TransformError(ValueError):
    pass


@dataclass(frozen=True)
class Fit:
    scale: tuple[float, float, float]
    translation: tuple[float, float, float]


def fit_bounds(source_min: Sequence[float], source_max: Sequence[float], target_dimensions: Sequence[float], *, preserve_proportions: bool = False) -> Fit:
    if len(source_min) != 3 or len(source_max) != 3 or len(target_dimensions) != 3:
        raise TransformError("bounds and dimensions must have three components")
    values = tuple(float(v) for v in (*source_min, *source_max, *target_dimensions))
    if not all(math.isfinite(v) for v in values):
        raise TransformError("bounds and dimensions must be finite")
    extent = tuple(float(source_max[i]) - float(source_min[i]) for i in range(3))
    target = tuple(float(v) for v in target_dimensions)
    if any(v <= 1e-9 for v in extent) or any(v <= 0 for v in target):
        raise TransformError("source and target dimensions must be positive and non-degenerate")
    ratios = tuple(target[i] / extent[i] for i in range(3))
    if preserve_proportions:
        uniform = min(ratios)
        scale = (uniform, uniform, uniform)
    else:
        scale = ratios
    center = tuple((float(source_min[i]) + float(source_max[i])) / 2 for i in range(3))
    return Fit(scale, tuple(-center[i] * scale[i] for i in range(3)))
