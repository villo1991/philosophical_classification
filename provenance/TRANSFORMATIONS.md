# Publication transformations

The presentation alias is `catalog60_8192_v2`. The original run identifier is
preserved only where required for scientific lineage, in [lineage.json](lineage.json).
No original research artifact was moved or modified.

- The main HTML/Markdown report is a clearly identified publication derivative,
  combining the completed run report with the relevant chapter-first REPORT.md.
  It adds a searchable work catalog, relative navigation and explicit counts.
- Source/work pages replace the old extraction-review navigation. They include
  all 1,731 accepted units, exact start/end excerpts, canonical spans, acceptance
  status, complete text links, block ledgers and compressed source mappings.
- The 168 MB aggregate JSON repeated source profiles in every unit. Compact,
  normalized metadata replaces those repetitions; original artifact hashes,
  scientific IDs, model/tokenizer identities and saved vector values are retained.
- Chapter vectors are byte-copied. Existing individual work/group/native window
  arrays are collated into explicitly indexed matrices without changing values.
  Inference/download caches, intermediate runs, model weights and environments
  are not part of the publication.
- Twelve selected scatter charts and four heatmaps are exported from the explicit
  plot manifest. One byte-identical shared Plotly bundle replaces redundant inline
  copies. Only outer presentation text/navigation changes; original figure data
  and layouts are checked for equality, and embedded numerical JavaScript is not
  globally rewritten. The upstream library includes generic URL-scheme handling;
  this is not an active local-file or network dependency of these charts.
- Canonical credit-email redaction preserves Unicode character offsets; original
  and derivative hashes are recorded. Primary accepted text is copied unchanged.
  Full unit source maps are compressed, not discarded. No original HTML scripts
  or image dependencies are required for the publication's source views.
- Machine-local paths, usernames, operational contacts and service endpoints are
  omitted from publication derivatives of logs/metadata. Historical test results
  remain labeled historical. No scientific identifier is renamed to claim a new
  experiment. Private original root paths are not publication dependencies.
- Earlier pilots and intermediate visualizations are summarized, not redundantly
  republished. Optional analysis code validates existing arrays only; viewing has
  no Python or model requirement. The complete model-inference installation is
  intentionally outside this static publication.

[Original artifact hashes and derivative map](original_artifacts.json) ·
[Original dependency graph](original_dependency_graph.json) ·
[Preservation checks](../verification/original_preservation.json).
