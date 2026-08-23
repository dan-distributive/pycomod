# pycomod

A multi-fleet pilot workforce model built on [pycomod](https://github.com/DRDC-RDDC/OS_PyCoMod) (Events branch), run as a Monte Carlo simulation across [DCP](https://distributed.computer/) — each repetition dispatched as one job slice.

## Layout

- `MultiFleet.py` / `MultiFleet.ipynb` — the model (training/OTU delays + MEAD experience model per aircraft fleet) and the DCP job dispatch/plotting pipeline. Same logic, script vs. notebook.
- `OS_PyCoMod_Events/` — a local copy of `pycomod`, shipped to DCP workers via `job.fs.add(...)` since it isn't a published package.

## Setup

```
pip install dcp numpy pandas matplotlib
```
Also requires [Node.js](https://nodejs.org/en/download) and a DCP identity/wallet (keystore in `~/.dcp`, or set explicitly in the script).

## Running

```
python3 MultiFleet.py
```
or open `MultiFleet.ipynb`. Both dispatch a Monte Carlo job (`reps` repetitions) via `dcp.compute_for`, wait for results, then plot per-fleet training/experience/NOP series.

## Changes made to `pycomod` for DCP workers

`OS_PyCoMod_Events/pycomod` is a general-purpose local library — used both here (once as the model builder inside the DCP work function, running in an isolated worker sandbox with no filesystem/GUI access, and once client-side for plotting) and elsewhere as an ordinary Python package. Two things needed fixing so the *same* package works in both contexts without maintaining a separate sandbox-only fork:

1. **Lazy `Plotter` import** (`pycomod/__init__.py`). The package used to `from .plotter import Plotter` unconditionally, which pulls in `matplotlib` at `import pycomod` time — something DCP worker sandboxes don't have and don't need (workers only ever touch `Model`). Now `Plotter` is resolved lazily via a module-level `__getattr__` (PEP 562), so `import pycomod` never touches `matplotlib`; it's only imported, and can only fail, the moment client-side code actually does `pycomod.Plotter(...)`.

2. **Sandbox-safe progress reporting** (`pycomod/model.py`). `dcp.progress()` only exists inside an actual DCP worker — the client SDK's `dcp` module doesn't define it until `dcp.init()` runs, and even then it's a different, worker-injected implementation. `Model._run()`'s per-timestep loop now detects `dcp.progress` availability once at import time (`hasattr` check, falling back to a no-op if `dcp` isn't installed or doesn't expose it) instead of calling it unconditionally — so a plain local/interactive model run doesn't crash, while a real worker still reports progress every 10%.

## Output size

By default `pycomod` tracks every pool/flow/parameter/equation in a model for output — for this model that meant ~60x more data coming back per job slice than what's actually plotted. `MultiFleet.py`/`MultiFleet.ipynb` restrict this per-submodel via `set_output(...)` (called after construction — calling it inside a model's own `build()` doesn't stick, since `Model.__init__` resets tracked output right after `build()` returns), drop a redundant per-element `dates` array (derivable from `times` + a shared start date), and downcast to `float32`. Together these cut per-slice output from ~63 MB to a couple MB for the same run.
