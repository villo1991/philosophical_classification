# Offline analysis of published results

Report viewing needs no Python. Optional scripts below use ordinary local Python
3.10+; no original virtual environment, local service, model, training framework
or inference is required.

```sh
cd philosophical_classification
python3 analysis/verify_portability.py
python3 analysis/verify_vectors.py
```

The portability checker uses the standard library. Vector validation needs NumPy;
the research used NumPy 1.26.4. [aggregations.py](aggregations.py) reuses the original
`unit`, `describe`, `validate_vector` and `chapter_descriptor` functions with only
local error-helper/import adaptation. It recomputes means for verification, not
new embeddings. [Dependencies](../provenance/dependencies.json) preserve the
research versions; no packages were installed by the packaging task.

[Chapter metadata](../results/catalog60_8192_v2/chapters.json) binds each vector row
to unit/work/edition IDs and native-window rows. [Windows](../results/catalog60_8192_v2/windows.json)
bind 1,996 native vectors to exact input hashes, core/context spans and ownership.
Work and philosopher metadata bind their row order and constituent indices.
Numeric matrices are NumPy `.npy` files with pickles disabled. Source mappings
are standard gzip-compressed JSON files, readable using `gzip` and `json`.

The saved scatter coordinates, reducer configurations and library versions are
linked from the [plot catalog](../catalog/plots.html). These suffice to inspect
the existing analysis; rerunning the full extraction/inference research requires
the separate source checkout, frozen tokenizer assets and model backend. They
are deliberately not installed or silently downloaded here. Code licensing is
documented in [LICENSE_NOTES.md](../LICENSE_NOTES.md).

The [publication checks](../PUBLICATION_CHECKS.md) describe the actual export
verification. On a system with `sha256sum`, verify file integrity from the
publication root:

```sh
sha256sum -c MANIFEST.sha256
```

Manifest paths are relative to the publication root. Optional Firefox
testing uses [verify_browser.py](verify_browser.py) and an already installed
Firefox/geckodriver; it is not required for viewing the reports.
