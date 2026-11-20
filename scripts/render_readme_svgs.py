"""Render the README diagrams in docs/assets/.

Every figure is laid out from explicit coordinates, every label is checked
against the box that holds it, and every moving token is bound to the same
<path> that is drawn on screen (animateMotion + mpath), so motion can never
drift off its track.

Data shown in the diagrams was captured from real runs:
  - blast-radius.svg:  `witnis impact Person` on spring-petclinic @ 500158f
  - trusted-agent-loop.svg: `witnis look/impact/plan/verify redact_text` on this repo

    python scripts/render_readme_svgs.py
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

ASSETS = Path(__file__).resolve().parents[1] / "docs" / "assets"

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

BG = "#0d1117"
PANEL = "#161b22"
LINE = "#30363d"
RULE = "#21262d"
FG = "#e6edf3"
MUTED = "#8b949e"
BLUE = "#58a6ff"
PURPLE = "#bc8cff"
GREEN = "#3fb950"
ORANGE = "#d29922"
RED = "#f85149"

# Conservative advance widths (em). Mono covers SF Mono/Menlo (0.60) and Consolas (0.55).
MONO_EM = 0.61
SANS_EM = 0.56

EASE = "0.42 0 0.2 1"
HOLD = "0 0 1 1"


def esc(s: str) -> str:
    out = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return "".join(c if ord(c) < 128 else f"&#{ord(c)};" for c in out)


def width(text: str, size: float, mono: bool) -> float:
    return len(text) * size * (MONO_EM if mono else SANS_EM)


def fit(text: str, size: float, mono: bool, room: float, where: str) -> None:
    w = width(text, size, mono)
    if w > room:
        raise SystemExit(f"text overflows {where}: {text!r} needs {w:.0f}px, has {room:.0f}px")


def t(x, y, s, *, size=12, mono=True, fill=FG, anchor="start", weight=None, extra=""):
    fam = MONO if mono else SANS
    w = f' font-weight="{weight}"' if weight else ""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}"'
        f' fill="{fill}" text-anchor="{anchor}"{w}{extra}>{esc(s)}</text>'
    )


def kt(*vals: float) -> str:
    return ";".join(f"{v:.4f}".rstrip("0").rstrip(".") if v not in (0, 1) else str(int(v)) for v in vals)


def frame(w: int, h: int, title: str, body: list[str]) -> str:
    return "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"'
            f' width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">',
            f"<title>{esc(title)}</title>",
            "<style>@media (prefers-reduced-motion: reduce) { * { animation: none !important; } }</style>",
            f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="12" fill="{BG}" stroke="{LINE}"/>',
            *body,
            "</svg>",
            "",
        ]
    )


# --------------------------------------------------------------------------- blast radius


@dataclass
class Node:
    key: str
    name: str
    sub: str
    cx: float
    cy: float
    w: float
    h: float = 40

    @property
    def left(self) -> float:
        return self.cx - self.w / 2

    @property
    def right(self) -> float:
        return self.cx + self.w / 2


def blast_radius() -> str:
    W, H = 960, 440
    dur = 9.0
    body: list[str] = []

    # header
    body.append(f'<line x1="0" y1="48" x2="{W}" y2="48" stroke="{RULE}"/>')
    body.append(t(24, 30, "$", fill=MUTED, size=13))
    body.append(t(38, 30, "witnis impact Person", size=13))
    head_r = "spring-petclinic @ 500158f   index_stale: false"
    fit(head_r, 12, True, 520, "blast header")
    body.append(t(W - 24, 30, head_r, size=12, fill=MUTED, anchor="end"))

    # left: what text search sees
    lx, ly, lw, lh = 24, 68, 246, 352
    body.append(f'<rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" rx="8" fill="{PANEL}" stroke="{LINE}"/>')
    inner = lw - 32
    grep = "$ git grep -lw Person"
    fit(grep, 12, True, inner, "grep title")
    body.append(t(lx + 16, ly + 26, grep, size=12, fill=MUTED))
    hits = [
        "Person.java",
        "Owner.java",
        "Vet.java",
        "PetClinicRuntimeHints.java",
        "ValidatorTests.java",
    ]
    y = ly + 56
    for h in hits:
        fit(h, 12, True, inner - 14, "grep hit")
        body.append(f'<rect x="{lx + 16}" y="{y - 8}" width="6" height="6" rx="1" fill="{MUTED}"/>')
        body.append(t(lx + 30, y, h, size=12))
        y += 22
    body.append(t(lx + 16, y + 6, "5 files", size=12, fill=MUTED))
    sep = ly + 214
    body.append(f'<line x1="{lx + 16}" y1="{sep}" x2="{lx + lw - 16}" y2="{sep}" stroke="{LINE}"/>')
    body.append(t(lx + 16, sep + 28, "Not matched by text search", size=13, mono=False, fill=FG, weight="600"))
    missed = ["OwnerController.java", "PetController.java", "VisitController.java"]
    miss_y = [sep + 54 + i * 22 for i in range(3)]

    # graph columns
    c1 = Node("person", "Person", "Person.java:29", 350, 238, 112)
    col2 = [
        Node("owner", "Owner", "inherits  :50", 580, 128, 184),
        Node("vet", "Vet", "inherits  :45", 580, 192, 184),
        Node("hints", "PetClinicRuntimeHints", "imports  :22", 580, 280, 184),
        Node("vtests", "ValidatorTests", "calls  :52 :68  (test)", 580, 344, 184),
    ]
    col3 = [
        Node("ownerctl", "OwnerController", "uses_type Owner  :78", 836, 108, 184),
        Node("petctl", "PetController", ":101 :108 :145 :186", 836, 172, 184),
        Node("visitctl", "VisitController", "uses_type Owner  :98", 836, 236, 184),
    ]
    status1 = {"owner": BLUE, "vet": BLUE, "hints": BLUE, "vtests": PURPLE}

    for x, label in ((c1.cx, "changed"), (580, "hop 1 \u00b7 direct"), (836, "hop 2 \u00b7 transitive")):
        body.append(t(x, 80, label, size=11, fill=MUTED, anchor="middle"))

    # timeline (fractions of dur)
    h1s, h1e = 0.10, 0.32
    h2s, h2e = 0.40, 0.62
    off = 0.90

    def edge_path(a: Node, b: Node) -> str:
        x1, y1, x2, y2 = a.right + 2, a.cy, b.left - 2, b.cy
        g = (x2 - x1) * 0.5
        return f"M{x1:.1f},{y1:.1f} C{x1 + g:.1f},{y1:.1f} {x2 - g:.1f},{y2:.1f} {x2:.1f},{y2:.1f}"

    defs = [
        "<defs>",
        '<filter id="glow" x="-200%" y="-200%" width="500%" height="500%">'
        '<feGaussianBlur stdDeviation="3"/></filter>',
    ]
    edges_svg: list[str] = []
    tokens_svg: list[str] = []

    def add_edge(eid: str, a: Node, b: Node, color: str, s: float, e: float) -> None:
        defs.append(f'<path id="{eid}" d="{edge_path(a, b)}"/>')
        edges_svg.append(f'<use xlink:href="#{eid}" fill="none" stroke="{LINE}" stroke-width="1.5"/>')
        edges_svg.append(
            f'<path d="{edge_path(a, b)}" fill="none" stroke="{color}" stroke-width="1.75"'
            f' stroke-dasharray="1 1" stroke-dashoffset="1" pathLength="1" opacity="0">'
            f'<animate attributeName="stroke-dashoffset" dur="{dur}s" repeatCount="indefinite"'
            f' values="1;1;0;0" keyTimes="{kt(0, s, e, 1)}" calcMode="spline" keySplines="{HOLD};{EASE};{HOLD}"/>'
            f'<animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite"'
            f' values="0;0;1;1;0" keyTimes="{kt(0, s, s + 0.01, off, 1)}"/>'
            "</path>"
        )
        tokens_svg.append(
            f'<g opacity="0">'
            f'<circle r="7" fill="{color}" opacity="0.35" filter="url(#glow)"/>'
            f'<circle r="3.5" fill="{color}"/>'
            f'<animateMotion dur="{dur}s" repeatCount="indefinite" keyPoints="0;0;1;1"'
            f' keyTimes="{kt(0, s, e, 1)}" calcMode="spline" keySplines="{HOLD};{EASE};{HOLD}">'
            f'<mpath xlink:href="#{eid}"/></animateMotion>'
            f'<animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite"'
            f' values="0;0;1;1;0;0" keyTimes="{kt(0, s, s + 0.02, e, e + 0.05, 1)}"/>'
            "</g>"
        )

    for n in col2:
        add_edge(f"e-{n.key}", c1, n, status1[n.key], h1s, h1e)
    for n in col3:
        add_edge(f"e-{n.key}", col2[0], n, PURPLE, h2s, h2e)
    defs.append("</defs>")

    def node_svg(n: Node, lit: str | None, at: float) -> str:
        fit(n.name, 12.5, True, n.w - 20, f"node {n.key}")
        fit(n.sub, 10.5, True, n.w - 20, f"node {n.key} sub")
        parts = [
            f'<rect x="{n.left:.1f}" y="{n.cy - n.h / 2:.1f}" width="{n.w}" height="{n.h}" rx="6"'
            f' fill="{PANEL}" stroke="{LINE if lit else BLUE}" stroke-width="1.25">'
        ]
        if lit:
            parts.append(
                f'<animate attributeName="stroke" dur="{dur}s" repeatCount="indefinite"'
                f' values="{LINE};{LINE};{lit};{lit};{LINE}" keyTimes="{kt(0, at, at + 0.04, off, 1)}"/>'
            )
        parts.append("</rect>")
        parts.append(t(n.cx, n.cy - 3, n.name, size=12.5, anchor="middle"))
        parts.append(t(n.cx, n.cy + 13, n.sub, size=10.5, fill=MUTED, anchor="middle"))
        return "".join(parts)

    body.extend(defs)
    body.extend(edges_svg)
    person = node_svg(c1, None, 0)
    pulse = (
        f'<rect x="{c1.left:.1f}" y="{c1.cy - c1.h / 2:.1f}" width="{c1.w}" height="{c1.h}" rx="6"'
        f' fill="none" stroke="{BLUE}" stroke-width="1.25" opacity="0">'
        f'<animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite"'
        f' values="0;0.9;0;0" keyTimes="{kt(0, 0.02, h1s + 0.04, 1)}"/>'
        f'<animate attributeName="stroke-width" dur="{dur}s" repeatCount="indefinite"'
        f' values="1.25;1.25;7;7" keyTimes="{kt(0, 0.02, h1s + 0.04, 1)}"/>'
        "</rect>"
    )
    body.append(pulse)
    body.append(person)
    for n in col2:
        body.append(node_svg(n, status1[n.key], h1e))
    for n in col3:
        body.append(node_svg(n, PURPLE, h2e))
    body.extend(tokens_svg)

    # missed list reacts when hop 2 lands
    for name, yy in zip(missed, miss_y):
        fit(name, 12, True, inner - 14, "missed")
        body.append(
            f'<rect x="{lx + 16}" y="{yy - 8}" width="6" height="6" rx="1" fill="{LINE}">'
            f'<animate attributeName="fill" dur="{dur}s" repeatCount="indefinite"'
            f' values="{LINE};{LINE};{PURPLE};{PURPLE};{LINE}" keyTimes="{kt(0, h2e, h2e + 0.04, off, 1)}"/>'
            "</rect>"
        )
        body.append(
            t(lx + 30, yy, name, size=12, fill=MUTED)[:-7]
            + f'<animate attributeName="fill" dur="{dur}s" repeatCount="indefinite"'
            f' values="{MUTED};{MUTED};{FG};{FG};{MUTED}" keyTimes="{kt(0, h2e, h2e + 0.04, off, 1)}"/>'
            "</text>"
        )
    # legend
    ly2 = 410
    gx = 300
    body.append(f'<circle cx="{gx + 4}" cy="{ly2 - 4}" r="4" fill="{BLUE}"/>')
    body.append(t(gx + 14, ly2, "observed  AST / import", size=11, fill=MUTED))
    gx2 = gx + 14 + width("observed  AST / import", 11, True) + 24
    body.append(f'<circle cx="{gx2 + 4}" cy="{ly2 - 4}" r="4" fill="{PURPLE}"/>')
    body.append(t(gx2 + 14, ly2, "derived  relation graph", size=11, fill=MUTED))
    counts = "direct 6   transitive 6"
    body.append(t(W - 24, ly2, counts, size=11, fill=MUTED, anchor="end"))
    fit(counts, 11, True, (W - 24) - (gx2 + 14 + width("derived  relation graph", 11, True)) - 16, "legend")

    return frame(W, H, "witnis impact Person on spring-petclinic: text search vs relation graph", body)


# --------------------------------------------------------------------------- 15s lie / blocked / ran


def caught_lying() -> str:
    W, H = 960, 280
    dur = 15.0
    body: list[str] = []
    body.append(t(24, 28, "verify", size=13, fill=MUTED))
    body.append(t(W - 24, 28, "blocked until you authorize", size=13, fill=MUTED, anchor="end"))
    beats = [
        (0.0, 0.32, "the agent", "tests passed", GREEN, "wrote that in the PR", MUTED),
        (0.34, 0.66, "witnis", "executed: 0   blocked", ORANGE, "default, nothing ran", MUTED),
        (0.68, 0.96, "witnis", "4 passed in 0.03s", GREEN, "after WITNIS_ALLOW_VERIFY=1", MUTED),
    ]
    box_w, box_h = 280, 168
    gap = (W - 48 - 3 * box_w) / 2
    xs = [24 + i * (box_w + gap) for i in range(3)]
    for i, (x, (a, d, who, claim, color, kicker, _)) in enumerate(zip(xs, beats)):
        fit(claim, 18, True, box_w - 28, f"beat {i}")
        body.append(
            f'<rect x="{x:.1f}" y="52" width="{box_w}" height="{box_h}" rx="10" fill="{PANEL}" stroke="{LINE}">'
            f'<animate attributeName="stroke" dur="{dur}s" repeatCount="indefinite"'
            f' values="{LINE};{LINE};{color};{color};{LINE};{LINE}"'
            f' keyTimes="{kt(0, max(a - 0.001, 0), a, d, min(d + 0.02, 0.999), 1)}"/>'
            "</rect>"
        )
        body.append(t(x + 16, 78, who, size=12, fill=MUTED))
        body.append(t(x + 16, 128, claim, size=18, fill=color, weight="700" if i else None))
        body.append(t(x + 16, 158, kicker, size=12, fill=MUTED))
        body.append(
            f'<rect x="{x:.1f}" y="{52 + box_h - 6:.1f}" width="0" height="6" rx="3" fill="{color}">'
            f'<animate attributeName="width" dur="{dur}s" repeatCount="indefinite"'
            f' values="0;0;{box_w};{box_w};0;0" keyTimes="{kt(0, a, a + 0.04, d, d + 0.02, 1)}"/>'
            "</rect>"
        )
    return frame(W, H, "Agent said tests passed. Witnis: executed 0, blocked. Then authorized: 4 passed in 0.03s.", body)


# --------------------------------------------------------------------------- loop


def loop() -> str:
    W, H = 960, 404
    body: list[str] = []
    xs = [96, 288, 480, 672, 864]
    ty = 92
    dwell, travel, reset = 3.4, 1.1, 0.9
    dur = 5 * dwell + 4 * travel + reset
    fade = 0.35

    arrive, depart = [], []
    clock = 0.0
    for i in range(5):
        arrive.append(clock / dur)
        clock += dwell
        depart.append(clock / dur)
        clock += travel if i < 4 else 0
    end_hold = depart[-1]
    f = fade / dur

    body.append(f'<line x1="0" y1="48" x2="{W}" y2="48" stroke="{RULE}"/>')
    body.append(t(24, 30, "Gated verification loop", size=14, mono=False, weight="600"))
    right = "target: redact_text   src/witnis/core/security.py:67"
    fit(right, 12, True, W - 48 - width("Gated verification loop", 14, False) - 24, "loop header")
    body.append(t(W - 24, 30, right, size=12, fill=MUTED, anchor="end"))

    stages = [
        ("look", "witnis look", BLUE),
        ("impact", "witnis impact", BLUE),
        ("plan", "witnis plan", BLUE),
        ("verify, no auth", "verify --execute", ORANGE),
        ("verify, authorized", "WITNIS_ALLOW_VERIFY=1", GREEN),
    ]

    # track + progress (progress shares the token's keyTimes and splines)
    kts = [0.0]
    pts = [0.0]
    for i in range(5):
        kts.append(depart[i] if i < 4 else end_hold)
        pts.append(i / 4)
        if i < 4:
            kts.append(arrive[i + 1])
            pts.append((i + 1) / 4)
    kts.append(1.0)
    pts.append(1.0)
    splines = []
    for i in range(len(kts) - 1):
        splines.append(EASE if pts[i] != pts[i + 1] else HOLD)
    spl = ";".join(splines)

    body.append(
        "<defs>"
        f'<path id="track" d="M{xs[0]},{ty} H{xs[-1]}"/>'
        '<filter id="glow" x="-200%" y="-200%" width="500%" height="500%">'
        '<feGaussianBlur stdDeviation="3.5"/></filter>'
        "</defs>"
    )
    body.append(f'<use xlink:href="#track" stroke="{LINE}" stroke-width="2" fill="none"/>')
    off_vals = ";".join(f"{1 - p:g}" for p in pts)
    body.append(
        f'<path d="M{xs[0]},{ty} H{xs[-1]}" stroke="{BLUE}" stroke-width="2" fill="none" pathLength="1"'
        f' stroke-dasharray="1 1" stroke-dashoffset="1">'
        f'<animate attributeName="stroke-dashoffset" dur="{dur:.2f}s" repeatCount="indefinite"'
        f' values="{off_vals}" keyTimes="{kt(*kts)}" calcMode="spline" keySplines="{spl}"/>'
        f'<animate attributeName="opacity" dur="{dur:.2f}s" repeatCount="indefinite"'
        f' values="1;1;0;0" keyTimes="{kt(0, end_hold, end_hold + f, 1)}"/>'
        "</path>"
    )

    for i, (x, (label, cmd, color)) in enumerate(zip(xs, stages)):
        room = (xs[1] - xs[0]) - 16
        fit(label, 13, False, room, f"stage {i}")
        fit(cmd, 11, True, room, f"stage {i} cmd")
        a = arrive[i]
        body.append(
            f'<circle cx="{x}" cy="{ty}" r="7" fill="{BG}" stroke="{LINE}" stroke-width="2">'
            f'<animate attributeName="stroke" dur="{dur:.2f}s" repeatCount="indefinite"'
            f' values="{LINE};{LINE};{color};{color};{LINE};{LINE}"'
            f' keyTimes="{kt(0, max(a - 0.0001, 0), a + f / 2, end_hold, end_hold + f, 1)}"/>'
            "</circle>"
        )
        body.append(t(x, ty + 30, label, size=13, mono=False, anchor="middle"))
        body.append(t(x, ty + 48, cmd, size=11, fill=MUTED, anchor="middle"))

    body.append(
        f'<g opacity="0">'
        f'<circle r="9" fill="{BLUE}" opacity="0.45" filter="url(#glow)"/>'
        f'<circle r="4.5" fill="{FG}"/>'
        f'<animateMotion dur="{dur:.2f}s" repeatCount="indefinite" keyPoints="{";".join(f"{p:g}" for p in pts)}"'
        f' keyTimes="{kt(*kts)}" calcMode="spline" keySplines="{spl}"><mpath xlink:href="#track"/></animateMotion>'
        f'<animate attributeName="opacity" dur="{dur:.2f}s" repeatCount="indefinite"'
        f' values="0;1;1;0;0" keyTimes="{kt(0, f, end_hold, end_hold + f, 1)}"/>'
        "</g>"
    )

    # output panel
    px, py, pw, ph = 24, 164, W - 48, 216
    body.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="8" fill="{PANEL}" stroke="{LINE}"/>')
    D = "\u2014"
    panels: list[tuple[str, tuple[str, str], list[tuple[str, str]]]] = [
        (
            "witnis look redact_text",
            ("success", BLUE),
            [
                ("def     function  redact_text  src/witnis/core/security.py:67", FG),
                ("caller  src/witnis/core/security.py:scan_text_for_secrets  :97 :114", FG),
                ("caller  src/witnis/core/verify.py:run_verification  :454 :455 :476 :477", FG),
                ("caller  tests/test_security.py:test_redact_text_masks_secrets  :13", FG),
                ("impact  8 direct edge(s)", FG),
                ("tests   tests/test_engine_parity.py, tests/test_security.py", FG),
                (f"plan    6 step(s) {D} run: witnis verify redact_text --execute", MUTED),
            ],
        ),
        (
            "witnis impact redact_text",
            ("success", BLUE),
            [
                ("repository.index_stale: false", MUTED),
                ("direct      8    calls (same-site references collapsed)  derived", FG),
                ("              security.py:scan_text_for_secrets   :97 :114", FG),
                ("              verify.py:run_verification          :454 :455 :476 :477", FG),
                ("              test_security.py  test_engine_parity.py", FG),
                ("transitive  20   callers of those callers         status: uncertain", FG),
                ("              tools.py:scan_secrets  cli.py:verify_cmd  pr_gate.py:run_pr_gate  +16", FG),
            ],
        ),
        (
            "witnis plan redact_text",
            ("planned", BLUE),
            [
                ("6 steps, nothing executed", MUTED),
                ("impact_review    analysis", FG),
                ("static_compile   python -m compileall -q src/witnis/core/security.py tests/test_security.py", FG),
                ("syntax_check     syntax", FG),
                ("import_graph     graph", FG),
                ("run_tests        python -m pytest -q tests/test_engine_parity.py tests/test_security.py", FG),
                ("static_reindex   python -m witnis index .", FG),
            ],
        ),
        (
            "witnis verify redact_text --execute",
            ("partial \u00b7 blocked", ORANGE),
            [
                ("status: partial   state: blocked   automation_verified: false", FG),
                ("executed: 0 commands", FG),
                ("", FG),
                ("limitation: Set environment variable WITNIS_ALLOW_VERIFY=1 to authorize command execution", ORANGE),
            ],
        ),
        (
            "WITNIS_ALLOW_VERIFY=1 witnis verify redact_text --execute",
            ("verified", GREEN),
            [
                ("isolation  detached git worktree at HEAD   profile: worktree   network: deny-hint", MUTED),
                ("static_compile   verified   exit 0   fs_diff: none", FG),
                ("syntax_check     verified", FG),
                ("import_graph     verified", FG),
                ("run_tests        verified   exit 0   7 passed, 1 skipped in 0.16s", FG),
                ("                 fs_diff: +4 .pytest_cache/*  (worktree removed afterwards)", MUTED),
                ("status: success   state: verified   automation_verified: true", GREEN),
            ],
        ),
    ]
    for i, (cmd, (chip, chip_color), lines) in enumerate(panels):
        a, d = arrive[i], depart[i] if i < 4 else end_hold
        g = [
            f'<g opacity="0"><animate attributeName="opacity" dur="{dur:.2f}s" repeatCount="indefinite"'
            f' values="0;0;1;1;0;0" keyTimes="{kt(0, a, a + f, d, d + f, 1)}"/>'
        ]
        if i == 0:
            g[0] = g[0].replace(f'values="0;0;1;1;0;0" keyTimes="{kt(0, a, a + f, d, d + f, 1)}"',
                                f'values="0;1;1;0;0" keyTimes="{kt(0, f, d, d + f, 1)}"')
        cw = width(chip, 11, True) + 20
        fit(cmd, 12.5, True, pw - 32 - cw - 24 - 14, f"panel {i} cmd")
        g.append(t(px + 16, py + 28, "$", size=12.5, fill=MUTED))
        g.append(t(px + 30, py + 28, cmd, size=12.5))
        cx = px + pw - 16 - cw
        g.append(
            f'<rect x="{cx:.1f}" y="{py + 13}" width="{cw:.1f}" height="22" rx="11" fill="none" stroke="{chip_color}"/>'
        )
        g.append(t(cx + cw / 2, py + 28, chip, size=11, fill=chip_color, anchor="middle"))
        yy = py + 58
        for text, color in lines:
            fit(text, 12, True, pw - 32, f"panel {i} line")
            if text:
                g.append(t(px + 16, yy, text, size=12, fill=color, extra=' xml:space="preserve"'))
            yy += 21
        if yy - 21 > py + ph - 12:
            raise SystemExit(f"panel {i} overflows vertically")
        g.append("</g>")
        body.append("".join(g))

    return frame(W, H, "witnis gated verification loop on redact_text", body)


# --------------------------------------------------------------------------- masthead


def masthead() -> str:
    W, H = 960, 168
    body: list[str] = []
    body.append(
        f'<rect x="0" y="0" width="4" height="{H}" fill="{BLUE}" opacity="0.22">'
        f'<animate attributeName="opacity" dur="16s" repeatCount="indefinite" values="0.12;0.38;0.12"/>'
        "</rect>"
    )
    body.append(t(40, 78, "witnis", size=56, mono=False, weight="700"))
    line = "Indexes the repo. On a PR it comments what moved, and whether tests ran."
    fit(line, 16, False, W - 80, "masthead line")
    body.append(t(40, 118, line, size=16, mono=False, fill=MUTED))
    body.append(t(W - 40, 64, "v1.11.0", size=12, fill=MUTED, anchor="end"))
    body.append(t(W - 40, 84, "Apache-2.0", size=12, fill=MUTED, anchor="end"))
    body.append(f'<line x1="40" y1="140" x2="{W - 40}" y2="140" stroke="{RULE}"/>')
    note = "witnis-dev  ·  not the company at witnis.se"
    fit(note, 12, False, W - 80, "masthead note")
    body.append(t(40, 158, note, size=12, mono=False, fill=MUTED))
    return frame(W, H, "witnis", body)


def main() -> None:
    out = {
        "witnis-masthead.svg": masthead(),
        "caught-lying.svg": caught_lying(),
        "blast-radius.svg": blast_radius(),
        "trusted-agent-loop.svg": loop(),
    }
    for name, svg in out.items():
        ET.fromstring(svg.encode("utf-8"))
        (ASSETS / name).write_text(svg, encoding="utf-8", newline="\n")
        studio = Path(__file__).resolve().parents[1] / "src" / "witnis" / "studio" / "assets"
        studio.mkdir(parents=True, exist_ok=True)
        (studio / name).write_text(svg, encoding="utf-8", newline="\n")
        print(f"wrote docs/assets/{name} and src/witnis/studio/assets/{name} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
