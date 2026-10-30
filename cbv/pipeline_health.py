"""Formal synchronization health monitoring and reporting.

Categorizes sources as CRITICAL vs OPTIONAL, enforces failure policies,
tracks timestamps for staleness detection, and generates audit reports.
"""

from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
import json
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Sao_Paulo")

# Source classifications
SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_OPTIONAL = "OPTIONAL"

STATUS_HEALTHY = "HEALTHY"
STATUS_DEGRADED = "DEGRADED"
STATUS_FAILED = "FAILED"
STATUS_STALE = "STALE"

SOURCE_SPECS = {
    "calendar": {"severity": SEVERITY_OPTIONAL, "description": "CBV public match schedule"},
    "superliga_m": {"severity": SEVERITY_CRITICAL, "description": "Superliga Masculina finished matches"},
    "superliga_f": {"severity": SEVERITY_CRITICAL, "description": "Superliga Feminina finished matches"},
    "cbs_m": {"severity": SEVERITY_OPTIONAL, "description": "CBS Masculino tournament matches"},
    "cbs_f": {"severity": SEVERITY_OPTIONAL, "description": "CBS Feminino tournament matches"},
    "scoresheets": {"severity": SEVERITY_OPTIONAL, "description": "Official match scoresheets"},
    "match_reports": {"severity": SEVERITY_CRITICAL, "description": "Official technical match reports"},
    "libero_reports": {"severity": SEVERITY_OPTIONAL, "description": "Libero control sheets"},
    "play_by_play": {"severity": SEVERITY_OPTIONAL, "description": "Play-by-play live sequence"},
}


