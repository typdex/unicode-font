# Contributing research

Start by reading [methodology](docs/methodology.md). Useful contributions add
auditable evidence for a coverage gap, correct a license record, or validate
rendering behavior for a script with an appropriate shaping engine.

To add a surveyed font:

1. Add its project record and input to `catalog/sources.json`. Include an
   authoritative homepage, immutable commit or release, font-license evidence
   and an explicit selection policy. Open repositories alone do not establish
   that their fonts have a free license. Set `is_foss`, `commercial_use`,
   `commercial_redistribution` and `modification` explicitly. Restricted fonts
   are welcome as clearly classified research entries; do not replace their
   conditions with a blanket “commercial allowed” label.
2. Use `kind: font` for a TTF/OTF/TTC/OTC, `zip` or `tar` for an archive of fonts.
   Archives include every supported font member; make that scope explicit.
   WOFF and source-font formats are not yet scanned. `local-font` inputs can
   describe licensed system fonts or experimental builds without redistributing
   their binaries. Use `--rescan-local` when first locking those inputs.
3. Run `.venv/bin/python scripts/refresh.py --update-lock` to explicitly accept
   the new source bytes. Normal refreshes require existing lock entries.
4. Run `python3 scripts/build_catalog.py`, review the changed counts and exact
   missing ranges, and run the verification commands in the README.
5. Explain which gap the contribution addresses, whether the fonts were
   visually reviewed, and any shaping or locale restrictions. Never mark a
   cmap result as validated typography without additional evidence.

To change the Unicode baseline, update all four versioned UCD URLs and the
`unicode_version` field together, retain Unicode’s license, refresh the lock,
and explain the repertoire changes. A new Unicode baseline also needs an
explicit replacement/comparison policy for `data/baseline/`; the current
gap-research comparison requires the same Unicode repertoire. Update `survey_date` when performing a
new survey. Generated reports must be committed with their evidence.

Do not commit font binaries, downloaded archives, virtual environments or cache
files. Upstream licenses remain authoritative. Original code and documentation
use the MIT license; vendored Unicode data retains its own license.
