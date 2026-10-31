"""Verify, relocate and ZIP the publication; no inference or original checkout required."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import zipfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'analysis'))
from verify_portability import check as check_links
from verify_vectors import check as check_vectors


def save(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def files(root):
    paths = sorted(p for p in root.rglob('*') if p.is_file())
    assert not any(p.is_symlink() for p in root.rglob('*')), 'Publication must contain regular files, not symlinks'
    assert not any('__pycache__' in p.parts or p.suffix in ('.pyc', '.tmp') for p in paths), 'Unexpected cache or temporary file'
    return paths


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def manifest(root):
    target = root / 'MANIFEST.sha256'
    target.write_text(''.join(sha(p) + '  ' + p.relative_to(root).as_posix() + '\n'
                              for p in files(root) if p != target))


def verify_manifest(root):
    rows = (root / 'MANIFEST.sha256').read_text().splitlines()
    for row in rows:
        expected, name = row.split('  ', 1)
        path = (root / name).resolve()
        assert path.is_relative_to(root.resolve()) and path.is_file()
        assert sha(path) == expected, 'Archive checksum mismatch: ' + name
    assert len(rows) + 1 == len(files(root)), 'Checksum inventory/file count mismatch'
    return len(rows)


def make_archive(root, destination):
    temporary = destination.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files(root):
            entry = zipfile.ZipInfo(root.name + '/' + path.relative_to(root).as_posix(), date_time=(2026, 10, 31, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
    temporary.replace(destination)


def roundtrip(archive_path):
    with tempfile.TemporaryDirectory(prefix='philosophical-publication-zip-') as temp:
        with zipfile.ZipFile(archive_path) as archive:
            assert archive.testzip() is None, 'ZIP CRC failure'
            for name in archive.namelist():
                assert not Path(name).is_absolute() and '..' not in Path(name).parts
            archive.extractall(temp)
        relocated = Path(temp) / ROOT.name
        hashes = verify_manifest(relocated)
        links = check_links(relocated)
        assert links['status'] == 'passed', links['errors']
        vectors = check_vectors(relocated)
        assert vectors['status'] == 'passed'
        return {'status': 'passed', 'zip_crc': 'passed', 'verified_file_hashes': hashes,
                'static_checks': links, 'vector_checks': vectors, 'inference_requests': 0}


def main():
    record = ROOT / 'verification/archive_checks.json'
    if not record.exists():
        save(record, {'status': 'pending'})
    inventory_path = ROOT / 'verification/package_inventory.json'
    if not inventory_path.exists():
        save(inventory_path, {'status': 'pending'})
    links = check_links(ROOT)
    save(ROOT / 'verification/publication_checks.json', links)
    assert links['status'] == 'passed', links['errors']
    vectors = check_vectors(ROOT)
    save(ROOT / 'verification/vector_checks.json', vectors)
    with tempfile.TemporaryDirectory(prefix='philosophical-publication-copy-') as temp:
        relocated = Path(temp) / ROOT.name
        shutil.copytree(ROOT, relocated)
        relocated_links = check_links(relocated)
        relocated_vectors = check_vectors(relocated)
        assert relocated_links['status'] == 'passed', relocated_links['errors']
        assert relocated_vectors['status'] == 'passed'
        save(ROOT / 'verification/relocation_checks.json', {
            'status': 'passed', 'location': 'temporary directory outside the research project',
            'static_checks': relocated_links, 'vector_checks': relocated_vectors,
            'browser_checks_file': 'browser_checks.json', 'inference_requests': 0})
    payload = files(ROOT)
    large = sorted(payload, key=lambda p: p.stat().st_size, reverse=True)[:10]
    assert max(p.stat().st_size for p in payload) < 100 * 1024 * 1024, 'File exceeds GitHub ordinary-file limit'
    save(inventory_path, {'snapshot_note': 'Payload sizes before writing this inventory and final checksum manifest.',
         'payload_bytes': sum(p.stat().st_size for p in payload if p != inventory_path and p.name != 'MANIFEST.sha256'),
         'largest_files': [{'file': Path(os.path.relpath(p, inventory_path.parent)).as_posix(), 'bytes': p.stat().st_size} for p in large],
         'files_over_100_MiB': 0, 'caches_environments_model_weights_included': False})
    archive_path = ROOT.with_suffix('.zip')
    manifest(ROOT)
    make_archive(ROOT, archive_path)
    # Record the first verified round trip, then include that evidence in the final
    # archive and verify the final archive again without mutating its contents.
    save(record, roundtrip(archive_path))
    manifest(ROOT)
    make_archive(ROOT, archive_path)
    final = roundtrip(archive_path)
    assert final['status'] == 'passed'
    print(json.dumps({'status': 'passed', 'publication': ROOT.name,
          'publication_files': len(files(ROOT)), 'publication_bytes': sum(p.stat().st_size for p in files(ROOT)),
          'zip': archive_path.name, 'zip_bytes': archive_path.stat().st_size, 'zip_sha256': sha(archive_path),
          'original_and_relocated_static_checks': 'passed', 'saved_vector_checks': 'passed',
          'final_archive_roundtrip': 'passed', 'inference_requests': 0}, indent=2))


if __name__ == '__main__':
    main()
