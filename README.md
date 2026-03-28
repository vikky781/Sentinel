# Sentinel

Sentinel is a deterministic static analysis CLI for Python codebases.
It parses source files into AST, computes maintainability-oriented metrics,
and produces structured outputs for terminal, JSON, and Markdown workflows.

## Installation

### Requirements

- Python 3.10+
- pip

### Local setup

```bash
git clone https://github.com/vikky781/Sentinel.git
cd Sentinel
python -m pip install --upgrade pip
pip install -e .
```

### Optional test dependencies

```bash
pip install pytest pytest-cov
```

## Architecture

Sentinel follows strict separation of concerns:

- `parser`: AST parsing and structural extraction only
- `analysis`: metric computation only
- `scoring`: risk and score computation only
- `reporting`: formatting and report generation only
- `ai`: optional interpretation layer only
- `cli`: orchestration and user interaction only

### Module flow

1. CLI receives `analyze <path>` input.
2. Parser loads and parses `.py` file to AST.
3. Analysis modules compute independent metrics.
4. Scoring computes maintainability score and risk.
5. Reporting renders summary/JSON/Markdown outputs.
6. AI reviewer can optionally generate narrative review.

## Usage

### Analyze a file

```bash
sentinel analyze path/to/file.py
```

### Output full JSON

```bash
sentinel analyze path/to/file.py --json
```

### Write Markdown report

```bash
sentinel analyze path/to/file.py --report report.md
```

### Request AI review (optional)

```bash
sentinel analyze path/to/file.py --ai
```

### Combine outputs

```bash
sentinel analyze path/to/file.py --json --report report.md --ai
```

## Metrics Explained

Sentinel computes deterministic static metrics:

### Cyclomatic complexity

- Base value per function: `1`
- Increment rules:
	- `+1` for `if`
	- `+1` for `for`
	- `+1` for `while`
	- `+1` for `except`
	- `+1` per additional `BoolOp` operand

### Nesting depth

- Maximum DFS nesting depth per function
- Tracked control-flow nodes include:
	- `if`, `for`, `while`, `with`, `try`, `async for`, `async with`

### Recursion detection

- Direct recursion only
- Function is marked recursive if it calls itself by name

### Call graph

- Dictionary-based caller-to-callees mapping
- Captures simple and dotted call targets where statically resolvable

### Global variables

- Detects top-level assignment targets only (`Assign`, `AnnAssign`, `AugAssign`)

### Maintainability score

Score uses a weighted penalty model:

```
penalty = (avg_complexity * 4.0) + (avg_nesting * 6.0) + (globals_count * 2.0)
score   = clamp(100.0 - penalty, 0.0, 100.0)
```

Risk bands:

- `LOW` for score >= 70
- `MEDIUM` for score >= 40 and < 70
- `HIGH` for score < 40

## AI Optional Design

AI in Sentinel is strictly optional and isolated in `ai/reviewer.py`.

- Input contract: structured JSON dictionary only
- If AI is disabled: deterministic summary is returned
- If AI is enabled but unavailable/misconfigured: deterministic fallback is returned
- Core static analysis path remains deterministic and does not require AI

### AI configuration (only if using `--ai`)

Set environment variables:

- `SENTINEL_AI_BASE_URL`
- `SENTINEL_AI_API_KEY`
- `SENTINEL_AI_MODEL`

## Contribution Guide

### Development principles

- Keep modules isolated by responsibility
- Do not move logic across parser/analysis/scoring/reporting/ai/cli boundaries
- Preserve deterministic behavior in core analysis and scoring paths
- Add explicit type hints and production-grade docstrings
- Never swallow exceptions silently

### Local quality checks

```bash
pytest -q
pytest --cov=src/sentinel --cov-report=term-missing --cov-fail-under=85
```

### CI expectations

- Workflow installs project dependencies
- Test suite must pass
- Coverage must remain at or above `85%`

### Pull request checklist

- Keep change scope minimal and intentional
- Include or update tests for behavior changes
- Ensure CLI behavior remains stable unless explicitly changed
- Ensure no unrelated files are modified

## License

Licensed under Apache 2.0. See `LICENSE`.
