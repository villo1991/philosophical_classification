# Completed philosophical corpus · catalog60_8192_v2

This is the publication edition of the completed corpus report, derived from the
actual full-corpus report and the chapter-first report. Original report hashes
and presentation changes are in [provenance](provenance/TRANSFORMATIONS.md).

| Object | Completed count |
|---|---:|
| Source documents / selected editions | 60 |
| Edition-level work identities | 153 |
| Attribution groups | 35 |
| Individual centroid groups | 30 |
| Traditional / joint groups | 4 / 1 |
| Final native-unit vectors | 1,731 × 1024 |
| Input windows / unique owned tokens | 1,996 / 5,214,383 |
| Single-window / multi-window units | 1,560 / 171 |
| Newly inferred / reused windows | 1,828 / 168 |
| Failed requests | 0 |

Browse the [153-work catalog](catalog/works.html), [60-source inventory](catalog/sources.html),
[attribution groups](catalog/attributions.html), [CSV](catalog/works.csv) and
[interactive report](CORPUS_REPORT.html). Work records expose original author or
tradition, translator, edition observations, source document, unit types/counts
and source/result links. Unknown dates remain unknown; composition, translation,
print-edition and digital-release dates are distinct.

The native-unit breakdown is 622 chapters, 702 sections, 182 aphorisms, 94 essays,
61 Books, 24 letters, 23 lectures, 12 Parts, 9 whole-work units, 1 poem and 1
prologue. “Chapter” in the aggregation label includes these native analysis units;
the unit types remain explicit in the catalog and row metadata.

## Completed full-corpus run versus history

The full accepted catalog completed in 571.964 seconds of inference/checkpointing,
excluding source inspection and token planning. Actual in-flight RTX 4060 samples
reached 100% utilization, 1,194 MiB model-process VRAM and 1,263 MiB total VRAM.
CPU layer offload was not quantified by the empty process table; host allocations
do not establish CPU-only execution. No embedding inference or training occurred
during publication packaging. The historical three-source 146-vector run is a
separate earlier result; its 146 vectors were verified bit-for-bit unchanged.

All 60 requested documents have represented accepted units under the recorded
inclusion policy. The original report records no unresolved substantive body
blocks: 36,320 included and 15,424 excluded blocks. This is source-checked structural
acceptance, not independent human approval or a semantic stance benchmark.

## Extraction and edition policy

57 new source-specific profiles share one range engine; the original three profiles
remain frozen. Guards pin original HTML hashes, parser identities, actual headings,
containers, contents destinations and work ranges. Chapters, Books, Parts, sections,
aphorisms, essays, letters, lectures and whole-work units remain distinguishable.
Parents and children are not duplicated as full primary inputs. In flat Critique
of Pure Reason markup the analysis uses exclusive source-heading sections with
their own prose. The lecture family includes James's native Postscript.

New profiles include author argument, verse, integral author appendices, scholia
and introductions within works. Standalone front prefaces/dedications and later
editorial introductions, translator notes/summaries, contents, pagination and
publisher matter are excluded from embedding inputs and retained separately.
Legacy profiles retain their historical appendix policy so previous vectors are
not silently changed. A dialogue speaker is not automatically its author or an
endorsed position. Notes are removed without fragmenting continuous paragraphs.

Edition limits are explicit: 51 native Epictetus headings; 81 Laozi sections;
130+52 Novum Organum aphorisms rather than internal Roman lists; only Analects
Books I–XX despite the title's wider advertised collection; three Machiavelli works;
translator-reported omissions of Gita concluding shlokas; a separate L. A. Magnus
credit for Nietzsche's closing poem. Complete installed-edition coverage does not
claim completeness of every original recension. Source texts and credits remain
traceable through each catalog source page.

## Dense algorithm and original-space geometry

BGE-M3 is frozen. Its verified limit is 8192 **total** tokens including special
tokens/headings: context=8192, physical token batch=8192, one text/request,
truncate=false. Inputs use the pinned tokenizer/adapter, not character counts.
Fitting units use one complete native embedding; only oversized units split,
with 256-token overlap and complete unique ownership. No generated summaries or
metadata prefixes replace source text.

One-window descriptors retain the native vector. Multiple windows use
`normalize(sum(unique_owned_tokens_i * window_vector_i) / sum(unique_owned_tokens_i))`.
Ownership removes duplicate weights, not residual contextual influence from overlap.
Work vectors use equal unit weights. Philosopher **work-balanced** vectors give
equal weight to work centroids; **chapter-balanced** vectors give equal weight to
accepted native units across works. Chapter-balanced is not idea-balanced.
Joint authorship and traditional groups remain explicit. All means are calculated
and normalized in original 1024D space before projection.

The chapter matrix is 1,731 × 1024. Cosine similarities use original normalized
vectors. PCA/UMAP/t-SNE produce approximate 2D views; independently fitted levels
are not overlaid. Chapter PCA explains **13.2128%** in two components, work PCA
17.0952%, philosopher work-balanced PCA 30.5294%, and chapter-balanced PCA 30.7928%.
Seeds, installed versions, parameters and exact coordinates are included per plot.
Chapter heatmaps use a deterministic 120-row subset; work/group heatmaps use all
153/35 vectors. All-row nearest neighbors use bounded 128×N score blocks.

## Results and checks

[All twelve scatter views and four cosine heatmaps](catalog/plots.html) include
the complete selected level. [Saved matrices and explicit row metadata](results/catalog60_8192_v2/chapters.json)
are aligned by IDs. [Analysis instructions](analysis/README.md) reproduce the
aggregation checks without model inference. All native window representations
and ownership weights are included for the transparent dense baseline.

Historical verification records 81 passing HTML tests, real short DOM fixtures,
source/window reconstruction, cache invalidation, interruption/resume, zero new
requests on completed restart, original-vector preservation and GPU measurements.
Fresh publication checks and actual browser outcomes are in the
[verification index](verification/index.html). Packaging checks are distinct from
historical model experiments. No genuine ColBERT inference was available; none
is claimed. No training was performed. Geometric proximity may reflect topic,
style, translation and length, and does not prove philosophical agreement.
