"""Thin Python SDK surface for agents and scripts.

Prefer importing from ``witnis.sdk`` over reaching into ``witnis.core`` internals.
"""

from __future__ import annotations

from witnis.core.index import index_repository
from witnis.core.tools import (
    analyze_change_impact,
    analyze_impact,
    check_import_graph,
    check_index_health,
    check_python_syntax,
    compare_revisions,
    compare_worktree,
    explain_change,
    explain_code,
    export_evidence_bundle,
    export_relation_graph,
    find_related_tests,
    get_evidence,
    list_capabilities,
    list_commits,
    list_index_snapshots,
    list_test_results,
    ingest_runtime_traces,
    query_lsp,
    refresh_evidence,
    refresh_index,
    render_evidence_report,
    repo_overview,
    repo_search,
    repo_status,
    scan_secrets,
    trace_symbol,
)
from witnis.core.verify import (
    create_verification_plan,
    get_verification_report,
    list_verification_runs,
    run_verification,
)
from witnis.compare_baselines import run_baseline_compare, write_baseline_report
from witnis.studio import render_studio

__all__ = [
    "index_repository",
    "repo_overview",
    "repo_status",
    "repo_search",
    "trace_symbol",
    "explain_code",
    "explain_change",
    "analyze_impact",
    "analyze_change_impact",
    "find_related_tests",
    "get_evidence",
    "ingest_runtime_traces",
    "query_lsp",
    "refresh_evidence",
    "refresh_index",
    "export_evidence_bundle",
    "export_relation_graph",
    "render_evidence_report",
    "render_studio",
    "check_import_graph",
    "check_index_health",
    "check_python_syntax",
    "compare_revisions",
    "compare_worktree",
    "scan_secrets",
    "list_capabilities",
    "list_commits",
    "list_index_snapshots",
    "list_test_results",
    "create_verification_plan",
    "run_verification",
    "get_verification_report",
    "list_verification_runs",
    "run_baseline_compare",
    "write_baseline_report",
]
