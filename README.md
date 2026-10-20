# Unicode Font Catalog

A research catalog mapping **every Unicode 18.0.0 block** to measured font
coverage, with source links, versions, license conditions and exact missing
code points. It includes FOSS fonts and clearly classified non-FOSS alternatives.

Start with the [block catalog](reports/blocks.md),
[remaining gaps](reports/gaps.md), or
[additional-font research](reports/additional-fonts.md).

## Current findings

The **2026-10-20** expanded survey measures **1,075 font faces in 658 files**
across **15 distributions/builds**. Its union maps **170,026 of 172,369 target
code points (98.64%)**. The FOSS-only union currently reaches the same total;
non-FOSS fonts provide additional alternatives without uniquely closing a gap.

| Unicode block status | Count |
| --- | ---: |
| Complete scalar cmap coverage | 339 |
| Partial coverage | 2 |
| Entirely uncovered | 2 |
| Outside the glyph metric | 10 |
| **Total blocks** | **353** |

Remaining gaps are **Archaic Cuneiform Numerals** (311), **Jurchen Radicals**
(51), part of **Jurchen** (910) and part of **Egyptian Hieroglyphs Extended-A**
(1,071). These are gaps in the surveyed binaries, not proof that no font exists.

The first 271-file survey left **82,534** targets missing. Additional fonts now
resolve **80,191** of them. The original evidence is retained under
[`data/baseline/`](data/baseline/).

| Additional source | Measured result against original gaps |
| --- | --- |
| [Jigmo](https://kamichikoichi.github.io/jigmo/) | Broad CJK extension coverage in its three published CC0 fonts |
| [BabelStone Han](https://www.babelstone.co.uk/Fonts/Han.html) | 27,372 alternative mappings, overlapping Jigmo |
| [Seal Sans](https://github.com/Ghimist/seal-sans) | All 11,328 Seal targets; embedded AGPL v3 declaration |
| [Egyptology Extended](https://github.com/LumabyteCo/egyptology-extended-font) | 2,924 Egyptian Extended-A targets; CeCILL-2.1 |
| [Fairfax HD](https://www.kreativekorp.com/software/fonts/fairfaxhd/) | The remaining 51 Latin Extended-G targets; OFL |
| [Charis 7.000](https://software.sil.org/charis/download/) | Eight measured faces, no original gap filled |
| [Tangut Yinchuan](https://www.babelstone.co.uk/Fonts/Yinchuan.html) | Permitted-use non-FOSS alternative; explicit modification and font-redistribution restrictions |
| [Apple-distributed fonts](reports/apple-fonts.md) | 785 installed macOS 27.0.1 faces; 3,864 original gap targets mapped, overlapping the added FOSS fonts |
| [Typdex Jigmo U18 experiment](experiments/jigmo/README.md) | Three successfully built fonts, 184 added mappings, 151 further original gaps resolved |

The initial Noto script fonts, Noto CJK, Noto Color Emoji, GNU Unifont, DejaVu
and GNU FreeFont remain part of the survey. Contributions overlap; do not add
font totals to obtain the union.

## Unicode versions and licenses

The reports include a **Unicode evaluation-version column**. Character-level
gap ranges also include **the Unicode version in which each character was
introduced**, taken from `DerivedAge.txt`. Block rows give the earliest/latest
character ages within their bounds. A font's embedded release version is a
separate field; none of these columns claims that a font implements an entire
Unicode release.

The [font CSV](reports/fonts.csv) includes **non-FOSS**, **commercial use**,
**commercial font redistribution**, and **modification** columns. Commercial
document use and selling or redistributing a font file are distinct permissions.
See the [license table](reports/licenses.md) for the recorded conditions.

Coverage means scalar `cmap` mappings, not verified shaping or glyph correctness.
The denominator excludes unassigned slots, controls, formats, surrogates,
private-use characters and default-ignorables. Read the
[methodology](docs/methodology.md) before interpreting results.

## Browse and query

| Artifact | Contents |
| --- | --- |
| [Block catalog](reports/blocks.md) | Every block, Unicode versions, FOSS/non-FOSS coverage and font candidates |
| [Gap report](reports/gaps.md) | Remaining uncovered and partial blocks |
| [Additional-font results](reports/additional-fonts.md) | Measured improvements against the original gaps |
| [Gap-resolution CSV](reports/gap-resolution.csv) | Exact original gap ranges, character ages and matching fonts |
| [Apple report](reports/apple-fonts.md) | Installed snapshot, measured versions and coverage contribution |
| [License table](reports/licenses.md) | FOSS classification and commercial-use conditions |
| [Font inventory](reports/fonts.csv) | Every face, version, license, source, collection index and hash |
| [Block CSV](reports/blocks.csv) / [project matrix](reports/projects.csv) | Reusable block and project comparisons |
| [Full results](data/blocks.json) / [gap research](data/gap-research.json) | All matching fonts and exact range-level evidence |
| [Summary](reports/summary.json) | Overall, FOSS-only and per-project statistics |
| [Source inventory](catalog/sources.json) / [input lock](data/inputs.lock.json) | Selection policies, licenses, pinned inputs and hashes |

With Python **3.9+**, query the committed snapshot without installing fonts:

```sh
python3 scripts/query.py --block "Jurchen"
python3 scripts/query.py --codepoint U+18D80 --limit 0
python3 scripts/query.py --codepoint U+13460 --limit 0
```

## Reproduce

Regenerate the reports offline using Python's standard library:

```sh
python3 scripts/build_catalog.py
python3 scripts/build_catalog.py --check
```

Remeasure the public locked downloads and run tests:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/refresh.py
python3 scripts/build_catalog.py --check
.venv/bin/python -m unittest discover -s tests -v
```

Ordinary refreshes preserve the committed evidence for explicit local inputs,
including Apple fonts and experimental builds. They do not require proprietary
binaries or a Mac. To remeasure the installed Apple snapshot:

```sh
.venv/bin/python scripts/refresh.py --rescan-local --local-project apple-macos
```

Changed bytes fail the lock check. Accept intentional changes with
`--update-lock`, then regenerate and review the reports. Downloaded archives,
font binaries, virtual environments and caches are excluded from Git.

The [Jigmo experiment](experiments/jigmo/README.md) includes its build program,
locked SVG inputs, manifest, verification and glyph proof. It is a **partial
experimental Unicode 18 East Asian update**, not a complete Unicode 18 font.
The remote fork is pending GitHub authentication; the local `unicode-18` branch
and a portable patch are prepared.

See [contribution instructions](CONTRIBUTING.md), the
[data format](docs/data-format.md), and [research notes](docs/research-notes.md).

## Licensing

Original code and documentation use [MIT](LICENSE). Unicode data retains the
[Unicode License](data/ucd/LICENSE.txt). Font binaries retain their upstream
terms; the catalog's license does not replace them. GlyphWiki experiment inputs
retain their [data license](experiments/jigmo/GLYPHWIKI-DATA-LICENSE.txt), and the
published Jigmo base uses [CC0](experiments/jigmo/JIGMO-CC0-LICENSE.txt).
