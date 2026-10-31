# Publication verification

This export uses only saved results. Packaging made **zero embedding requests**,
ran no training and installed no dependencies.

- The exported catalog agrees with the saved matrices: 60 source documents,
  153 edition-level work identities, 35 attribution groups, 1,731 native-unit
  vectors and 1,996 native window vectors, each with 1024 components.
- Shape, finite values, normalization, explicit row IDs, text hashes, window
  ownership, equal-unit work aggregation and both philosopher aggregation methods
  pass fresh offline checks. All 1,731 accepted texts reconstruct exactly from
  their piecewise canonical source mappings. The included/excluded block totals
  are 36,320 / 15,424, with no substantive unresolved blocks under the frozen policy.
- HTML/Markdown links, asset references, JSON publication paths and HTML fragments
  are checked in this folder and in a copy outside the research checkout. All
  sixteen chart files are reachable from the main report. Personal absolute paths
  and contact emails are absent from readable derivatives. The unchanged Plotly
  bundle contains generic protocol-handling strings, not external asset links.
- Firefox 156.0.1 opened the relocated main report, followed report/catalog links,
  filtered the works catalog to both Thoreau works and rendered all twelve
  scatter plots and four cosine heatmaps. Scatter zoom and hover worked. External
  asset loading was blocked through an unreachable browser proxy; no chart
  network-asset requests were recorded. Representative screenshots are linked below.
- Export-time SHA256 checks protected 6,217 original files. Primary texts and
  chapter matrices retain their original bytes. Saved window/work/group values
  are collated without numerical changes. Chart data/layouts are unchanged.
- The ZIP is extracted into a separate temporary directory, checked against
  `MANIFEST.sha256`, and subjected to the same static and scientific checks.

The historical 81-test result and historical GPU/inference measurements are
reported separately; they were not rerun as a new model experiment. Structural
source inspection does not constitute independent human approval. Scientific
interpretation, translated-edition limitations, the blocked genuine ColBERT track
and rights limitations remain explicit in [REPORT.md](REPORT.md) and
[LICENSE_NOTES.md](LICENSE_NOTES.md).

[Detailed checks](verification/index.html) ·
[Main report screenshot](verification/browser/main_report.png) ·
[Catalog screenshot](verification/browser/catalog_filtered.png) ·
[PCA screenshot](verification/browser/chapter_pca.png) ·
[UMAP screenshot](verification/browser/chapter_umap.png) ·
[Work cosine screenshot](verification/browser/work_cosine.png) ·
[Archive checks](verification/archive_checks.json).
