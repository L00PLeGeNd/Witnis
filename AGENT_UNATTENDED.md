# Local unattended kickoff (Witnis v0.1)

## Your settings (once)

Cursor → Settings → Agents → Approvals & Execution → prefer fewer prompts (`Auto-run` / `Run Everything` if you accept the risk).  
Keep the machine awake; leave this repo as the workspace: `C:\Users\Ibiza\Desktop\IT\Witnis`.

## Paste this into a new Agent chat

```text
You are continuing Witnis v0.1 Foundation in this local repo only.

Read and follow:
- docs/superpowers/specs/2026-11-03-witnis-design.md
- docs/superpowers/plans/2026-11-03-witnis-v0.1-foundation.md

Hard rules:
- Do NOT gh repo create, do NOT add a public remote, do NOT push to GitHub.
- Do NOT add Co-authored-by Cursor / AI trailers in commits.
- Do NOT build Studio, MCP, Verification, or multi-language parsers in v0.1.
- Stay inside the Witnis folder. Read-only toward indexed fixture sources.

Success criteria (stop when all green):
1. pytest passes
2. `python -m witnis index fixtures/mini_py` works
3. `python -m witnis overview` shows nonzero files/symbols
4. `python -m witnis search login` finds the fixture symbol with file+line
5. Write docs/demo-v0.1.md with the exact commands and sample output

Work autonomously task-by-task from the plan. Commit locally when a task is done. If blocked twice on the same error, stop and write BLOCKED.md with the error and last attempts. When success criteria pass, write DONE.md and stop—do not ask me what to do next unless blocked.
```

## After it finishes

Check `DONE.md` or `BLOCKED.md`, run the three demo commands yourself once, then decide whether the result is good enough to publish later.
