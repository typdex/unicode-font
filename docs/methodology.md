# Research method

## Question and scope

For each named Unicode block, which surveyed font binaries map its characters,
which are FOSS, and which target code points remain unmapped by their unions?

This is a reproducible **scalar cmap survey**, not a claim of universal text rendering
or an exhaustive census of every font. “Popular” is a curated starting scope,
not a measured popularity ranking. Noto, GNU Unifont, DejaVu and GNU FreeFont were
chosen as established, freely licensed projects with broad or complementary
repertoires. Each project’s exact selection, revision and upstream license evidence
is in [sources.json](../catalog/sources.json). Noto script fonts, CJK and Emoji are
tracked separately because they have separate distributions.

The expanded survey includes specialist FOSS fonts, restricted-use fonts such as
Tangut Yinchuan, an installed Apple-distributed font snapshot, and an experimental
Jigmo build. FOSS and non-FOSS coverage are reported separately. A freely
downloadable font need not permit modification or font resale. Commercial use
of a rendered document, commercial redistribution of the font binary and
modification have separate fields; the recorded upstream conditions remain
attached to each font. Apple distributions include some OFL fonts, classified
per face from their explicit embedded grants.

The Unicode baseline is **18.0.0**. All block boundaries and categories come from
the versioned UCD, never from the Python interpreter’s built-in Unicode version.
`DerivedAge.txt` supplies the version in which each character was introduced.
Every block row includes the evaluation `unicode_version` and the earliest and
latest character ages within its bounds. These are character ages, not a claim
about the historical date when the block itself was defined. Gap-resolution
ranges split whenever the character age or font candidates change.
The [Unicode release page](https://www.unicode.org/versions/Unicode18.0.0/) was
consulted on 2026-10-20; it still displayed some preliminary-draft notices.
The actual downloaded inputs are the versioned 18.0.0 files, identified by URL
and SHA-256 in the lock. The results describe these bytes even if upstream
documentation changes later.

## Denominator

1. Enumerate every record in `Blocks.txt`, including supplementary planes.
2. Read `UnicodeData.txt`, expanding `First` / `Last` ranges for CJK, Hangul,
   private-use and surrogate categories.
3. Include categories **L, M, N, P, S and Zs**: letters, marks, numbers,
   punctuation, symbols and space separators.
4. Exclude `Default_Ignorable_Code_Point` from `DerivedCoreProperties.txt`.

Unassigned positions (`Cn`), controls (`Cc`), formats (`Cf`), surrogates (`Cs`),
private-use (`Co`), line/paragraph separators (`Zl`, `Zp`) and noncharacters
are outside the target metric. Space separators remain included: they require
spacing behavior even when their outlines are blank. Combining marks remain
included; some can also be produced by shaping without a direct scalar mapping.

`assigned_count` means code points represented in UnicodeData with a non-Cn
category, including Co and Cs. It is not the Unicode Standard’s count of encoded
abstract characters. `excluded_assigned_count` is that count minus target count.
Unused block slots never enlarge the coverage denominator. Code points outside
named blocks are not a separate block.

Default-ignorables include variation selectors, tag characters and certain
fillers. An entire block with zero targets is **not-applicable**, not uncovered.
This does not say those characters are unnecessary for text processing.

## Numerator and provenance

For each selected TTF/OTF file and each TTC/OTC collection face, FontTools reads
every Unicode cmap subtable.
Their scalar mappings are unioned, discarding mappings to glyph ID zero
(`.notdef`) and values outside Unicode scalar space. Format 14 variation-sequence
records are deliberately excluded. Font files within release ZIP/TAR archives
are read without extracting or installing them. Each member has its own SHA-256.
Collection faces share the container hash and have distinct face indexes.
`font_files` counts containers; `font_faces` counts individually scanned faces.

`font-coverage.json` stores exact compact ranges of mapped scalars, family,
style and version strings, source IDs, archive member names, file hashes and
the FontTools version. `inputs.lock.json` records upstream byte hashes and
retrieval time. The version embedded in a font may differ from a release tag;
both are preserved. Repository commit URLs pin Noto artifacts; release URLs plus
hashes pin other inputs. Hashes establish reproducibility, not publisher authenticity
or independent signature verification.

A font contributes only its mappings intersected with a block’s targets.
Project coverage is a union across surveyed files of that project. Block-wide
coverage is a union across all surveyed projects:

| Status | Definition |
| --- | --- |
| complete | At least one target; every target mapped by the surveyed union |
| partial | Some targets mapped, some missing |
| uncovered | Targets exist, zero targets mapped |
| not-applicable | Zero targets under this metric |

One complete block does not necessarily have a single complete font. Every
per-font hit in `blocks.json` includes its own count and status. Project coverage
counts can overlap and must not be added to obtain the global union.
The same applies to FOSS and non-FOSS unions: their mapped targets overlap.
The original survey and gap set are retained under `data/baseline/`; additions
are evaluated against this fixed set, with removal or replacement of an
original font treated as an invalid comparison.

## What the measurement does not establish

- OpenType shaping, mark positioning, language-specific glyph selection,
  bidi behavior, fallback quality or readability. GNU Unifont’s own
  [limitations](https://unifoundry.com/unifont/index.html) describe its lack of
  contextual forms for complex scripts.
- Correct outlines. A nonzero cmap entry may still be blank, a diagnostic box,
  a placeholder or the wrong glyph. There is no automatic outline audit here.
- Emoji ZWJ sequences, flags, skin-tone composition, standardized variation
  sequences, ideographic variation sequences or color-renderer compatibility.
- Coverage of other weights, variable-only fonts, development sources,
  alternative Unifont formats or omitted families. The explicit Noto omissions
  are recorded under `selection_evidence` in `sources.json`.
- Absence of fonts outside this survey. Gaps are research leads, not proofs
  that no FOSS font exists.

## Follow-up research

Prioritize wholly uncovered blocks, then partial blocks by missing-target count.
See the [additional-font results](../reports/additional-fonts.md) and
[research notes](research-notes.md) for measured additions and remaining leads.
Separate license
verification, binary cmap measurement, outline review, shaping tests and native
reader review into recorded evidence stages. A good follow-up adds exact font
bytes and reruns the union rather than inferring support from a family name.

## Reproducibility

The offline builder verifies committed UCD hashes and inventory consistency,
then deterministically regenerates JSON, CSV and Markdown. `--check` fails when
any generated output differs. The network refresh validates all downloaded
inputs against the lock and fails instead of treating missing inputs as zero
coverage. Local platform fonts are a separate, explicit inventory; the refresh
does not discover arbitrary installed user fonts.

Ordinary refreshes preserve locked local-font evidence so they can run on Linux
without proprietary binaries. `--rescan-local` explicitly remeasures those
files and checks the input lock. The Apple snapshot covers installed files under
`/System/Library/Fonts`, including Supplemental, from macOS 27.0.1 build 26A434.
It excludes LastResort, whose diagnostic mappings are not actual character
outlines. Neither proprietary font bytes nor private user font folders are
committed or uploaded.

The first acquisition used `refresh.py --update-lock`; subsequent ordinary
refreshes reject changed bytes. The ignored `.cache/` is keyed by URL. To
intentionally refetch a mutable URL, delete its cache entry (or `.cache/`) before
accepting an update. An update command can reuse cached bytes; it is not an
automatic latest-release discovery process.
