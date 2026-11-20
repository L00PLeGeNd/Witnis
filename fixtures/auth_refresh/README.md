# auth_refresh — narrative demo fixture

Task the community demo walks through:

> Change **token refresh** so expired refresh tokens are rejected, without breaking login or the auth filter.

Files map to a familiar stack shape:

| Role | File |
|---|---|
| Controller | `controller.py` |
| Auth service | `service.py` |
| Token store | `tokens.py` |
| Auth filter / middleware | `filter.py` |
| Tests | `test_auth_refresh.py` |

Run: `witnis scene` (from repo root) or `witnis demo fixtures/auth_refresh -s refresh_token`
