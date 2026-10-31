# Philosophical Classification
An exploratory project evaluating how BGE-M3 semantic embeddings represent philosophical texts and capture similarities and differences among philosophers.

## Explore the results
Open [CORPUS_REPORT.html](CORPUS_REPORT.html) to browse the searchable catalog, interactive visualizations, and supporting results.

Download and extract the complete repository before opening the report. Preserve its directory structure so that relative links continue to work.

The report and charts work offline, with bundled Plotly assets. GitHub's regular file viewer displays HTML source rather than the interactive report.

For methodology, verification details, and limitations, see [REPORT.md](REPORT.md).

## Corpus and outputs
| Item | Count |
|---|---:|
| Source documents | 60 |
| Work identities | 153 |
| Attribution groups | 35 |
| Final textual-unit vectors | 1,731 |
| Window vectors | 1,996 |
| Interactive scatter plots | 12 |
| Cosine-similarity heatmaps | 4 |

Source documents, works, and attribution groups are distinct categories. A document may contain multiple works, and an attribution group may represent an individual philosopher, joint authorship, or a tradition.

The package includes source texts, vector mappings, provenance records, validation code, dependency documentation, and redistribution notices.

## Project goal

The project generates 1024-dimensional embeddings using BGE-M3, with a maximum input context of 8,192 tokens. PCA, UMAP, and t-SNE provide complementary two-dimensional visualizations.

The analysis explores four levels of representation:

1. **Chapters and other textual units**  
   Individual chapters, books, essays, or dialogues reveal variation within and across works.

2. **Works**  
   Each work is represented by the L2-normalized mean of its constituent unit vectors.

3. **Philosophers — work-balanced**  
   Each philosopher is represented by the L2-normalized mean of their work vectors, giving every work equal weight.

4. **Philosophers — chapter-balanced**  
   Each philosopher is represented by the L2-normalized mean of all their textual unit vectors. Each unit receives equal weight, so works containing more units contribute more strongly.

“Chapter-balanced” refers to the extracted textual units, which are not always chapters. It does not mean weighting chapters by their length or giving equal weight to individual ideas.

## Handling long units

Units that fit within the model's context limit receive a single embedding. Longer units are divided into windows with a 256-token overlap.

Window embeddings are combined using a weighted mean. Each window's weight is the number of unique source tokens assigned to it. The resulting vector is then L2-normalized.

Overlapping tokens are not counted twice in the weights, although they still influence the contextual embeddings.

This token-based weighting applies within oversized units. It is separate from work-balanced and chapter-balanced aggregation.

## Reading the visualizations

- **PCA** provides a linear projection that preserves as much variance as possible in two dimensions.
- **UMAP** emphasizes neighborhood relationships.
- **t-SNE** emphasizes local neighborhoods; distances between separated groups require caution.
- **Cosine heatmaps** compare vectors in the original 1024-dimensional space.

The twelve scatter plots cover the four representation levels using all three projection methods. Four heatmaps show the corresponding original-space cosine similarities.

Two-dimensional projections lose information. Nearby points may reflect shared topics, vocabulary, translation style, or philosophical content; they do not necessarily indicate philosophical agreement.

## Validation

The packaging verification report records successful checks for:

- Internal links, assets, and fragment identifiers.
- Vector alignment and aggregation.
- Reconstruction of all included source texts.
- Portability after relocating the folder and extracting the ZIP archive.
- Offline rendering of all 16 charts in Firefox, including navigation, filtering, hover, and zoom.

Hash checks confirmed that 6,217 original files remained unchanged. No new model inference or training was performed during packaging.

These checks establish technical consistency and portability. They do not constitute independent validation of philosophical interpretation or every segmentation decision.

## Package size
- Unpacked: approximately **109.5 MB**.
- ZIP archive: approximately **43.2 MB**.
- Largest individual file: the **8.2 MB window-vector matrix**.

## Scope and limitations

This release presents BGE-M3 dense embeddings. It does not include genuine ColBERT multi-vector inference results.
Aggregation produces compact, lossy representations. Results depend on corpus selection, editions, translations, segmentation, and weighting choices.
Source inspection performed by a coding assistant is not independent human approval. The project supports exploratory research rather than a definitive classification of philosophers.

## Rights and redistribution
Consult the included redistribution notices before reusing source texts, code, or third-party assets. Different materials may have different terms; no blanket license is claimed for the entire package.

Consult the included redistribution notices before reusing source texts, code, or third-party assets. Different materials may have different terms; no blanket license is claimed for the entire package.
