# Witnis vs baselines (local)

- Fixture: `fixtures\mini_py`
- Query: `login`

## Witnis

- Typed search hits: **3**
- Trace callers: **4**
- Impact direct edges: **6**
- Index health issues: 0
- Incremental refresh skipped/updated: 4/0
- Latency ms: `{'index': 71.04, 'search': 38.08, 'trace': 41.57, 'impact': 64.69}`

## Baselines

- git/naive grep text hits: **11** (no symbol kinds / call graph / evidence envelope)
- Naive file scan: 4 code files, 3 regex login defs

## Deltas (Witnis advantages on this fixture)

- Typed symbols over grep: **3**
- Relation edges over grep: **10**
- Typed symbols over naive regex: **0**

## Security / agent-safety checks

- Verify blocked without auth: **True**
- Unauthorized writes observed: **0**
- Core path requires LLM: **False**

## Notes

- This is a **local** acceptance report, not a published leaderboard.
- Public GitHub remains gated until maintainers explicitly publish.
