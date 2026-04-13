# Before & After — What Drift Catches

## Before: A developer reads this code

```python
# Validates the input schema and returns the cleaned data
def process_request(data, schema, timeout=30):
    """
    Process an incoming API request.
    
    Args:
        data: The raw request data
        schema: JSON schema to validate against
        timeout: Request timeout in seconds
        retries: Number of retry attempts
    
    Returns:
        dict: The validated and transformed response
    """
    # TODO: add schema validation (JIRA-1234)
    result = transform(data)
    return result.id
```

The developer thinks:
- ✅ This function validates schemas (comment says so)
- ✅ It accepts a `retries` parameter (docstring says so)  
- ✅ It returns a dict (docstring says so)
- ✅ Schema validation is coming soon (TODO says so)

## After: Drift scans this code

```
📢 [test_name_vs_assertion] process.py:1
   Claims: Comment says function validates input schema
   Reality: No validation logic found in function body

🗣️ [docstring_vs_signature] process.py:3
   Claims: Docstring documents param `retries`
   Reality: `retries` is not in the function signature

🗣️ [comment_vs_code] process.py:3
   Claims: Docstring says returns dict
   Reality: Function returns `result.id` (likely a scalar)

🤫 [todo_abandoned] process.py:14
   Claims: TODO: add schema validation (JIRA-1234)
   Reality: This TODO has been here for 347 days
```

The developer now knows:
- ❌ There is no schema validation — the comment lies
- ❌ There is no `retries` parameter — the docstring lies
- ❌ It returns an ID, not a dict — the docstring lies
- ❌ That TODO is nearly a year old — nobody is doing it

**Four lies in 15 lines of code.** None of them would be caught by a linter, a type checker, or a test suite. Drift catches all four.

---

## The value proposition

| Tool | Catches this? |
|------|:---:|
| Linter (ruff, flake8) | ❌ |
| Type checker (mypy) | ❌ |
| Test suite | ❌ |
| Code review (human) | Maybe |
| Code review (AI) | Maybe |
| **Drift** | **✅** |

Drift fills the gap between "the code compiles" and "the code is honest."
