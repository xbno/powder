# Powder - Development Guidelines

## Philosophy

This is a **simple POC**. Keep it minimal. No over-engineering.

## Code Style

- **Absolute imports only**: Use `from powder.tools.database import X`, never `from .database import X`
- **Empty `__init__.py` files**: No re-exports, no `__all__`, just docstrings if needed
- **No premature abstraction**: Write simple, direct code. Three similar lines > one clever abstraction
- **No unnecessary complexity**: If it's not needed for the POC, don't add it

## Structure

```
powder/
├── agent.py          # Main DSPy agent
├── signatures.py     # DSPy signatures
├── tools/
│   ├── database.py   # Mountain DB queries
│   ├── weather.py    # Open-Meteo client
│   ├── routing.py    # Distance/routing
│   └── scoring.py    # Scoring function
├── data/
│   └── seed_mountains.py
└── eval/
    ├── dataset.py
    ├── metrics.py
    └── backtest.py
```

## Testing Style

Use `pytest` with `@pytest.mark.parametrize` for data-driven tests:

```python
@pytest.mark.parametrize(
    "input_val, expected_output",
    [
        # Descriptive comment for this case
        (input1, expected1),
        # Another case
        (input2, expected2),
    ],
)
def test_something(self, input_val, expected_output):
    """Test description."""
    result = function_under_test(input_val)
    assert result == expected_output
```

For API mocks, use `unittest.mock.patch` with `side_effect` for multiple responses:

```python
with patch("powder.tools.module.httpx.get") as mock_get:
    mock_get.return_value = MagicMock(json=MagicMock(return_value=mock_response))
    result = function_under_test()
```

Keep test data inline in parametrize tuples - no separate fixtures for simple cases.

## Key Decisions

- **Region**: Northeast US (Vermont, New Hampshire, Maine, New York, Massachusetts)
- **Weather API**: Open-Meteo (free, no key needed)
- **Routing**: Haversine for filtering, OpenRouteService for accurate drive times
- **Database**: SQLite via SQLAlchemy
- **No snow reports**: Rely on Open-Meteo snow depth data
