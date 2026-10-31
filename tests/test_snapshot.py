import hashlib
from contextlib import closing
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from tools.snapshot import snapshot, restore


class SnapshotTests(unittest.TestCase):
    def test_deduplicate_restore_and_exclude_credentials(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'input'
            source.mkdir()
            (source / 'a.txt').write_text('same content', encoding='utf-8')
            (source / 'b.txt').write_text('same content', encoding='utf-8')
            (source / '.env').write_text('PRIVATE=do-not-copy', encoding='utf-8')
            (source / '.env.example').write_text('PRIVATE=', encoding='utf-8')
            archive = root / 'all.zip'
            manifest = snapshot({'primary': source}, archive)
            self.assertEqual(3, len(manifest['files']))
            self.assertEqual(2, manifest['object_count'])
            self.assertEqual('.env', manifest['excluded'][0]['path'])
            with zipfile.ZipFile(archive) as z:
                self.assertNotIn(b'do-not-copy', b''.join(z.read(n) for n in z.namelist()))
            report = restore(archive, root / 'restored')
            self.assertEqual(3, report['verified_files'])
            self.assertEqual('same content', (root / 'restored/primary/b.txt').read_text())

    def test_corrupt_or_missing_object_fails(self):
        for contents in (b'wrong', None):
            with self.subTest(contents=contents), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                digest = hashlib.sha256(b'expected').hexdigest()
                manifest = {'format': 'dchr-source-archive-v1', 'files': [
                    {'root': 'primary', 'path': 'a', 'sha256': digest, 'bytes': 8}]}
                with zipfile.ZipFile(root / 'bad.zip', 'w') as z:
                    z.writestr('manifest.json', json.dumps(manifest))
                    if contents is not None:
                        z.writestr('objects/' + digest, contents)
                with self.assertRaises((ValueError, KeyError)):
                    restore(root / 'bad.zip', root / 'out')

    def test_traversal_refused_before_writing(self):
        for relative in ('../outside', '/absolute', 'C:/absolute', 'sub/../../outside', 'a\\..\\outside',
                         'nul', 'NUL.txt', 'sub/COM1.csv', 'LPT9', 'trailing.', 'trailing '):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                digest = hashlib.sha256(b'body').hexdigest()
                manifest = {'format': 'dchr-source-archive-v1', 'files': [
                    {'root': 'primary', 'path': relative, 'sha256': digest, 'bytes': 4}]}
                with zipfile.ZipFile(root / 'bad.zip', 'w') as z:
                    z.writestr('manifest.json', json.dumps(manifest))
                    z.writestr('objects/' + digest, b'body')
                with self.assertRaises(ValueError):
                    restore(root / 'bad.zip', root / 'out')
                self.assertFalse((root / 'outside').exists())

    def test_scientific_qa_source_is_preserved_browser_profile_is_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source';qa=source/'results/run/qa_source';qa.mkdir(parents=True)
            (qa/'independent_check.py').write_text('assert 2+2==4',encoding='utf-8')
            browser=source/'runtime/qa_browser';browser.mkdir(parents=True)
            (browser/'Local State').write_text('{}',encoding='utf-8')
            (browser/'Default').mkdir()
            manifest=snapshot({'primary':source},root/'all.zip')
            self.assertEqual(['results/run/qa_source/independent_check.py'],[f['path'] for f in manifest['files']])
            self.assertIn('runtime/qa_browser',[e['path'] for e in manifest['excluded']])

    def test_live_sqlite_is_consistent_snapshot(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'input'
            source.mkdir()
            with closing(sqlite3.connect(source / 'history.sqlite')) as connection:
                connection.execute('PRAGMA journal_mode=WAL')
                connection.execute('CREATE TABLE events(value INTEGER)')
                connection.execute('INSERT INTO events VALUES(42)')
                connection.commit()
                manifest = snapshot({'primary': source}, root / 'db.zip')
            entry = next(f for f in manifest['files'] if f['path'] == 'history.sqlite')
            self.assertEqual('sqlite-backup', entry['capture'])
            restore(root / 'db.zip', root / 'out')
            with closing(sqlite3.connect(root / 'out/primary/history.sqlite')) as restored:
                self.assertEqual(42, restored.execute('SELECT value FROM events').fetchone()[0])


if __name__ == '__main__':
    unittest.main()
