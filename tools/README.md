# Export tools

These tools are optional. Opening the report requires no Python or local service.

`build_publication.py` is the read-only export adapter used for this publication.
It requires a separately supplied original research checkout, NumPy,
BeautifulSoup and Plotly (versions are in the dependency manifest). It resolves
the frozen run and its explicit current aggregate/plot pointers, verifies source
hashes, and exports saved results. It never calls an inference endpoint. The
original research checkout and its Python environment are not bundled or needed
for viewing.

`package_publication.py` checks the exported files, repeats checks after copying
them outside the original directory, writes a SHA256 manifest, creates a ZIP,
and verifies the extracted archive. Existing unrelated files are preserved.
It needs NumPy for scientific array validation; the link checker uses only the
standard library.

```sh
cd philosophical_classification
python3 tools/package_publication.py
```

The resulting ZIP is placed alongside this folder. Run this only when intentionally
repackaging: it refreshes publication verification records and the archive, and
does not access the original research data.

The optional [Firefox checker](../analysis/verify_browser.py) uses an already
installed Firefox/geckodriver, a temporary isolated profile and a test control
socket. The reports themselves load directly from disk. No Selenium, new browser
installation or network-based report server is required. Browser evidence from
this export is in [browser_checks.json](../verification/browser_checks.json).
