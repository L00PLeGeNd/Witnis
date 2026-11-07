# Public benchmark scoreboard

Command: `python -m witnis bench --suite public`

```
version   passed/total   score   notes
1.8.0     21/21          1.00    +public_svc Ledger/Authorize; CI gate
1.7.0     19/19          1.00    public_svc polyglot + LSP index fallback
1.6.0     12/12          1.00    mini_* suite
```

Fixtures: `fixtures/mini_py`, `mini_go`, `mini_js`, `mini_java`, `fixtures/public_svc`.  
Task definitions: [`benchmarks/public/tasks.json`](../../benchmarks/public/tasks.json).
