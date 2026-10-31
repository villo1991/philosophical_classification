"""Check saved vectors, exact row identities, ownership and aggregation offline."""
from __future__ import annotations
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import sys
import numpy as np


def check(root: Path) -> dict:
    root = root.resolve()
    folder = root / 'results/catalog60_8192_v2'
    def read(path):
        return json.loads(path.read_text())
    def load(name):
        meta = read(folder / (name + '.json'))
        matrix = np.load(folder / meta['matrix_file'], allow_pickle=False)
        assert matrix.shape == (len(meta['rows']), 1024), name + ': shape'
        assert np.isfinite(matrix).all(), name + ': finite'
        norms = np.linalg.norm(matrix.astype(np.float64), axis=1)
        assert np.all(np.abs(norms - 1) < 1e-5), name + ': normalization'
        assert [r['row_index'] for r in meta['rows']] == list(range(len(matrix))), name + ': row order'
        assert len({r['id'] for r in meta['rows']}) == len(matrix), name + ': explicit IDs'
        return meta['rows'], matrix
    chapters, cv = load('chapters')
    windows, nv = load('windows')
    works, wv = load('works')
    group_meta = read(folder / 'philosophers.json')
    groups = group_meta['rows']
    assert [g['row_index'] for g in groups] == list(range(len(groups)))
    def centroid(array, weights=None):
        values = np.average(array.astype(np.float64), axis=0, weights=weights)
        norm = np.linalg.norm(values)
        assert norm > 1e-10
        return values / norm
    errors = []
    seen_windows = []
    ownership_total = 0
    single = 0
    max_error = 0.0
    for row, chapter in enumerate(chapters):
        indices = chapter['window_rows']
        seen_windows.extend(indices)
        assert len(indices) == chapter['windows']
        selected = [windows[j] for j in indices]
        assert [w['id'] for w in selected] == chapter['window_ids']
        assert all(w['unit_id'] == chapter['id'] and w['source_id'] == chapter['source_id'] for w in selected)
        weights = [w['owned_tokens'] for w in selected]
        assert sum(weights) == chapter['unique_chapter_tokens'] == chapter['owned_tokens']
        ownership_total += sum(weights)
        cursor = 0
        for w in selected:
            assert 0 < w['total_input_tokens'] <= 8192
            assert w['core_token_start'] == cursor
            assert w['core_token_end'] - w['core_token_start'] == w['owned_tokens']
            assert w['context_start'] <= w['core_start'] <= w['core_end'] <= w['context_end']
            cursor = w['core_token_end']
        assert cursor == chapter['unique_chapter_tokens']
        if len(indices) == 1:
            single += 1
            assert np.array_equal(cv[row], nv[indices[0]]), chapter['id'] + ': single-window identity'
        else:
            diff = float(np.max(np.abs(centroid(nv[indices], weights) - cv[row])))
            max_error = max(max_error, diff)
            assert diff < 2e-6, chapter['id'] + ': weighted centroid'
        text = (folder / chapter['text_file']).read_bytes()
        assert hashlib.sha256(text).hexdigest() == chapter['cleaned_sha256'], chapter['id'] + ': text hash'
    assert sorted(seen_windows) == list(range(len(windows))), 'window row exactly once'
    seen_units = []
    for row, work in enumerate(works):
        indices = work['chapters']
        seen_units.extend(indices)
        assert all(chapters[j]['work_id'] == work['id'] for j in indices)
        assert len(indices) == work['chapter_count']
        assert dict(Counter(chapters[j]['unit_type'] for j in indices)) == work['unit_types']
        assert np.max(np.abs(centroid(cv[indices]) - wv[row])) < 2e-6
    assert sorted(seen_units) == list(range(len(chapters)))
    for balance, filename in group_meta['matrices'].items():
        matrix = np.load(folder / filename, allow_pickle=False)
        assert matrix.shape == (len(groups), 1024) and np.isfinite(matrix).all()
        assert np.allclose(np.linalg.norm(matrix, axis=1), 1, atol=1e-5)
        for row, group in enumerate(groups):
            indices = group['work_indices'] if balance == 'work-balanced' else group['chapter_indices']
            expected = centroid(wv[indices] if balance == 'work-balanced' else cv[indices])
            assert np.max(np.abs(expected - matrix[row])) < 2e-6
    # Check every cleaned unit against its canonical block mapping. Redactions
    # occur only in front/back credits and do not change canonical offsets.
    mapping_units = 0
    source_blocks = Counter()
    by_id = {u['id']: u for u in chapters}
    for path in sorted((root / 'sources').glob('*/unit_mappings.json.gz')):
        with gzip.open(path, 'rt', encoding='utf-8') as f:
            mappings = json.load(f)
        assert isinstance(mappings, list) and mappings
        canonical = (path.parent / 'canonical.txt').read_text()
        ledger = read(path.parent / 'ledger.json')
        owned_blocks = []
        for item in mappings:
            u = by_id[item['id']]
            text = (folder / u['text_file']).read_text()
            reconstructed = []
            cursor = 0
            for piece in item['mapping']:
                assert piece['clean_start'] == cursor
                value = (canonical[piece['canonical_start']:piece['canonical_end']]
                         if piece['kind'] == 'source_text' else piece['text'])
                assert value == text[piece['clean_start']:piece['clean_end']], item['id'] + ': mapping slice'
                reconstructed.append(value)
                cursor = piece['clean_end']
            assert ''.join(reconstructed) == text and cursor == len(text), item['id'] + ': reconstruction'
            owned_blocks.extend(item['substantive_block_ids'])
        included = [b['block_id'] for b in ledger['blocks'] if b['disposition'] == 'included']
        assert len(set(owned_blocks)) == len(owned_blocks), 'Substantive block duplication'
        assert set(owned_blocks) == set(included), path.parent.name + ': ledger coverage'
        source_blocks.update(b['disposition'] for b in ledger['blocks'])
        mapping_units += len(mappings)
    assert mapping_units == len(chapters)
    return {'status': 'passed', 'source_documents': len(list((root / 'sources').glob('*/canonical.txt'))),
            'native_unit_vectors': len(cv), 'window_vectors': len(nv), 'work_vectors': len(wv),
            'attribution_groups': len(groups), 'dimensions': 1024, 'single_window_units': single,
            'multi_window_units': len(cv) - single, 'unique_owned_tokens': ownership_total,
            'max_centroid_component_error': max_error, 'mapping_files': 60,
            'exact_source_mapping_reconstructions': mapping_units, 'block_dispositions': dict(source_blocks),
            'all_cleaned_text_hashes_match': True, 'row_order_and_ids_verified': True,
            'all_aggregation_levels_verified': True, 'inference_requests': 0, 'errors': errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        result = check(args.root)
    except (AssertionError, ValueError, KeyError, OSError) as exc:
        result = {'status': 'failed', 'error': str(exc), 'inference_requests': 0}
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
