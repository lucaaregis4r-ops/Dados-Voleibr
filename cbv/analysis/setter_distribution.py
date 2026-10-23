"""Probabilistic setter distribution engine and attack prediction under varying pass qualities and rotations."""

import math
from typing import Optional, Dict, Any, List, Tuple
from functools import lru_cache
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from cbv.config import logger
from cbv.database.repository import default_repo
from cbv.analysis.tactics import get_team_tactical_dossier

console = Console()


@lru_cache(maxsize=512)
def infer_team_tactical_roles(team_query: str, season: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Identifies functional volleyball roles (Setter, Opposite, Outside Hitters,
    Middle Blockers, Libero) from empirical match data.
    Prioritizes active season roster when available.
    """
    dossier = get_team_tactical_dossier(team_query, season=season)
    if not dossier:
        return None

    actual_team = dossier["team"]
    target_season = dossier.get("record", {}).get("target_season")
    curr_games = dossier.get("record", {}).get("current_season_games", 0)

    with default_repo.get_connection() as conn:
        if curr_games > 0 and target_season:
            df = conn.execute(
                """
                SELECT p.player_name, p.is_libero,
                       COALESCE(SUM(p.attack_attempts), 0) as att,
                       COALESCE(SUM(p.attack_points), 0) as pts,
                       COALESCE(SUM(p.reception_attempts), 0) as rec,
                       COALESCE(SUM(p.block_points), 0) as blk,
                       COALESCE(SUM(p.serve_attempts), 0) as srv,
                       COALESCE(AVG(p.rating), 6.0) as avg_rating
                FROM player_match_stats p
                JOIN matches m ON p.match_id = m.match_id
                WHERE p.team = ? AND m.season = ?
                GROUP BY p.player_name, p.is_libero
                ORDER BY att DESC, rec DESC
                """,
                [actual_team, target_season],
            ).fetchdf()
        else:
            df = conn.execute(
                """
                SELECT p.player_name, p.is_libero,
                       COALESCE(SUM(p.attack_attempts), 0) as att,
                       COALESCE(SUM(p.attack_points), 0) as pts,
                       COALESCE(SUM(p.reception_attempts), 0) as rec,
                       COALESCE(SUM(p.block_points), 0) as blk,
                       COALESCE(SUM(p.serve_attempts), 0) as srv,
                       COALESCE(AVG(p.rating), 6.0) as avg_rating
                FROM player_match_stats p
                WHERE p.team = ?
                GROUP BY p.player_name, p.is_libero
                ORDER BY att DESC, rec DESC
                """,
                [actual_team],
            ).fetchdf()

    if df.empty:
        return None

    # Calculate kill %
    df["kill_pct"] = df.apply(
        lambda r: round((r["pts"] / r["att"] * 100.0), 1) if r["att"] > 0 else 0.0,
        axis=1,
    )

    total_team_attacks = max(1, int(df["att"].sum()))

    players = df.to_dict(orient="records")

    # 1. Identify Libero
    libero = None
    for p in players:
        if p["is_libero"] or (p["rec"] >= 15 and p["att"] == 0 and p["srv"] == 0):
            libero = p
            break

    # 2. Identify Setter (high serve, very low attack, low reception)
    setter = None
    candidates_setter = [
        p for p in players
        if p != libero and p["srv"] >= 15 and p["att"] <= 10 and p["rec"] <= 10
    ]
    if candidates_setter:
        setter = max(candidates_setter, key=lambda x: x["srv"])
    else:
        # Fallback to lowest attack attempts among regular servers
        regular_players = [p for p in players if p != libero and p["srv"] >= 5]
        if regular_players:
            setter = min(regular_players, key=lambda x: x["att"])

    # 3. Identify Hitters
    hitters = [p for p in players if p != libero and p != setter and p["att"] > 0]
    if not hitters:
        hitters = [p for p in players if p != libero and p != setter]

    # Outside Hitters (OH): Passers with significant reception volume
    oh_candidates = sorted(
        [p for p in hitters if p["rec"] >= 15],
        key=lambda x: x["att"],
        reverse=True,
    )

    # Middle Blockers (MB): High block to attack ratio, almost no reception
    mb_candidates = sorted(
        [p for p in hitters if p not in oh_candidates and p["blk"] >= 2 and p["rec"] <= 12],
        key=lambda x: (x["blk"], x["att"]),
        reverse=True,
    )

    # Opposite (OPP): High offensive load, low reception
    opp_candidates = sorted(
        [p for p in hitters if p not in oh_candidates and p not in mb_candidates],
        key=lambda x: x["att"],
        reverse=True,
    )

    # Balance allocations if candidates overlap or are missing
    unallocated = [p for p in hitters if p not in oh_candidates and p not in mb_candidates and p not in opp_candidates]

    oh1 = oh_candidates[0] if len(oh_candidates) > 0 else (unallocated.pop(0) if unallocated else None)
    oh2 = oh_candidates[1] if len(oh_candidates) > 1 else (unallocated.pop(0) if unallocated else None)

    opp = opp_candidates[0] if len(opp_candidates) > 0 else None
    if not opp and unallocated:
        opp = unallocated.pop(0)
    elif not opp and len(oh_candidates) > 2:
        opp = oh_candidates[2]

    mb1 = mb_candidates[0] if len(mb_candidates) > 0 else (unallocated.pop(0) if unallocated else None)
    mb2 = mb_candidates[1] if len(mb_candidates) > 1 else (unallocated.pop(0) if unallocated else None)

    # Final fallbacks to ensure all 5 main hitter spots are represented
    assigned_names = {x["player_name"] for x in [setter, libero, oh1, oh2, opp, mb1, mb2] if x}
    remaining_pool = [p for p in players if p["player_name"] not in assigned_names]

    if not oh1 and remaining_pool:
        oh1 = remaining_pool.pop(0)
    if not oh2 and remaining_pool:
        oh2 = remaining_pool.pop(0)
    if not opp and remaining_pool:
        opp = remaining_pool.pop(0)
    if not mb1 and remaining_pool:
        mb1 = remaining_pool.pop(0)
    if not mb2 and remaining_pool:
        mb2 = remaining_pool.pop(0)

    roles_dict = {
        "team": actual_team,
        "total_team_attacks": total_team_attacks,
        "setter": setter,
        "libero": libero,
        "oh1": oh1,
        "oh2": oh2,
        "opposite": opp,
        "mb1": mb1,
        "mb2": mb2,
    }

    return roles_dict


def get_5x1_rotation_lineup(roles: Dict[str, Any], rotation_code: str) -> Dict[str, Any]:
    """
    Computes front-row and back-row hitter positions for a 5x1 rotation (P1 to P6).
    """
    rot = rotation_code.upper().strip()
    if not rot.startswith("P"):
        rot = f"P{rot}"

    oh1 = roles.get("oh1")
    oh2 = roles.get("oh2")
    opp = roles.get("opposite")
    mb1 = roles.get("mb1")
    mb2 = roles.get("mb2")
    setter = roles.get("setter")

    # In 5x1 system:
    # Front row: Zones 4, 3, 2
    # Back row: Zones 1, 6, 5
    if rot == "P1":
        # Setter at zone 1 (back row). 3 front row hitters.
        front_row = [
            {"player": oh1, "role": "Ponteira 1 (OH1)", "zone": "Z4 (Entrada / Ponta)"},
            {"player": mb1, "role": "Central 1 (MB1)", "zone": "Z3 (Meio de Rede)"},
            {"player": opp, "role": "Oposta (OPP)", "zone": "Z2 (Saída de Rede)"},
        ]
        back_row = [
            {"player": oh2, "role": "Ponteira 2 (OH2)", "zone": "Z6 (Fundo / Pipe)"},
            {"player": setter, "role": "Levantadora (S)", "zone": "Z1 (Fundo / Saque)"},
        ]
    elif rot == "P2":
        # Setter at zone 2 (front row). 2 front row hitters. OPP at back row zone 1.
        front_row = [
            {"player": oh1, "role": "Ponteira 1 (OH1)", "zone": "Z4 (Entrada / Ponta)"},
            {"player": mb1, "role": "Central 1 (MB1)", "zone": "Z3 (Meio de Rede)"},
        ]
        back_row = [
            {"player": opp, "role": "Oposta (OPP)", "zone": "Z1 (Fundo de Saída)"},
            {"player": oh2, "role": "Ponteira 2 (OH2)", "zone": "Z6 (Fundo / Pipe)"},
        ]
    elif rot == "P3":
        # Setter at zone 3 (front row). 2 front row hitters.
        front_row = [
            {"player": oh2, "role": "Ponteira 2 (OH2)", "zone": "Z4 (Entrada / Ponta)"},
            {"player": mb2, "role": "Central 2 (MB2)", "zone": "Z2 (Meio / Saída)"},
        ]
        back_row = [
            {"player": opp, "role": "Oposta (OPP)", "zone": "Z6/Z1 (Ataque do Fundo)"},
            {"player": oh1, "role": "Ponteira 1 (OH1)", "zone": "Z5 (Fundo)"},
        ]
    elif rot == "P4":
        # Setter at zone 4 (front row). 2 front row hitters.
        front_row = [
            {"player": mb2, "role": "Central 2 (MB2)", "zone": "Z3 (Meio de Rede)"},
            {"player": oh2, "role": "Ponteira 2 (OH2)", "zone": "Z2 (Saída / Ponta)"},
        ]
        back_row = [
            {"player": opp, "role": "Oposta (OPP)", "zone": "Z1 (Fundo de Saída)"},
            {"player": oh1, "role": "Ponteira 1 (OH1)", "zone": "Z6 (Fundo / Pipe)"},
        ]
    elif rot == "P5":
        # Setter at zone 5 (back row). 3 front row hitters.
        front_row = [
            {"player": opp, "role": "Oposta (OPP)", "zone": "Z4 (Entrada de Rede)"},
            {"player": mb2, "role": "Central 2 (MB2)", "zone": "Z3 (Meio de Rede)"},
            {"player": oh2, "role": "Ponteira 2 (OH2)", "zone": "Z2 (Saída de Rede)"},
        ]
        back_row = [
            {"player": oh1, "role": "Ponteira 1 (OH1)", "zone": "Z6 (Fundo / Pipe)"},
        ]
    else:  # P6
        # Setter at zone 6 (back row). 3 front row hitters.
        front_row = [
            {"player": oh2, "role": "Ponteira 2 (OH2)", "zone": "Z4 (Entrada / Ponta)"},
            {"player": mb1, "role": "Central 1 (MB1)", "zone": "Z3 (Meio de Rede)"},
            {"player": opp, "role": "Oposta (OPP)", "zone": "Z2 (Saída de Rede)"},
        ]
        back_row = [
            {"player": oh1, "role": "Ponteira 1 (OH1)", "zone": "Z5/Z6 (Fundo / Pipe)"},
        ]

    # Filter out None players
    front_row = [f for f in front_row if f["player"]]
    back_row = [b for b in back_row if b["player"] and b["player"] != setter]

    return {
        "rotation": rot,
        "setter_zone": "Rede" if rot in ("P2", "P3", "P4") else "Fundo",
        "front_row": front_row,
        "back_row": back_row,
    }


def compute_setter_distribution(
    team_query: str,
    rotation: str = "P1",
    pass_quality: str = "positive",
    roles: Optional[Dict[str, Any]] = None,
    dossier: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Computes data-driven conditional probabilities of athlete sets given
    setter rotation and pass quality, along with statistical precision metrics.
    """
    if roles is None:
        console.print("MODELO: Modelo heurístico de disponibilidade ofensiva. Não corresponde à frequência real de levantamentos observados.")
        roles = infer_team_tactical_roles(team_query)
    if not roles:
        return None

    team = roles["team"]
    total_attacks = roles["total_team_attacks"]

    # Normalize rotation
    rot = rotation.upper().strip()
    if rot not in ("P1", "P2", "P3", "P4", "P5", "P6"):
        rot = "P1"

    # Normalize pass quality
    pass_q = pass_quality.lower().strip()
    if pass_q not in ("positive", "negative", "transition"):
        if "neg" in pass_q or "quebr" in pass_q or "c" in pass_q:
            pass_q = "negative"
        elif "trans" in pass_q or "k2" in pass_q or "def" in pass_q:
            pass_q = "transition"
        else:
            pass_q = "positive"

    # Get tactical dossier to fetch team phase attack stats
    if dossier is None:
        dossier = get_team_tactical_dossier(team)
    tot = dossier["totals"] if dossier else {}

    pos_att_pct = tot.get("pos_rec_att_points_pct") or 48.0
    neg_att_pct = tot.get("neg_rec_att_points_pct") or 36.0
    trans_att_pct = tot.get("trans_att_points_pct") or 40.0

    layout = get_5x1_rotation_lineup(roles, rot)
    front_players = layout["front_row"]
    back_players = layout["back_row"]

    # Compute raw weights based on base attack share and pass condition
    weighted_candidates = []

    for entry in front_players:
        p = entry["player"]
        role_label = entry["role"]
        zone_label = entry["zone"]

        base_share = (p["att"] / total_attacks) if total_attacks > 0 else 0.2

        # Pass condition multiplier for Front Row
        if "Central" in role_label:
            if pass_q == "positive":
                multiplier = 2.30  # Middle attack is primed with good pass
            elif pass_q == "negative":
                multiplier = 0.05  # Middle cannot attack on out-of-system pass
            else:  # transition
                multiplier = 0.45
        elif "Ponteira" in role_label:
            if pass_q == "positive":
                multiplier = 1.05
            elif pass_q == "negative":
                multiplier = 2.10 if "OH1" in role_label else 1.45  # Go-to high ball to wing
            else:
                multiplier = 1.35
        elif "Oposta" in role_label:
            if pass_q == "positive":
                multiplier = 1.20
            elif pass_q == "negative":
                multiplier = 1.85  # High ball to opposite
            else:
                multiplier = 1.65
        else:
            multiplier = 1.0

        weight = base_share * multiplier
        weighted_candidates.append({
            "player_name": p["player_name"],
            "role": role_label,
            "zone": zone_label,
            "is_front": True,
            "base_kill_pct": p["kill_pct"],
            "weight": weight,
            "player_raw": p,
        })

    for entry in back_players:
        p = entry["player"]
        role_label = entry["role"]
        zone_label = entry["zone"]

        base_share = (p["att"] / total_attacks) if total_attacks > 0 else 0.1

        # Back row multipliers
        if "Oposta" in role_label:
            # Back row attack (Zone 1)
            if pass_q == "positive":
                multiplier = 0.65
            elif pass_q == "negative":
                multiplier = 0.85
            else:
                multiplier = 0.80
        elif "Ponteira" in role_label:
            # Pipe attack (Zone 6)
            if pass_q == "positive":
                multiplier = 0.40  # Pipe is fast with good pass
            elif pass_q == "negative":
                multiplier = 0.10  # Very rare to set high ball pipe
            else:
                multiplier = 0.35
        else:
            multiplier = 0.0

        weight = base_share * multiplier
        if weight > 0:
            weighted_candidates.append({
                "player_name": p["player_name"],
                "role": role_label,
                "zone": zone_label,
                "is_front": False,
                "base_kill_pct": p["kill_pct"],
                "weight": weight,
                "player_raw": p,
            })

    total_weight = sum(c["weight"] for c in weighted_candidates)
    if total_weight <= 0:
        total_weight = 1.0

    # Phase efficiency modifier for expected kill rate
    if pass_q == "positive":
        phase_eff_mod = pos_att_pct / 45.0
        pass_name_pt = "Passe A / Positivo (+#) — Bola na Mão"
    elif pass_q == "negative":
        phase_eff_mod = neg_att_pct / 45.0
        pass_name_pt = "Passe C / Negativo (-!) — Passe Quebrado"
    else:
        phase_eff_mod = trans_att_pct / 45.0
        pass_name_pt = "Transição / Contra-Ataque (K2) — Defesa"

    # Effective sample size: attacks observed for this team
    n_eff = max(30, total_attacks)

    probabilities = []
    shannon_entropy = 0.0

    for c in weighted_candidates:
        prob = c["weight"] / total_weight
        prob_pct = round(prob * 100.0, 1)

        # Standard error and 95% Confidence Interval
        se = math.sqrt((prob * (1.0 - prob)) / n_eff)
        margin = round(1.96 * se * 100.0, 1)
        ci_low = round(max(0.0, prob_pct - margin), 1)
        ci_high = round(min(100.0, prob_pct + margin), 1)

        # Expected Kill Rate
        exp_kill = round(min(95.0, c["base_kill_pct"] * phase_eff_mod), 1)

        if prob > 0.001:
            shannon_entropy -= prob * math.log2(prob)

        probabilities.append({
            "player_name": c["player_name"],
            "role": c["role"],
            "zone": c["zone"],
            "is_front": c["is_front"],
            "probability_pct": prob_pct,
            "margin_error_pct": None,
            "ci_95": None,
            "expected_kill_pct": exp_kill,
            "historical_attacks": c["player_raw"]["att"],
        })

    # Sort candidates by probability descending
    probabilities.sort(key=lambda x: x["probability_pct"], reverse=True)

    # Setter Predictability Index
    num_options = max(1, len(probabilities))
    max_entropy = math.log2(num_options) if num_options > 1 else 1.0
    predictability_pct = round((1.0 - (shannon_entropy / max_entropy)) * 100.0, 1) if max_entropy > 0 else 100.0
    predictability_pct = max(0.0, min(100.0, predictability_pct))

    if predictability_pct >= 65.0:
        pred_label = "Extremamente Alta (Levantadora previsível / bola cantada)"
        pred_style = "bold red"
    elif predictability_pct >= 45.0:
        pred_label = "Moderada (Tendência clara nas principais opções)"
        pred_style = "bold yellow"
    else:
        pred_label = "Baixa (Distribuição variada e equilibrada)"
        pred_style = "bold green"

    # Tactical Gameplan for CT
    top_target = probabilities[0] if probabilities else None
    ct_advice = []
    if top_target:
        if pass_q == "negative":
            ct_advice.append(
                f"MARCAÇÃO DE BLOQUEIO: Em passe quebrado (-!), fechar bloqueio pesado duplo/triplo "
                f"em {top_target['player_name']} ({top_target['zone']}), que concentra {top_target['probability_pct']}% "
                f"das solicitações. A central adversária está praticamente descartada."
            )
        elif pass_q == "positive":
            ct_advice.append(
                f"LEITURA DE PRIMEIRO TEMPO: Com passe na mão (+#), o meio adversário tem opção ativa. "
                f"O bloqueador central deve manter a base e pular com o atacante de meio antes de abrir para a ponta."
            )
        else:
            ct_advice.append(
                f"COBERTURA DE TRANSIÇÃO: Na defesa/contra-ataque, orientar bloqueio para conter "
                f"{top_target['player_name']} ({top_target['probability_pct']}% de probabilidade de acionamento)."
            )

    return {
        "metric_class": "EXPERIMENTAL",
        "model_name": "Distribuição estimada — experimental",
        "model_version": "setter-heuristic-legacy-v1",
        "source_type": "AGGREGATED_ATTACK_VOLUME_AND_HEURISTICS",
        "sample_size": total_attacks,
        "limitation": "Não corresponde à frequência real de levantamentos observados.",
        "team": team,
        "rotation": rot,
        "pass_quality": pass_q,
        "pass_quality_name": pass_name_pt,
        "setter_name": roles["setter"]["player_name"] if roles["setter"] else "Desconhecida",
        "sample_size_attacks": total_attacks,
        "predictability_pct": predictability_pct,
        "predictability_label": "Concentração dos pesos heurísticos; não mede previsibilidade observada",
        "predictability_style": pred_style,
        "shannon_entropy": round(shannon_entropy, 3),
        "shannon_entropy_norm": round(shannon_entropy / max_entropy, 3) if max_entropy > 0 else 0.0,
        "max_entropy": round(max_entropy, 3),
        "literature_reference": None,
        "distribution": probabilities,
        "ct_advice": ["Hipótese experimental: não usar como distribuição observada ou recomendação validada."],
    }


def display_setter_distribution(
    team_query: str,
    rotation: Optional[str] = None,
    pass_quality: Optional[str] = None,
) -> None:
    """
    Renders formatted tactical intelligence on setter distribution,
    attack probabilities by pass type and rotation, and precision margins for CT.
    """
    rot_list = [rotation.upper()] if rotation else ["P1", "P2", "P3", "P4", "P5", "P6"]
    pass_list = [pass_quality.lower()] if pass_quality else ["positive", "negative", "transition"]

    console.print("MODELO: Modelo heurístico de disponibilidade ofensiva. Não corresponde à frequência real de levantamentos observados.")
    roles = infer_team_tactical_roles(team_query)
    if not roles:
        console.print(f"[red]Equipe '{team_query}' não encontrada no banco de dados.[/red]")
        return

    team = roles["team"]
    setter_name = roles["setter"]["player_name"] if roles["setter"] else "Titular"

    console.print(Panel(
        f"[bold yellow]ANÁLISE DE DISTRIBUIÇÃO DA LEVANTADORA — {team}[/bold yellow]\n"
        f"[dim]Levantadora: {setter_name} | Amostra auditada: {roles['total_team_attacks']} ataques da equipe[/dim]",
        expand=False,
    ))

    for rot in rot_list:
        for p_qual in pass_list:
            res = compute_setter_distribution(team, rotation=rot, pass_quality=p_qual)
            if not res:
                continue

            console.print(f"\n[bold cyan]► Rotação {res['rotation']} | {res['pass_quality_name']}[/bold cyan]")
            console.print(
                f"[dim]Índice de Previsibilidade da Levantadora: "
                f"[{res['predictability_style']}]{res['predictability_pct']}% — {res['predictability_label']}[/{res['predictability_style']}][/dim]"
            )

            tbl = Table(show_header=True, header_style="bold magenta")
            tbl.add_column("Atacante")
            tbl.add_column("Função Tática")
            tbl.add_column("Posicionamento")
            tbl.add_column("Prob. Acionamento", justify="center")
            tbl.add_column("Margem de Erro (IC 95%)", justify="center")
            tbl.add_column("Kill Rate Estimado", justify="center")

            for item in res["distribution"]:
                prob_str = f"[bold]{item['probability_pct']}%[/bold]"
                if item["probability_pct"] >= 45.0:
                    prob_str = f"[bold red]{item['probability_pct']}%[/bold red]"
                elif item["probability_pct"] >= 25.0:
                    prob_str = f"[bold green]{item['probability_pct']}%[/bold green]"

                ci_str = "Indisponível: pesos heurísticos não fornecem IC"
                kill_str = f"{item['expected_kill_pct']}%"

                tbl.add_row(
                    item["player_name"],
                    item["role"],
                    item["zone"],
                    prob_str,
                    f"[dim]{ci_str}[/dim]",
                    kill_str,
                )

            console.print(tbl)

            for adv in res["ct_advice"]:
                console.print(f"[yellow]💡 Diretriz CT:[/yellow] {adv}")
    console.print()
