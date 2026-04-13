# Sample Drift Report — Evidence

This is an example of Drift running against a real codebase. The findings below are illustrative.

---

## 🗺️ Drift Report: `acme-api`

> Found 11 drifts across 23 files: 📢 3 shouts, 🗣️ 5 murmurs, 🤫 3 whispers

## Overview

| Metric | Value |
|--------|-------|
| Files scanned | 23 |
| Strata examined | 47 |
| Total drifts | 11 |
| Stale (>6mo) | 4 |

## 📢 Shouts (fix these)

These are dangerous lies. Someone will get burned.

### `tests/test_auth.py:45` 🪦 STALE
**Claims:** `test_validates_expired_token` is a test\
**Reality:** Contains zero assertions. This is theater.

```python
def test_validates_expired_token():
    token = create_token(expires_in=-1)
    result = validate(token)
    # TODO: add assertion
```

---

### `tests/test_payments.py:89`
**Claims:** `test_handles_payment_failure` handles errors\
**Reality:** Catches exceptions and swallows them silently

```python
def test_handles_payment_failure():
    try:
        process_payment(invalid_card)
    except Exception:
        pass  # "handled"
```

---

### `README.md:34`
**Claims:** README references function `migrate_database()`\
**Reality:** No function named `migrate_database` found in codebase

```markdown
## Quick Start
    migrate_database()
    start_server()
```

---

## 🗣️ Murmurs (address when nearby)

### `api/handlers.py:67`
**Claims:** Comment references `validate_schema`\
**Reality:** `validate_schema` not found as identifier in this file

```python
# Validate the request using validate_schema before processing
data = request.json()
process(data)
```

---

### `api/handlers.py:112`
**Claims:** Comment says function returns: the user object\
**Reality:** Function actually returns: user.id

```python
# Returns the user object for the given session
def get_current_user(session):
    user = db.query(User).filter_by(session_id=session.id).first()
    return user.id
```

---

## 🔥 Hotspots

Files with the most drift:

- **tests/test_auth.py** — 3 drifts (2 📢)
- **api/handlers.py** — 2 drifts
- **README.md** — 2 drifts

---

## Drift Age Distribution
```
     < 1 month | ███████ 3
   1-3 months  | ████████████ 4
  6-12 months  | ██████ 2
      > 1 year | ████ 2
```

Staleness score: 0.41 (0=fresh, 1=ancient)
