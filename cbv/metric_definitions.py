"""Compatibility bindings; canonical definitions live in cbv.metrics.registry."""
from cbv.metrics.registry import legacy_bindings
VERSION='scouting-1.0'  # Baseline data semantics intentionally preserved.
METRICS=legacy_bindings()
