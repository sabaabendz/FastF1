# F1 Race Strategy Engine

A portfolio project that will estimate tyre degradation and simulate pit strategies to find a fast race plan.

## Current phase

Phase 1 — setup and exploration. See [docs/phase1.md](docs/phase1.md) for scope and decisions.

## Setup

Requires Python 3.11 or newer. From the project root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The first setup step currently uses FastF1, pandas, and Matplotlib. Later phases will add their own dependencies when we reach them.
