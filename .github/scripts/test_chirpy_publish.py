import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import chirpy_publish as p


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.site = self.root / '_site'
        for name in ['DailyEpoch', 'chirpy-src/legacy-posts']:
            (self.root / name).mkdir(parents=True)
        self.date = '2026-10-11'
        self.source = self.root / f'DailyEpoch/{self.date}.md'
        self.source.write_text(f'---\ntitle: "每日 AI 技术简报｜{self.date}"\ndate: {self.date}\npermalink: /DailyEpoch/{self.date}/\n---\n\n## 原稿\n正文不改变。\n', encoding='utf-8')
        (self.root / 'DailyEpoch/index.md').write_text(f'- [{self.date}](./{self.date}/)\n', encoding='utf-8')
        for name in ['index.html', 'assets/css/jekyll-theme-chirpy.css', 'assets/js/dist/theme.min.js', 'DailyEpoch/index.html', '2018/09/03/2018年暑期（05.21-08.10）实习总结/index.html']:
            dest = self.site / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text('鸣响的杯子 DailyEpoch', encoding='utf-8')
        self.page = self.site / f'DailyEpoch/{self.date}/index.html'
        self.page.parent.mkdir(parents=True)
        self.page.write_text(f'<link rel="canonical" href="{p.BASE_URL}/DailyEpoch/{self.date}/">', encoding='utf-8')

    def tearDown(self):
        self.tmp.cleanup()

    def test_valid_site(self):
        p.validate(self.root, self.site)

    def test_prepare_keeps_original_bytes(self):
        before = self.source.read_bytes()
        p.prepare(self.root)
        self.assertEqual(before, self.source.read_bytes())
        self.assertTrue((self.root / f'chirpy-src/_posts/{self.date}-dailyepoch.md').is_file())

    def test_missing_index_entry_rejected(self):
        (self.root / 'DailyEpoch/index.md').write_text('')
        with self.assertRaisesRegex(RuntimeError, 'MISSING_INDEX_ENTRY'):
            p.validate(self.root, self.site)

    def test_wrong_canonical_rejected(self):
        self.page.write_text('<link rel="canonical" href="https://example.com/">')
        with self.assertRaisesRegex(RuntimeError, 'CANONICAL_MISMATCH'):
            p.validate(self.root, self.site)

    def test_missing_page_rejected(self):
        self.page.unlink()
        with self.assertRaisesRegex(RuntimeError, 'POST_COUNT_MISMATCH'):
            p.validate(self.root, self.site)

    def test_internal_citation_rejected(self):
        with self.source.open('a', encoding='utf-8') as f:
            f.write('\ue200cite\ue202turn1search0\ue201')
        with self.assertRaisesRegex(RuntimeError, 'INTERNAL_CITATION_MARKER'):
            p.validate(self.root, self.site)

    def test_duplicate_index_rejected(self):
        with (self.root / 'DailyEpoch/index.md').open('a') as f:
            f.write(f'- [{self.date}](./{self.date}/)\n')
        with self.assertRaisesRegex(RuntimeError, 'INDEX_DUPLICATED_OR_OUT_OF_ORDER'):
            p.validate(self.root, self.site)

    def test_security_failures_are_not_retryable(self):
        self.assertFalse(p.retryable_push('403 Permission denied'))
        self.assertFalse(p.retryable_push('GH013 repository rule violation'))
        self.assertFalse(p.retryable_push('safety check denied action'))
        self.assertTrue(p.retryable_push('! [rejected] HEAD -> master (fetch first)'))
        self.assertTrue(p.retryable_push('non-fast-forward'))

    def test_source_diff_is_not_silently_ignored(self):
        with patch.object(p, 'run') as runner:
            runner.return_value.returncode = 1
            self.assertTrue(p.input_changed(self.root, 'old', 'new'))
            self.assertIn(':(glob)DailyEpoch/*.md', runner.call_args.args[0])
            runner.return_value.returncode = 0
            self.assertFalse(p.input_changed(self.root, 'old', 'new'))


if __name__ == '__main__':
    unittest.main()
