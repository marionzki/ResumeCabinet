# ResumeCabinet — Technical / product specification

Version: maintained alongside the codebase. User-facing onboarding remains in [`README.md`](README.md).

## 1. Scope & non-goals

**In scope**

- Offline editing of structured CV content, PDF preview/export.
- Portable folder layout beside the executable or dev project root.
- Multiple named profiles (“full name”) with isolated profile JSON and user templates.

**Explicit non-goals (current phase)**

- Network sync, authenticated cloud storage, concurrent multi-device editing.

## 2. Portable data model

**Root**

Environment variable **`RESUMECABINET_DATA_ROOT`** (optional). When unset during development/fallback paths, resolver may use `%APPDATA%/ResumeCabinet` for legacy behaviours inside specific helpers — the **preferred** portable root is `./data` under the directory containing `ResumeCabinet.exe` or the cloned repository.

**Directories (normative)**

| Path | Purpose |
|------|---------|
| `global/library.json` | Shared sections: Competencias (`knowledge`), Software (`software`), Languages (`languages`) |
| `global/software/` | PNG pool for Software tab |
| `global/languages/` | PNG pool for Languages tab |
| `defaults/example_templates/` | Source JSON shipped with the product (seed only; not user-editable “bundle”) |
| `defaults/avatars/` | Seed portrait PNGs copied into a user avatar folder when empty |
| `defaults/initial_profile.json`, `defaults/initial_library.json` | Factory seeds |
| `users/<user_key>/user_data.json` | Profile-local CV payload (everything except shared library slices) |
| `users/<user_key>/templates/*.json` | CV templates visible in Templates tab (**all deletable**) |
| `users/<user_key>/avatar/` | Profile avatars |

**User key**: derived from trimmed display name: lowercased spaces→underscores, alphanumeric + `_`/`-`; empty → fallback key.

## 3. Persistence rules

### 3.1 Load

- Profile JSON + `global/library.json` compose the in-memory `CVData`.
- If `library.json` is missing, bootstrap from defaults seed (`defaults/initial_library.json` analogue).
- Loading must **not** silently merge seed library onto an existing disk library in a way that undoes explicit deletions documented in changelog (current behaviour writes library from composed state at save boundaries — see README).

### 3.2 Save

- `user_data.json` persists profile payload (settings, header, personal, experience, education).
- **`global/library.json` is rewritten from `_library_payload_from_cv(cv_data)`** — no additive merge with the previous global file snapshot (prevents deleted shared entries from reappearing).

## 4. Global library semantics

### 4.1 Canonical duplicate keys

- **Knowledge (`generic` section, TextModule)** key: lowercase trimmed **title**.
- **Software / Language (ImageModule)** key: lowercase trimmed **name**.
- Fallback to module `id` when title/name empty (`*_fallback`, `other` tuples — see `_canonical_library_item_key`).

### 4.2 User operations

- **Add** with cancelled editor: module must **not** be appended until **Save** in the modal (pending-new flow).
- **Delete** Competencia / Software / Language: confirm dialog warns **all profiles**.
- Imports from another profile extend library **without duplicates** by canonical key.

### 4.3 Templates vs library

Applying a `.json` **CV template**:

- Replace **settings** + **header_info** from file.
- For **knowledge, software, languages, experience, education, personal_info**: **merge**.
  - Never drop modules present only locally.
  - For modules matched by canonical merge keys: keep local content fields; **`is_active` taken from template**.

## 5. Templates tab behaviour

**Discovery**: only `*.json` under **`users/<user_key>/templates/`**.

**Initial examples**: When that folder contains **zero** `.json`, copy everything from **`data/defaults/example_templates/`** once (typically at profile creation or first-time migration). After the user deletes all templates, folder stays empty intentionally until they save new ones — **do not auto-reseed** on every startup.

**Build-time**: Running `tools/prepare_distribution_data.py` after PyInstaller fills `dist/data/defaults/example_templates/` from the repository’s `defaults/example_templates/`.

## 6. Media path references

**Stable relative references**

- `global/software/...`, `global/languages/...`
- `users/<user_key>/avatar/...`
- Legacy passes through: `images/...`, `user/...` (under `data/assets`)

**Behaviour**

- Editors pick folders per section (software/language/avatar buckets).
- `resolve_asset_path` probes storage root → external assets bundle → packaged runtime directories.

Implementation: [`utils/asset_paths.py`](utils/asset_paths.py).

## 7. Acceptance criteria (testable)

Tracked at high level — mirror with tests where practical (`tests/`).

1. **`AC-PATH-NORM`**: A file living under storage root resolves from a `global/software/rel.png` logical path (see `test_resolve_asset_path_finds_file_under_storage_root`).
2. **`AC-MEDIA-PREFIX`**: `is_storage_managed_media_ref` distinguishes global and avatar prefixes from generic strings.
3. **`AC-LIB-KEY`**: Two ImageModules with identical name differing only by case collide on canonical key (`test_canonical_duplicate_name_same_key_language_section`).
4. **`AC-SEED-IDEMPOTENT`**: Running `seed_defaults_example_templates_into_storage` twice never overwrites destination JSON (`test_seed_defaults_example_templates_idempotent`).
5. **`AC-USER-TPL-EMPTY`**: `seed_user_templates_folder_if_empty` copies examples only when the user templates directory has zero `.json` (`test_seed_user_templates_only_when_folder_has_no_json`).
6. **`AC-LANG-STEMS`**: language logo filenames in `LANGUAGE_LOGO_STEMS` classify Python/C#/… family for filesystem organisation (`LANGUAGE_LOGO_STEMS` assertions).

Higher-level behavioural tests (profile switch, autosave orchestration without UI) belong in future work with heavier mocking.
