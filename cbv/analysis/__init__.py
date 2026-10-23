"""Analysis API; pure statistics must not open the production database."""
from importlib import import_module

_MODULES={
    **{name:'metrics' for name in ('calc_attack_success_pct','calc_attack_efficiency','calc_ace_rate','calc_serve_error_rate','calc_ace_error_ratio','calc_per_set')},
    **{name:'rankings' for name in ('get_aggregated_player_stats','get_scoring_ranking','get_attack_ranking','get_block_ranking','get_serve_ranking','display_rankings')},
    **{name:'tactics' for name in ('get_match_tactical_report','display_match_tactics')},
}

def __getattr__(name):
    if name not in _MODULES:raise AttributeError(name)
    value=getattr(import_module('cbv.analysis.'+_MODULES[name]),name)
    globals()[name]=value
    return value

__all__ = [
    "calc_attack_success_pct",
    "calc_attack_efficiency",
    "calc_ace_rate",
    "calc_serve_error_rate",
    "calc_ace_error_ratio",
    "calc_per_set",
    "get_aggregated_player_stats",
    "get_scoring_ranking",
    "get_attack_ranking",
    "get_block_ranking",
    "get_serve_ranking",
    "display_rankings",
    "get_match_tactical_report",
    "display_match_tactics",
]

