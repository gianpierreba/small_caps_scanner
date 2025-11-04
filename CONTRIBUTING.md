## Development Setup

1. Install pre-commit:
```bash
   pip install pre-commit
```

2. Install git hooks:
```bash
   pre-commit install
```

3. Now linting runs automatically on every commit!

To manually run checks:
```bash
pre-commit run --all-files
```