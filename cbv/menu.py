"""Interactive CLI menu for effortless daily CT operations."""

import sys
import subprocess
import webbrowser
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from cbv.config import BASE_DIR
from cbv.database.repository import default_repo
from cbv.scraper.sync import run_daily_sync
from cbv.analysis.predictions import display_match_prediction, display_model_evaluation
from cbv.analysis.setter_distribution import display_setter_distribution
from cbv.analysis.rankings import display_rankings
from cbv.export.html_dashboard import export_dashboard_html
from cbv.export.csv_export import export_all_to_csv
from cbv.export.json_export import export_all_to_json

console = Console()
EXPORTS_DIR = BASE_DIR / "exports"


def get_available_teams():
    """Fetches list of unique teams stored in DuckDB."""
    try:
        with default_repo.get_connection() as conn:
            teams = [r[0] for r in conn.execute("SELECT DISTINCT team FROM team_tactical_stats ORDER BY team").fetchall()]
            return teams
    except Exception:
        return []


def run_interactive_menu():
    """Runs the main interactive terminal menu."""
    while True:
        console.clear()
        console.print(Panel(
            "[bold green]🏐 CBV VOLLEY DATA — PAINEL DA COMISSÃO TÉCNICA (CT)[/bold green]\n"
            "[dim]Scouting Avançado, Sincronização Diária, Previsões e Distribuição Tática[/dim]\n"
            "[cyan]CBS Feminino / Masculino — Temporada Oficial 2026[/cyan]",
            border_style="green",
            expand=False,
        ))

        teams = get_available_teams()
        teams_count = len(teams)

        console.print(f"[dim]Base de dados atual: [bold]{teams_count} seleções[/bold] cadastradas.[/dim]\n")
        console.print("[bold yellow]Escolha uma funcionalidade:[/bold yellow]")
        console.print("  [bold cyan][1][/bold cyan] 🔄 Sincronizar Jogos por URL (Rotina Diária da CT + Boletim WhatsApp)")
        console.print("  [bold cyan][2][/bold cyan] 🌐 Abrir Dashboard Interativo Completo no Navegador")
        console.print("  [bold cyan][3][/bold cyan] 🔮 Prever Confronto / Vitória (Probabilidades, Margem de Erro e Scouting)")
        console.print("  [bold cyan][4][/bold cyan] 🏐 Analisar Distribuição da Levantadora (Acionamento por Rotação P1-P6 e Passe)")
        console.print("  [bold cyan][5][/bold cyan] 📊 Ver Classificação e Rankings Oficiais do Torneio")
        console.print("  [bold cyan][6][/bold cyan] 📋 Ver/Copiar Último Boletim para WhatsApp da CT")
        console.print("  [bold cyan][7][/bold cyan] 🎯 Avaliar Acurácia e Calibração do Modelo Preditivo")
        console.print("  [bold cyan][8][/bold cyan] 📥 Exportar Todos os Dados (CSV, JSON e HTML)")
        console.print("  [bold red][0][/bold red] 🚪 Sair\n")

        choice = Prompt.ask("Digite o número da opção", default="1")

        if choice == "0":
            console.print("\n[green]Encerrando CBV Volley Data. Bom trabalho com a Comissão Técnica![/green]\n")
            break

        elif choice == "1":
            console.print("\n[bold cyan]--- SINCRONIZAÇÃO DIÁRIA DA COMPETIÇÃO ---[/bold cyan]")
            console.print("[dim]Cole a URL da página do campeonato na CBV (ex: CBS Feminino no final de novembro).[/dim]")
            default_url = "https://cbv.com.br/volei-de-quadra/cbs/2026/feminino/sub-18-especial"
            url_input = Prompt.ask("URL da competição", default=default_url)

            open_dash = Confirm.ask("Abrir Dashboard atualizado no navegador após a sincronização?", default=True)

            try:
                run_daily_sync(url=url_input, open_browser=open_dash)
            except Exception as e:
                console.print(f"[red]Erro durante a sincronização:[/red] {e}")

            Prompt.ask("\nPressione [bold]ENTER[/bold] para voltar ao menu principal")

        elif choice == "2":
            console.print("\n[bold cyan]Gerando e abrindo Dashboard Interativo...[/bold cyan]")
            try:
                html_path = export_dashboard_html()
                webbrowser.open(html_path.resolve().as_uri())
                console.print(f"[green]✓ Dashboard aberto no seu navegador padrão: {html_path.resolve()}[/green]")
            except Exception as e:
                console.print(f"[red]Erro ao abrir dashboard:[/red] {e}")

            Prompt.ask("\nPressione [bold]ENTER[/bold] para voltar ao menu principal")

        elif choice == "3":
            console.print("\n[bold cyan]--- PREVISÃO PROBABILÍSTICA DE CONFRONTO ---[/bold cyan]")
            if teams:
                console.print(f"[dim]Equipes disponíveis: {', '.join(teams)}[/dim]\n")
            team_a = Prompt.ask("Primeira Equipe", default=teams[0] if teams else "SÃO PAULO")
            team_b = Prompt.ask("Segunda Equipe", default=teams[1] if len(teams) > 1 else "MINAS GERAIS")

            try:
                display_match_prediction(team_a, team_b)
            except Exception as e:
                console.print(f"[red]Erro ao calcular previsão:[/red] {e}")

            Prompt.ask("\nPressione [bold]ENTER[/bold] para voltar ao menu principal")

        elif choice == "4":
            console.print("\n[bold cyan]--- PREVISÃO DE ACIONAMENTO DA LEVANTADORA ---[/bold cyan]")
            if teams:
                console.print(f"[dim]Equipes disponíveis: {', '.join(teams)}[/dim]\n")
            team = Prompt.ask("Equipe para análise", default=teams[0] if teams else "SÃO PAULO")

            console.print("\nRotação da levantadora: [bold]P1, P2, P3, P4, P5, P6[/bold] (ou ENTER para todas)")
            rot = Prompt.ask("Rotação", default="P1")
            if not rot.strip():
                rot = None

            console.print("\nQualidade do passe: [bold]positive[/bold] (Passe A / mão), [bold]negative[/bold] (Passe C / quebrado), [bold]transition[/bold] (K2), ou ENTER para todas")
            pass_q = Prompt.ask("Passe", default="negative")
            if not pass_q.strip():
                pass_q = None

            try:
                display_setter_distribution(team, rotation=rot, pass_quality=pass_q)
            except Exception as e:
                console.print(f"[red]Erro ao analisar levantadora:[/red] {e}")

            Prompt.ask("\nPressione [bold]ENTER[/bold] para voltar ao menu principal")

        elif choice == "5":
            console.print("\n[bold cyan]--- RANKINGS E ESTATÍSTICAS OFICIAIS ---[/bold cyan]")
            try:
                display_rankings(competition_title="CBS 2026", min_attack_attempts=10, min_serve_attempts=10)
            except Exception as e:
                console.print(f"[red]Erro ao exibir rankings:[/red] {e}")

            Prompt.ask("\nPressione [bold]ENTER[/bold] para voltar ao menu principal")

        elif choice == "6":
            console.print("\n[bold cyan]--- BOLETIM DIÁRIO FORMATADO PARA WHATSAPP (CT) ---[/bold cyan]")
            txt_path = EXPORTS_DIR / "boletim_ct_diario.txt"
            if txt_path.exists():
                content = txt_path.read_text(encoding="utf-8")
                console.print(Panel(content, title="Boletim CT", border_style="cyan"))

                # Try copying to Linux clipboard if xclip or wl-copy is installed
                copied = False
                for cmd in [["xclip", "-selection", "clipboard"], ["wl-copy"]]:
                    try:
                        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                        p.communicate(input=content.encode("utf-8"))
                        if p.returncode == 0:
                            copied = True
                            break
                    except Exception:
                        pass

                if copied:
                    console.print("[green]✓ Texto copiado automaticamente para a sua área de transferência! (Pronto para Ctrl+V no WhatsApp)[/green]")
                else:
                    console.print(f"[dim]Arquivo salvo em: {txt_path.resolve()}[/dim]")
            else:
                console.print("[yellow]Nenhum boletim gerado ainda. Execute a opção [1] para sincronizar e gerar o primeiro boletim.[/yellow]")

            Prompt.ask("\nPressione [bold]ENTER[/bold] para voltar ao menu principal")

        elif choice == "7":
            console.print("\n[bold cyan]--- AVALIAÇÃO DA ACURÁCIA DO MODELO PREDITIVO ---[/bold cyan]")
            try:
                display_model_evaluation()
            except Exception as e:
                console.print(f"[red]Erro ao avaliar modelo:[/red] {e}")

            Prompt.ask("\nPressione [bold]ENTER[/bold] para voltar ao menu principal")

        elif choice == "8":
            console.print("\n[bold cyan]--- EXPORTAÇÃO COMPLETA DE DADOS ---[/bold cyan]")
            try:
                export_all_to_csv()
                export_all_to_json()
                export_dashboard_html()
                console.print(f"[green]✓ Todos os arquivos exportados com sucesso na pasta [bold]{EXPORTS_DIR.resolve()}[/bold][/green]")
            except Exception as e:
                console.print(f"[red]Erro na exportação:[/red] {e}")

            Prompt.ask("\nPressione [bold]ENTER[/bold] para voltar ao menu principal")


if __name__ == "__main__":
    run_interactive_menu()
