# Data format

All JSON and CSV files use UTF-8. Code-point bounds in JSON are decimal integers,
inclusive at both ends. Human-readable reports show hexadecimal `U+` notation.

## Inputs

`catalog/sources.json` contains the Unicode version, survey date, project records,
selection evidence and a list of input records. IDs are unique and stable within
the snapshot. A project has a name, revision, selection policy and upstream
font-license evidence. An input has an ID, URL and kind:

| Kind | Meaning |
| --- | --- |
| `font` | Single TTF or OTF; requires `project` |
| `local-font` | Explicit local licensed or built font; requires `path` and `project`; ordinary refresh reuses locked evidence |
| `zip` / `tar` | Scan every TTF/OTF/TTC/OTC member; requires `project` |
| `ucd` | Vendored UCD input or license; requires `filename` |

`data/inputs.lock.json` associates each input ID and URL with its SHA-256 and
byte size. `retrieved_at` records the UTC lock acquisition time. Ordinary
refreshes check hashes; `--update-lock` accepts input bytes explicitly.

## Font evidence

`data/font-coverage.json` records the Unicode baseline, FontTools version,
measurement method and `fonts` array. Each font contains:

- `id`: source ID, or `source_id::archive/member.ttf` for archive members.
- `source_id`, `project`, `member`: joins to the input and project inventories;
  `member` is null for direct downloads.
- `family`, `style`, `version`: embedded font name-table values.
- `face_index`: collection face number, null for standalone fonts. Face IDs
  append `::face-N`; multiple faces can share a font-container hash.
- `embedded_license`, `embedded_license_url`: font name-table records 13 and 14.
- `sha256`: hash of the font bytes; for archive members, distinct from the
  enclosing archive hash.
- `mapped_count`, `mapped_ranges`: raw scalar cmap evidence, before applying
  Unicode categories or block targets. Ranges use `[[start, end], ...]`.

For a direct input, the font hash equals its locked input hash. An archive
member hash is reproduced by rescanning the locked archive. Original binaries
are deliberately absent from Git.

## Block results

`data/blocks.json` contains a `summary` and an ordered `blocks` array, one row per
UCD block. Each block includes:

- `block`, `start`, `end`: exact block name and inclusive bounds.
- `unicode_version`: Unicode evaluation baseline.
- `first_character_unicode_version`, `last_character_unicode_version`,
  `character_unicode_versions`: UCD Age metadata for characters in this block.
  These do not assert the historical date of the block's definition.
- `assigned_count`, `excluded_assigned_count`, `target_count`: the UCD and
  denominator counts defined in the [methodology](methodology.md).
- `covered_count`, `missing_count`, `status`: surveyed union results.
- `foss_covered_count`, `non_foss_covered_count`, `foss_status`: license-classified
  unions. These can overlap and must not be summed.
- `missing_ranges`: exact target code points not mapped by any surveyed font.
- `missing_by_unicode_version`: missing-target counts grouped by character age.
- `projects`: project ID to mapped-target count and status. Absent projects
  contribute zero. For a block with zero targets, absence means not applicable.
- `fonts`: every font with a nonzero target intersection, its family, count and
  individual coverage status. Sorted by descending count, then font ID.

Counts from different fonts and projects overlap. `covered_count` is the size
of their union, not their sum. `target_count = covered_count + missing_count`.
All block targets, mapped and missing ranges are independent of the host
Python Unicode version.

CSV exports flatten these results. `projects.csv` uses one mapped-target count
column per project. A zero-target row is not applicable regardless of its zeros.
`fonts.csv` has one row per scanned face, including `is_foss`, `non_foss`,
`commercial_use`, `commercial_redistribution`, `modification`, license evidence
and the Unicode evaluation baseline. `blocks.csv` uses semicolons to separate
project IDs and comma-separated `U+` ranges inside properly quoted CSV fields.
The block Markdown and CSV reports omit the repeated evaluation-version column;
the baseline remains in the Markdown header and JSON metadata. Character-age
columns remain in both block reports.

`reports/summary.json` duplicates the summary from `blocks.json`. Its per-project
counts are unions within each project, and its global counts are unions across
all surveyed projects. Never add project totals to reconstruct a global count.

## Original gaps and additional-font research

`data/baseline/` preserves the first survey's font evidence, source selection,
summary and exact missing target set. `data/gap-research.json` records each new
face's intersection with those gaps, unique contributions among added faces,
per-block changes and ranges of identical age and candidate fonts.

`reports/gap-resolution.csv` exports every original missing code point as exact
inclusive ranges. Ranges split on block, character age, candidate list or a hole
in the original missing set. `introduced_unicode_version` is the character's
UCD Age; `unicode_version` is the evaluation baseline. Font IDs join to the
font inventory. Original gap points remain listed even after they are resolved.

`reports/apple-fonts.md` describes the installed platform snapshot and its
contribution to original gaps. `reports/licenses.md` summarizes project terms;
the per-face CSV retains exceptions such as Apple-distributed OFL fonts.
