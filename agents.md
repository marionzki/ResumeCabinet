# Agent / contributor guide (ResumeCabinet)

Audience: humans and IDE agents working on this repository.

## Product context

- **Desktop CV editor** built with **Flet** (Python).
- **Portable mode**: all application state lives under a single tree pointed to by `RESUMECABINET_DATA_ROOT` (default: `./data` next to the executable or project root).
- **Multiple profiles** under `data/users/<user_key>/`; **shared global library** (Competencias / Software / Lenguajes tabs) under `data/global/`.
- **UI language**: Spanish where user-facing strings exist in the repo. **Code identifiers and block comments**: English unless they mirror short UI copy.

## Authoritative specs

1. **`spec.md`** — system contract (portable layout, persistence, library merging, templates, media paths). Extend or amend it **before** changing behaviour that affects users or on-disk formats.
2. **`README.md`** — setup, build, and distribution story for humans.

## Engineering rules

- **Do not** ship read-only “bundled” CV templates inside the executable. Example JSON lives in `defaults/example_templates/` in the repo and is copied into `data/defaults/example_templates/` at runtime or by `tools/prepare_distribution_data.py`.
- **Canonical portable build** (Windows): `build_portable.bat` → `ResumeCabinet.spec` + `python tools/prepare_distribution_data.py` (produces `dist/ResumeCabinet.exe` + `dist/data/`).
- **Additive global library merges** must not resurrect deleted modules: `library.json` is written from current in-memory CV (see controller `save_autosave`).
- **Applying a CV template** must not remove user-created modules (merge rules in `_merge_template_into_current_cv`).
- Prefer **focused diffs**: avoid drive-by refactors unrelated to the task.

## Recommended workflow (SDD / TDD)

1. Read the relevant sections of **`spec.md`** (and **`README.md`** if build/distribution-related).
2. Add or tighten a **`pytest`** that encodes the expected behaviour (`tests/`). Run `python -m pytest`.
3. Implement the smallest change that makes tests and app behaviour match the spec.
4. Update **`spec.md`** acceptance criteria when the contract changes.

## Commands

```bash
pip install -r requirements-dev.txt    # runtime + pytest
python main_flet.py                     # development run
python -m pytest                        # automated tests
build_portable.bat                      # Windows exe + dist\data seed (after PyInstaller installed)
```

## High-churn modules

| Area | Location |
|------|----------|
| Persistence, profiles, library, templates | [`controller/flet_controller.py`](controller/flet_controller.py) |
| Portable path helpers | [`utils/asset_paths.py`](utils/asset_paths.py) |
| Seed PNGs / example templates on disk | [`utils/portable_media_bootstrap.py`](utils/portable_media_bootstrap.py) |
| Domain model | [`model/cv_data.py`](model/cv_data.py), [`model/modules.py`](model/modules.py) |

## Out of scope (unless spec changes)

Cloud sync, multi-user realtime collaboration, non-Windows packaging (may work but unsupported in docs).
