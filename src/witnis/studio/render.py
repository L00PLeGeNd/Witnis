from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from witnis.core.envelope import make_envelope
from witnis.core.tools import (
    export_relation_graph,
    get_evidence,
    render_evidence_report,
    repo_search,
    repo_status,
)

_TEMPLATE = Path(__file__).with_name("template.html")

_I18N = {
    "en": {
        "lede": "Local evidence studio — witness the index, verification runs, and symbol proof without leaving the machine.",
        "index": "Index",
        "health": "Health",
        "runs": "Recent verification",
        "graph": "Relation graph",
        "evidence": "Evidence",
        "report": "Report",
        "files": "Files",
        "symbols": "Symbols",
        "snapshots": "Snapshots",
        "health_ok": "No structural issues. Index looks coherent.",
        "runs_empty": "No verification runs persisted yet. Plan or execute a verify pass.",
        "graph_empty": "No graph for this target yet. Pass --target when rendering studio.",
        "evidence_empty": "No evidence rows for this target.",
        "report_empty": "No report rendered.",
        "foot": "Witnis Studio · local-only",
        "verify": "verify",
    },
    "zh": {
        "lede": "本地证据工作室 — 在机器上核对索引、验证运行与符号证据。",
        "index": "索引",
        "health": "健康",
        "runs": "最近验证",
        "graph": "关系图",
        "evidence": "证据",
        "report": "报告",
        "files": "文件",
        "symbols": "符号",
        "snapshots": "快照",
        "health_ok": "无结构问题，索引一致。",
        "runs_empty": "尚无验证运行。可先 plan-verify / verify。",
        "graph_empty": "尚无关系图。渲染时传入 --target。",
        "evidence_empty": "该目标暂无证据。",
        "report_empty": "暂无报告。",
        "foot": "Witnis Studio · 仅本地",
        "verify": "验证",
    },
    "pt": {
        "lede": "Estúdio local de evidências — índice, verificações e prova de símbolos na máquina.",
        "index": "Índice",
        "health": "Saúde",
        "runs": "Verificações recentes",
        "graph": "Grafo de relações",
        "evidence": "Evidência",
        "report": "Relatório",
        "files": "Arquivos",
        "symbols": "Símbolos",
        "snapshots": "Snapshots",
        "health_ok": "Sem problemas estruturais. Índice coerente.",
        "runs_empty": "Nenhuma verificação ainda. Use plan-verify / verify.",
        "graph_empty": "Sem grafo. Passe --target ao renderizar.",
        "evidence_empty": "Sem evidência para este alvo.",
        "report_empty": "Sem relatório.",
        "foot": "Witnis Studio · apenas local",
        "verify": "verificar",
    },
    "fr": {
        "lede": "Studio local de preuves — index, vérifications et symbols sans quitter la machine.",
        "index": "Index",
        "health": "Santé",
        "runs": "Vérifications récentes",
        "graph": "Graphe de relations",
        "evidence": "Preuve",
        "report": "Rapport",
        "files": "Fichiers",
        "symbols": "Symboles",
        "snapshots": "Instantanés",
        "health_ok": "Aucun problème structurel. Index cohérent.",
        "runs_empty": "Pas encore de vérification. Utilisez plan-verify / verify.",
        "graph_empty": "Pas de graphe. Passez --target à studio.",
        "evidence_empty": "Pas de preuve pour cette cible.",
        "report_empty": "Pas de rapport.",
        "foot": "Witnis Studio · local uniquement",
        "verify": "vérifier",
    },
    "ru": {
        "lede": "Локальная студия доказательств — индекс, проверки и символы на вашей машине.",
        "index": "Индекс",
        "health": "Здоровье",
        "runs": "Недавние проверки",
        "graph": "Граф связей",
        "evidence": "Доказательства",
        "report": "Отчёт",
        "files": "Файлы",
        "symbols": "Символы",
        "snapshots": "Снимки",
        "health_ok": "Структурных проблем нет. Индекс согласован.",
        "runs_empty": "Проверок пока нет. Сначала plan-verify / verify.",
        "graph_empty": "Нет графа. Передайте --target.",
        "evidence_empty": "Нет доказательств для цели.",
        "report_empty": "Нет отчёта.",
        "foot": "Witnis Studio · только локально",
        "verify": "проверка",
    },
}


def _pick_target(db_path: Path, target: str | None) -> str | None:
    if target:
        return target
    hits = repo_search(db_path, "login", limit=5)
    matches = (hits.get("result") or {}).get("matches") or []
    if matches:
        return str(matches[0].get("name") or "login")
    overview = repo_status(db_path)
    # fall back: none
    _ = overview
    return None


def render_studio(
    db_path: Path,
    *,
    out: Path | None = None,
    target: str | None = None,
    lang: str = "en",
) -> dict[str, Any]:
    """Render Studio HTML with status, graph, evidence, and report panels."""
    status = repo_status(db_path)
    if status["status"] == "failed":
        return status

    focus = _pick_target(db_path, target)
    graph_text = ""
    edge_count = 0
    if focus:
        graph_payload = export_relation_graph(db_path, focus, fmt="mermaid")
        graph_text = (graph_payload.get("result") or {}).get("graph") or ""
        edge_count = int((graph_payload.get("result") or {}).get("edge_count") or 0)

    evidence_rows: list[dict[str, Any]] = []
    if focus:
        evidence_payload = get_evidence(db_path, focus, limit=20)
        evidence_rows = list(evidence_payload.get("evidence") or [])[:20]

    report_md = ""
    if focus:
        report_payload = render_evidence_report(db_path, target=focus)
        report_md = (report_payload.get("result") or {}).get("markdown") or ""

    locale = _I18N.get(lang) or _I18N["en"]
    bundle = {
        **status,
        "studio": {
            "lang": lang if lang in _I18N else "en",
            "i18n": locale,
            "target": focus,
            "graph": graph_text,
            "edge_count": edge_count,
            "evidence": evidence_rows,
            "report_markdown": report_md[:12000],
        },
    }

    template = _TEMPLATE.read_text(encoding="utf-8")
    payload = json.dumps(bundle, ensure_ascii=False)
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e")
    html = template.replace("__WITNIS_DATA__", payload)

    target_path = out
    if target_path is None:
        base = db_path.parent if db_path.parent.exists() else Path.cwd() / ".witnis"
        base.mkdir(parents=True, exist_ok=True)
        target_path = base / "studio.html"

    target_path.write_text(html, encoding="utf-8")
    repo = status.get("repository")
    return make_envelope(
        status="success",
        repository=repo,
        result={
            "path": str(target_path.resolve()),
            "bytes": len(html.encode("utf-8")),
            "target": focus,
            "lang": lang if lang in _I18N else "en",
            "has_graph": bool(graph_text),
            "has_report": bool(report_md),
            "evidence_count": len(evidence_rows),
            "edge_count": edge_count,
        },
        evidence=[
            {
                "type": "studio_render",
                "status": "observed",
                "path": str(target_path.resolve()),
                "target": focus,
            }
        ],
        limitations=[
            "Studio is a static HTML snapshot; re-run after index/verify changes",
            "Graph/evidence/report panels require a resolvable --target",
        ],
    )