class SyncHealthTracker:
    def __init__(self, exports_dir: Optional[Path] = None):
        self.started_at = datetime.now(TZ)
        self.finished_at: Optional[datetime] = None
        self.exports_dir = Path(exports_dir) if exports_dir else None
        self.sources: Dict[str, Dict[str, Any]] = {}
        self.prior_health = self._load_prior_health()
        
        # Initialize sources with defaults
        for key, spec in SOURCE_SPECS.items():
            self.sources[key] = {
                "status": "PENDING",
                "severity": spec["severity"],
                "description": spec["description"],
                "attempted": 0,
                "successful": 0,
                "failed": 0,
                "latest_source_date": None,
                "message": "Aguardando execução",
            }

    def _load_prior_health(self) -> Optional[Dict[str, Any]]:
        if not self.exports_dir:
            return None
        health_file = self.exports_dir / "sync_health.json"
        if health_file.exists():
            try:
                return json.loads(health_file.read_text(encoding="utf-8"))
            except Exception:
                return None
        return None

    def record_source(
        self,
        key: str,
        attempted: int = 1,
        successful: int = 1,
        failed: int = 0,
        latest_date: Optional[str] = None,
        message: str = "",
        error: Optional[Exception] = None,
    ):
        if key not in self.sources:
            severity = SEVERITY_OPTIONAL
            desc = key
        else:
            severity = self.sources[key]["severity"]
            desc = self.sources[key]["description"]

        if error is not None:
            failed = attempted if failed == 0 else failed
            successful = 0
            msg = f"Erro: {str(error)}" if not message else f"{message} ({error})"
            status = STATUS_FAILED
        elif failed > 0 and successful > 0:
            status = STATUS_DEGRADED
            msg = message or f"{successful}/{attempted} bem-sucedidos"
        elif failed > 0:
            status = STATUS_FAILED
            msg = message or "Todas as tentativas falharam"
        else:
            status = STATUS_HEALTHY
            msg = message or "Coletado com sucesso"

        self.sources[key] = {
            "status": status,
            "severity": severity,
            "description": desc,
            "attempted": attempted,
            "successful": successful,
            "failed": failed,
            "latest_source_date": latest_date,
            "message": msg,
        }

    def query_validation_metrics(self, conn) -> Dict[str, int]:
        tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
        metrics = {
            "valid_matches": 0,
            "valid_with_warnings": 0,
            "failed": 0,
            "rallies": 0,
            "high_confidence_rotations": 0,
            "high_confidence_lineups": 0,
        }
        if "matches" in tables:
            rows = conn.execute(
                "SELECT validation_status, count(*) FROM matches GROUP BY validation_status"
            ).fetchall()
            status_map = dict(rows)
            metrics["valid_matches"] = status_map.get("VALID", 0)
            metrics["valid_with_warnings"] = status_map.get("WARNING", 0) + status_map.get("VALID_WITH_WARNINGS", 0)
            metrics["failed"] = status_map.get("INVALID", 0) + status_map.get("FAILED", 0)

        if "rallies" in tables:
            metrics["rallies"] = conn.execute("SELECT count(*) FROM rallies").fetchone()[0]
            metrics["high_confidence_rotations"] = conn.execute(
                "SELECT count(*) FROM rallies WHERE home_rotation IS NOT NULL AND away_rotation IS NOT NULL"
            ).fetchone()[0]

        if "lineups" in tables:
            metrics["high_confidence_lineups"] = conn.execute(
                "SELECT count(*) FROM lineups WHERE confidence = 'RECONSTRUCTED_HIGH'"
            ).fetchone()[0]

        return metrics

    def finalize(
        self,
        conn,
        initial_match_count: int,
        quality_gate_passed: bool = True,
        new_matches: int = 0,
        updated_matches: int = 0,
    ) -> Dict[str, Any]:
        self.finished_at = datetime.now(TZ)
        db_match_count = conn.execute("SELECT count(*) FROM matches").fetchone()[0] if conn else initial_match_count
        validation = self.query_validation_metrics(conn) if conn else {}

        # Evaluate status
        has_critical_failure = False
        has_optional_failure = False

        for k, src in self.sources.items():
            if src["status"] == STATUS_FAILED:
                if src["severity"] == SEVERITY_CRITICAL:
                    has_critical_failure = True
                else:
                    has_optional_failure = True
            elif src["status"] == STATUS_DEGRADED:
                has_optional_failure = True

        if not quality_gate_passed or has_critical_failure:
            overall_status = STATUS_FAILED
        elif has_optional_failure:
            overall_status = STATUS_DEGRADED
        else:
            overall_status = STATUS_HEALTHY

        # Staleness check (36 hours)
        last_full_success = None
        if self.prior_health and self.prior_health.get("last_full_success"):
            last_full_success = self.prior_health["last_full_success"]

        if overall_status == STATUS_HEALTHY:
            last_full_success = self.finished_at.isoformat()
        elif last_full_success:
            try:
                prior_dt = datetime.fromisoformat(last_full_success)
                if (self.finished_at - prior_dt) > timedelta(hours=36):
                    overall_status = STATUS_STALE
            except Exception:
                pass
        else:
            # No record of prior success and not healthy today
            overall_status = STATUS_STALE

        report = {
            "status": overall_status,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "last_full_success": last_full_success,
            "database_match_count": db_match_count,
            "new_matches": new_matches,
            "updated_matches": updated_matches,
            "sources": self.sources,
            "validation": validation,
        }
        return report

    def save_report(self, report: Dict[str, Any], target_dir: Path) -> Path:
        target_dir = Path(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / "sync_health.json"
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    @staticmethod
    def generate_github_summary(report: Dict[str, Any], initial_count: int) -> str:
        status = report.get("status", "UNKNOWN")
        db_count = report.get("database_match_count", 0)
        new_m = report.get("new_matches", 0)
        val = report.get("validation", {})
        valid = val.get("valid_matches", 0)
        warnings = val.get("valid_with_warnings", 0)
        failed = val.get("failed", 0)

        # Find latest source date across sources
        dates = [
            s.get("latest_source_date")
            for s in report.get("sources", {}).values()
            if s.get("latest_source_date")
        ]
        latest_date = max(dates) if dates else "não informada"

        icon = "🟢" if status == STATUS_HEALTHY else ("🟡" if status == STATUS_DEGRADED else "🔴")

        md = [
            f"### {icon} ATLAS SYNC",
            "",
            f"- **Status**: `{status}`",
            f"- **Partidas antes**: {initial_count}",
            f"- **Partidas depois**: {db_count}",
            f"- **Novas**: {new_m}",
            f"- **Validadas**: {valid}",
            f"- **Warnings**: {warnings}",
            f"- **Failed**: {failed}",
            f"- **Última fonte**: {latest_date}",
            f"- **Finalizado em**: {report.get('finished_at', '')}",
            "",
            "#### Fontes:",
            "| Fonte | Severidade | Status | Tentativas | Sucessos | Detalhe |",
            "|---|---|---|---|---|---|",
        ]
        for name, src in report.get("sources", {}).items():
            s_icon = "✓" if src["status"] == STATUS_HEALTHY else ("⚠" if src["status"] == STATUS_DEGRADED else "✗")
            md.append(
                f"| `{name}` | {src['severity']} | {s_icon} {src['status']} | {src['attempted']} | {src['successful']} | {src['message']} |"
            )
        return "\n".join(md)
