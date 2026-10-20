"""Derived metrics calculation and volleyball analytical formulas."""

from typing import Optional


def calc_attack_success_pct(points: Optional[int], attempts: Optional[int]) -> Optional[float]:
    """Calculates attack success rate (percentage): points / attempts * 100."""
    if not attempts or attempts <= 0 or points is None:
        return None
    return round((points / attempts) * 100, 2)


def calc_attack_efficiency(
    points: Optional[int],
    errors: Optional[int],
    blocked: Optional[int],
    attempts: Optional[int],
) -> Optional[float]:
    """
    Calculates offensive efficiency: (points - errors - blocked) / attempts * 100.
    Returns None if attempts is 0 or None.
    """
    if not attempts or attempts <= 0:
        return None
    pts = points or 0
    errs = errors or 0
    blo = blocked or 0
    return round(((pts - errs - blo) / attempts) * 100, 2)


def calc_ace_rate(aces: Optional[int], attempts: Optional[int]) -> Optional[float]:
    """Calculates ace rate: aces / attempts * 100."""
    if not attempts or attempts <= 0 or aces is None:
        return None
    return round((aces / attempts) * 100, 2)


def calc_serve_error_rate(errors: Optional[int], attempts: Optional[int]) -> Optional[float]:
    """Calculates serve error rate: errors / attempts * 100."""
    if not attempts or attempts <= 0 or errors is None:
        return None
    return round((errors / attempts) * 100, 2)


def calc_ace_error_ratio(aces: Optional[int], errors: Optional[int]) -> Optional[float]:
    """Calculates ace / error ratio. Returns None if errors is None or 0."""
    if aces is None or errors is None:
        return None
    if errors <= 0:
        return float(aces) if aces > 0 else 0.0
    return round(aces / errors, 2)


def calc_per_set(total: Optional[int], sets: Optional[int]) -> Optional[float]:
    """Calculates metric per set played."""
    if not sets or sets <= 0 or total is None:
        return None
    return round(total / sets, 2)
