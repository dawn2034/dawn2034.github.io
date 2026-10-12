"""Exercise a real local Git remote; stub only Ruby dependency installation/build."""
import os
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import chirpy_publish as p
import test_chirpy_publish as fixture


class RebuildRaceTest(unittest.TestCase):
    setUp = fixture.PublicationTests.setUp
    tearDown = fixture.PublicationTests.tearDown

    def test_rebuild_after_source_advance_keeps_sources_and_excludes_lock(self):
        def git(*args, check=True):
            return subprocess.run(['git', *args], cwd=self.root, check=check,
                                  text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        with tempfile.TemporaryDirectory() as remote:
            subprocess.run(['git', 'init', '--bare', remote], check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            git('init', '-b', 'master')
            git('config', 'user.name', 'Publication test')
            git('config', 'user.email', 'test@example.invalid')
            git('add', 'DailyEpoch', 'chirpy-src')
            git('commit', '-m', 'initial source')
            old = git('rev-parse', 'HEAD').stdout.strip()
            git('remote', 'add', 'origin', remote)
            git('push', '-u', 'origin', 'master')
            with self.source.open('a', encoding='utf-8') as f:
                f.write('Concurrent source edit must survive.\n')
            expected_source = self.source.read_bytes()
            git('commit', '-am', 'source advanced during build')
            latest = git('rev-parse', 'HEAD').stdout.strip()
            git('push', 'origin', 'master')
            original_run = p.run

            def fake_install(args, cwd, **kwargs):
                if args[:2] == ['bundle', 'install']:
                    (cwd / 'Gemfile.lock').write_text('generated build-only lock')
                    return subprocess.CompletedProcess(args, 0, 'installed')
                return original_run(args, cwd, **kwargs)

            def fake_build(root, site):
                shutil.copytree(self.site, site)
                with (site / f'DailyEpoch/{self.date}/index.html').open('a') as f:
                    f.write('rebuilt latest source')

            env = {'BUILD_SOURCE_SHA': old, 'TRIGGER_HEAD_SHA': 'test-trigger',
                   'GITHUB_EVENT_NAME': 'pull_request', 'GITHUB_RUN_ID': '1',
                   'GITHUB_REPOSITORY': 'test/repo', 'GITHUB_STEP_SUMMARY': ''}
            with patch.dict(os.environ, env), patch.object(p, 'run', side_effect=fake_install), patch.object(p, 'build', side_effect=fake_build) as rebuilder:
                p.publish(self.root, self.site)
            self.assertEqual(rebuilder.call_count, 1)
            git('fetch', 'origin', 'master')
            actual = git('show', f'origin/master:DailyEpoch/{self.date}.md').stdout.encode()
            self.assertEqual(actual, expected_source)
            self.assertNotEqual(git('rev-parse', 'origin/master').stdout.strip(), latest)
            self.assertNotEqual(git('cat-file', '-e', 'origin/master:Gemfile.lock', check=False).returncode, 0)
            page = git('show', f'origin/master:DailyEpoch/{self.date}/index.html').stdout
            self.assertIn('rebuilt latest source', page)
            self.assertEqual(git('ls-tree', '-r', '--name-only', 'origin/master', 'chirpy-src/_posts').stdout.strip(), '')


if __name__ == '__main__':
    unittest.main()
