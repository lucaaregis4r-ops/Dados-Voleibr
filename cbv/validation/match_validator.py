"""Validation engine for CBV match reports and statistics."""

from typing import List, Dict, Any, Tuple
from cbv.models.stats import MatchData, TeamMatchStats
from cbv.models.player import PlayerMatchStats


class MatchValidator:
    """Validates structural and mathematical integrity of parsed match data."""

    @staticmethod
    def validate(data: MatchData) -> Tuple[str, List[str]]:
        """
        Validates match data and returns (status, list_of_warnings).
        Status is one of: 'VALID', 'WARNING', 'INVALID'.
        """
        warnings: List[str] = []
        errors: List[str] = []

        # 1. Structural Validation
        if not data.match.match_id:
            errors.append("match_id missing or invalid")

        if not data.match.home_team or not data.match.away_team:
            errors.append("home_team or away_team missing")

        if data.match.home_team == data.match.away_team:
            errors.append(f"home and away team names are identical ({data.match.home_team})")

        if len(data.players) == 0:
            errors.append("no players found in match report")

        home_players = [p for p in data.players if p.team == data.match.home_team]
        away_players = [p for p in data.players if p.team == data.match.away_team]

        if len(home_players) < 6:
            warnings.append(f"home team ({data.match.home_team}) has fewer than 6 players ({len(home_players)})")

        if len(away_players) < 6:
            warnings.append(f"away team ({data.match.away_team}) has fewer than 6 players ({len(away_players)})")

        if len(data.sets) == 0:
            warnings.append("no set scores recorded")

        # 2. Numerical Cross-Validation per team
        teams_map: Dict[str, TeamMatchStats] = {t.team: t for t in data.teams}

        for team_name in [data.match.home_team, data.match.away_team]:
            team_stats = teams_map.get(team_name)
            if not team_stats:
                warnings.append(f"team stats row missing for {team_name}")
                continue

            team_player_list = [p for p in data.players if p.team == team_name]

            # Sum of Attack Points
            player_attack_pts = sum(p.attack_points or 0 for p in team_player_list)
            if team_stats.attack_points is not None:
                if player_attack_pts != team_stats.attack_points:
                    warnings.append(
                        f"{team_name}: sum of player attack points ({player_attack_pts}) != team total ({team_stats.attack_points})"
                    )

            # Sum of Blocks
            player_blocks = sum(p.block_points or 0 for p in team_player_list)
            if team_stats.block_points is not None:
                if player_blocks != team_stats.block_points:
                    warnings.append(
                        f"{team_name}: sum of player block points ({player_blocks}) != team total ({team_stats.block_points})"
                    )

            # Sum of Aces (Serve Points)
            player_aces = sum(p.serve_points or 0 for p in team_player_list)
            if team_stats.serve_points is not None:
                if player_aces != team_stats.serve_points:
                    warnings.append(
                        f"{team_name}: sum of player aces ({player_aces}) != team total ({team_stats.serve_points})"
                    )

            # Sum of Total Points
            player_points = sum(p.points_total or 0 for p in team_player_list)
            if team_stats.points_total is not None:
                if player_points != team_stats.points_total:
                    warnings.append(
                        f"{team_name}: sum of player total points ({player_points}) != team total ({team_stats.points_total})"
                    )

            # Point Reconciliation: attack + blocks + aces + opponent_errors ≈ points_total
            if (
                team_stats.attack_points is not None
                and team_stats.block_points is not None
                and team_stats.serve_points is not None
                and team_stats.opponent_errors is not None
            ):
                reconstructed_points = (
                    team_stats.attack_points
                    + team_stats.block_points
                    + team_stats.serve_points
                    + team_stats.opponent_errors
                )
                # Check against sum of sets won by this team if sets exist
                if data.sets:
                    is_home = (team_name == data.match.home_team)
                    actual_set_points = sum(s.home_points if is_home else s.away_points for s in data.sets)
                    if reconstructed_points != actual_set_points:
                        warnings.append(
                            f"{team_name}: reconstructed points ({reconstructed_points}) != set points total ({actual_set_points})"
                        )

        # 3. Decision
        if errors:
            status = "INVALID"
            warnings.extend(errors)
        elif warnings:
            status = "WARNING"
        else:
            status = "VALID"

        return status, warnings
