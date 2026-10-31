# Philosophical classification

A self-contained publication of **catalog60_8192_v2**: 60 source documents,
153 edition-level work identities, 35 attribution groups, and 1,731 normalized
1024-dimensional native-unit vectors. No model, Python, internet connection or
local service is needed to view the saved interactive results.

**Start here:** [CORPUS_REPORT.html](CORPUS_REPORT.html) ·
[Work catalog](catalog/works.html) · [All plots](catalog/plots.html) ·
[Full report](REPORT.md) · [Verification](verification/index.html).

[Fresh publication checks](PUBLICATION_CHECKS.md) cover the exported copy, a
relocated copy, all sixteen charts in Firefox and an extracted ZIP. SHA256 file
hashes are provided in `MANIFEST.sha256`.

## Open locally

Clone/download the repository or extract its ZIP. Keep the folder structure.
Double-click `CORPUS_REPORT.html`, or on Linux:

```sh
cd philosophical_classification
xdg-open CORPUS_REPORT.html
```

GitHub's regular file viewer shows HTML source; it does not execute the report
or Plotly charts. Download the files to view them interactively. The report,
catalog search, plots and local source evidence use relative paths and bundled
assets. Optional external source citations do not prevent offline viewing.

## Folder guide

- `CORPUS_REPORT.html`, `REPORT.md`: publication report and complete current scope.
- `catalog/`: searchable works, sources, attribution groups, CSV/JSON and plot index.
- `visualizations/`: twelve saved scatter views, four cosine heatmaps, coordinates,
  reducer parameters and all-row nearest neighbors. All refer to saved data.
- `results/catalog60_8192_v2/`: exact saved native/chapter/work/group vector values
  and explicit row metadata. Native window results are collated scientific arrays,
  not a copied inference cache.
- `texts/`, `sources/`: accepted text, canonical source derivatives, block ledgers,
  profiles and compressed exact source mappings. No raw book scripts/images run.
- `analysis/`: model-free validation and original aggregation functions.
- `assets/`, `notices/`: shared Plotly JavaScript, local styling and rights/credits.
- `provenance/`, `verification/`: original identities, transformations, hashes and checks.

## Scope and limits

60 documents do not mean 60 philosophers. The 35 groups comprise 30 individual
centroid groups, four traditional groups and one joint Marx/Engels group. Work
identities follow the translated items/essays represented by these editions.
Structural source inspection is not independent human approval. Proximity does
not establish philosophical agreement; 2D distances are approximate and chapter
descriptors are lossy. Genuine ColBERT output was unavailable and is not claimed.

## Optional analysis, not model inference

Viewing needs no environment. Optional validation uses a locally installed Python
3.10+ and NumPy; see [analysis instructions](analysis/README.md). The research
pipeline, model weights, virtual environments, download/inference caches,
redundant historical runs and temporary files are intentionally excluded.
This is sufficient to verify the published dense aggregation and saved plots;
it is not a complete model-inference installation.

The publication alias is a presentation name. Scientific IDs, hashes and lineage
remain recorded in [lineage.json](provenance/lineage.json). Private operational
paths and credit email addresses were removed in documented derivatives.

## GitHub upload and optional Pages

Create a new empty repository yourself. Upload **this folder's contents**, keeping
all subdirectories, then commit through GitHub or your own local Git workflow.
Do not upload the ZIP into that repository as a substitute for the folder contents.
No remote repository, push or Pages deployment was created by this packaging task.

For optional GitHub Pages, serve the repository root from your chosen branch.
`index.html` links/redirects to the report and `.nojekyll` keeps these static assets
unchanged. All report links work under a repository subpath. Rights vary by item:
read [LICENSE_NOTES.md](LICENSE_NOTES.md) before public redistribution. No umbrella
license was invented for the existing project code or research outputs.
