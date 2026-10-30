"""Content-addressed project archive. Never modifies source trees.

The archive contains objects/<sha256> and manifest.json. Use restore(), not
ZipFile.extractall(), to recover the original directory layout safely.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sqlite3
import tempfile
import zipfile

FORMAT = 'dchr-source-archive-v1'
PRUNE = {'.git', 'node_modules', '__pycache__', 'slprj', '.angular', 'Cache',
         'Code Cache', 'GPUCache', 'Crashpad', 'python_deps', '.venv'}
SECRET_NAME = re.compile(r'(^\.env($|\.)|passwords?$|credentials?|cookies?$|Login Data|Web Data)', re.I)
SECRET_BYTES = re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----)')


def safe_relative(value):
    if not isinstance(value, str) or not value or '\\' in value or ':' in value or '\x00' in value:
        raise ValueError('Unsafe archive path')
    path = PurePosixPath(value)
    if path.is_absolute() or any(p in ('..', '.') for p in path.parts):
        raise ValueError('Unsafe archive path')
    return path


def exclusion(name):
    if name == '.env.example':
        return None
    if SECRET_NAME.search(name):
        return 'local credential/browser file'
    if name.endswith(('.pyc', '.pyo', '.slxc', '.sqlite-wal', '.sqlite-shm', '.db-wal', '.db-shm')):
        return 'generated cache or SQLite sidecar (database is backed up consistently)'
    if name in {'server.lock', 'MATLAB_PID.txt', 'STOP', 'PAUSE'} or name.endswith('.pid'):
        return 'machine-local process/control state'
    return None


def snapshot(roots, archive, destination=None, progress=None):
    archive = Path(archive)
    archive.parent.mkdir(parents=True, exist_ok=True)
    if archive.exists():
        raise FileExistsError(archive)
    manifest = {'format': FORMAT, 'created_utc': datetime.now(timezone.utc).isoformat(),
                'files': [], 'excluded': [], 'errors': [], 'roots': list(roots)}
    seen = set()
    partial = archive.with_suffix(archive.suffix + '.partial')
    if partial.exists():
        raise FileExistsError(partial)
    with zipfile.ZipFile(partial, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6,
                         allowZip64=True) as z:
        for alias, directory in roots.items():
            safe_relative(alias)
            root = Path(directory)
            if not root.is_dir():
                raise FileNotFoundError(root)
            count = 0
            for base, dirs, names in os.walk(root):
                dirs.sort()
                for name in dirs[:]:
                    path = Path(base) / name
                    if name in PRUNE or name.startswith('qa_') or path.is_symlink():
                        dirs.remove(name)
                        manifest['excluded'].append({'root': alias, 'path': path.relative_to(root).as_posix(),
                                                     'reason': 'installed dependency, generated cache, browser profile or symlink'})
                for name in sorted(names):
                    source = Path(base) / name
                    relative = source.relative_to(root).as_posix()
                    reason = exclusion(name)
                    if source.is_symlink():
                        reason = 'symlink (not followed)'
                    if reason:
                        manifest['excluded'].append({'root': alias, 'path': relative, 'reason': reason})
                        continue
                    try:
                        with tempfile.SpooledTemporaryFile(max_size=4 * 1024 * 1024) as spool:
                            capture = 'file-bytes'
                            if source.suffix.lower() in {'.sqlite', '.db'}:
                                with tempfile.TemporaryDirectory() as temp:
                                    backup = Path(temp) / 'backup.sqlite'
                                    with closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True, timeout=5)) as live:
                                        with closing(sqlite3.connect(backup)) as target:
                                            live.backup(target)
                                    with backup.open('rb') as stream:
                                        shutil.copyfileobj(stream, spool)
                                capture = 'sqlite-backup'
                            else:
                                with source.open('rb') as stream:
                                    shutil.copyfileobj(stream, spool)
                            spool.seek(0)
                            digest = hashlib.sha256()
                            size = 0
                            sensitive = False
                            tail = b''
                            while chunk := spool.read(1024 * 1024):
                                digest.update(chunk)
                                size += len(chunk)
                                if SECRET_BYTES.search(tail + chunk):
                                    sensitive = True
                                tail = chunk[-256:]
                            if sensitive:
                                manifest['excluded'].append({'root': alias, 'path': relative,
                                                             'reason': 'recognized secret material in contents; original preserved locally'})
                                continue
                            sha = digest.hexdigest()
                            if sha not in seen:
                                spool.seek(0)
                                with z.open('objects/' + sha, 'w', force_zip64=True) as obj:
                                    shutil.copyfileobj(spool, obj)
                                seen.add(sha)
                            entry = {'root': alias, 'path': relative, 'sha256': sha,
                                     'bytes': size, 'capture': capture}
                            manifest['files'].append(entry)
                            if destination is not None and selected(alias, relative, size):
                                target = Path(destination) / alias / relative
                                target.parent.mkdir(parents=True, exist_ok=True)
                                spool.seek(0)
                                with target.open('wb') as stream:
                                    shutil.copyfileobj(spool, stream)
                            count += 1
                    except (OSError, sqlite3.Error) as error:
                        manifest['errors'].append({'root': alias, 'path': relative, 'error_type': type(error).__name__})
                if progress and count and count % 1000 == 0:
                    progress(alias, count, len(seen))
            if progress:
                progress(alias, count, len(seen))
        manifest['object_count'] = len(seen)
        manifest['logical_bytes'] = sum(f['bytes'] for f in manifest['files'])
        z.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, separators=(',', ':')))
    partial.replace(archive)
    return manifest


def selected(alias, relative, size):
    """Small operational checkout; the archive retains everything else."""
    if size > 50 * 1024 * 1024:
        return False
    parts = PurePosixPath(relative).parts
    if alias == 'primary':
        if parts[0] == 'results':
            return len(parts) == 2 or (len(parts) > 2 and parts[1].startswith('pool_') and
                   'source_snapshot' not in parts and 'release' not in relative.lower())
        if parts[0] == 'automation':
            return False
        if 'runtime' in parts:
            return Path(relative).suffix.lower() in {'.csv', '.json', '.png', '.m', '.py'} and size < 5 * 1024 * 1024
        if 'fuxa' in parts and ('client' in parts or 'server' in parts):
            return False
        return True
    if alias.startswith('synapse/'):
        return 'runtime' not in parts and size < 20 * 1024 * 1024
    return True


def restore(archive, target, prefix=None):
    target = Path(target).resolve()
    with zipfile.ZipFile(archive) as z:
        manifest = json.loads(z.read('manifest.json'))
        if manifest.get('format') != FORMAT:
            raise ValueError('Unknown archive format')
        paths = []
        seen_paths = set()
        for entry in manifest['files']:
            rel = safe_relative(entry['root']) / safe_relative(entry['path'])
            if prefix and not str(rel).startswith(prefix):
                continue
            path = (target / str(rel)).resolve()
            if not path.is_relative_to(target) or path in seen_paths:
                raise ValueError('Unsafe or duplicate restore path')
            seen_paths.add(path)
            if not re.fullmatch(r'[0-9a-f]{64}', entry['sha256']):
                raise ValueError('Invalid object digest')
            if path.exists():
                raise FileExistsError(path)
            paths.append((entry, path))
        checked = set()
        for entry, path in paths:
            sha = entry['sha256']
            info = z.getinfo('objects/' + sha)
            if info.file_size != entry['bytes']:
                raise ValueError('Object size mismatch: ' + entry['path'])
            if sha not in checked:
                with z.open(info) as stream:
                    actual = hashlib.file_digest(stream, 'sha256').hexdigest()
                if actual != sha:
                    raise ValueError('Object checksum mismatch: ' + entry['path'])
                checked.add(sha)
        for entry, path in paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            with z.open('objects/' + entry['sha256']) as stream, path.open('xb') as output:
                shutil.copyfileobj(stream, output)
    return {'verified_files': len(paths), 'verified_objects': len(checked), 'target': str(target)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    create = sub.add_parser('create')
    create.add_argument('--roots', type=Path, required=True, help='JSON mapping source alias to directory')
    create.add_argument('--archive', type=Path, required=True)
    create.add_argument('--checkout', type=Path)
    create.add_argument('--manifest', type=Path, required=True)
    recover = sub.add_parser('restore')
    recover.add_argument('archive', type=Path)
    recover.add_argument('target', type=Path)
    recover.add_argument('--prefix')
    args = parser.parse_args()
    if args.command == 'restore':
        print(json.dumps(restore(args.archive, args.target, args.prefix)))
    else:
        roots = json.loads(args.roots.read_text(encoding='utf-8-sig'))
        manifest = snapshot(roots, args.archive, args.checkout,
                            lambda a, n, o: print(a, n, 'files;', o, 'objects', flush=True))
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({k: v for k, v in manifest.items() if k not in {'files', 'excluded', 'roots'}}))
        if manifest['errors']:
            raise SystemExit(2)


if __name__ == '__main__':
    main()
