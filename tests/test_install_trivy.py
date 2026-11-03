"""Exercise the real installer with local release-download fixtures."""

import hashlib
import io
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/install-trivy.sh"


class InstallTrivyTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name)
        self.destination = self.root / "installed tools"
        self.destination.mkdir()
        (self.destination / "trivy").write_text("existing binary")
        self.mock_bin = self.root / "bin"
        self.mock_bin.mkdir()
        # Only transport is replaced. The real checksum, tar and install tools run.
        mock = self.mock_bin / "curl"
        mock.write_text("""#!/usr/bin/env python3
import os, pathlib, shutil, sys
args = sys.argv[1:]
url = next(arg for arg in args if arg.startswith('https://'))
root = pathlib.Path(os.environ['FIXTURES'])
with (root / 'requests').open('a') as log:
    log.write(url + '\\n')
if os.environ.get('FAIL_DOWNLOAD'):
    sys.exit(22)
shutil.copyfile(root / url.rsplit('/', 1)[1], args[args.index('--output') + 1])
""")
        mock.chmod(0o755)

    def release(self, architecture="X64", checksum_mode="valid", link=False):
        platform = {"X64": "64bit", "ARM64": "ARM64"}[architecture]
        asset = f"trivy_0.69.3_Linux-{platform}.tar.gz"
        archive = self.root / asset
        with tarfile.open(archive, "w:gz") as tar:
            entry = tarfile.TarInfo("trivy")
            if link:
                entry.type = tarfile.SYMTYPE
                entry.linkname = "/bin/sh"
                tar.addfile(entry)
            else:
                content = b"#!/bin/sh\necho 'Trivy fixture 0.69.3'\n"
                entry.size = len(content)
                tar.addfile(entry, io.BytesIO(content))
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        line = f"{digest}  {asset}\n"
        if checksum_mode == "mismatch":
            line = f"{'0' * 64}  {asset}\n"
        elif checksum_mode == "missing":
            line = f"{digest}  unrelated.tar.gz\n"
        elif checksum_mode == "duplicate":
            line += line
        elif checksum_mode == "malformed":
            line = f"invalid  {asset}\n"
        (self.root / "trivy_0.69.3_checksums.txt").write_text(line)
        return asset

    def run_installer(self, architecture="X64", version="v0.69.3", fail_download=False):
        env = dict(os.environ, PATH=f"{self.mock_bin}:{os.environ['PATH']}", FIXTURES=str(self.root))
        if fail_download:
            env["FAIL_DOWNLOAD"] = "1"
        return subprocess.run(
            ["bash", str(SCRIPT), version, architecture, str(self.destination)],
            env=env, capture_output=True, text=True, timeout=10,
        )

    def assert_preserved(self, result):
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.destination / "trivy").read_text(), "existing binary")

    def test_verified_release_installs_for_both_linux_architectures(self):
        for architecture in ("X64", "ARM64"):
            with self.subTest(architecture=architecture):
                asset = self.release(architecture)
                result = self.run_installer(architecture)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                binary = self.destination / "trivy"
                self.assertTrue(os.access(binary, os.X_OK))
                self.assertIn("Trivy fixture 0.69.3", subprocess.check_output([str(binary)], text=True))
                self.assertIn(f"https://github.com/aquasecurity/trivy/releases/download/v0.69.3/{asset}", (self.root / "requests").read_text())

    def test_bad_checksums_preserve_existing_binary(self):
        for mode in ("mismatch", "missing", "duplicate", "malformed"):
            with self.subTest(mode=mode):
                self.release(checksum_mode=mode)
                self.assert_preserved(self.run_installer())

    def test_download_failure_preserves_existing_binary(self):
        self.release()
        self.assert_preserved(self.run_installer(fail_download=True))

    def test_symlink_is_rejected(self):
        self.release(link=True)
        self.assert_preserved(self.run_installer())

    def test_invalid_versions_and_architectures_do_not_download(self):
        for version, architecture in (("latest", "X64"), ("v0.69.3/../evil", "X64"), ("v0.69.3", "X86")):
            with self.subTest(version=version, architecture=architecture):
                self.assert_preserved(self.run_installer(architecture, version))
                self.assertFalse((self.root / "requests").exists())


class ScanSummaryTests(unittest.TestCase):
    def test_unsuccessful_scan_never_claims_clean_results(self):
        action = (SCRIPT.parents[1] / "action.yaml").read_text()
        step = action.split("    - name: Post Trivy results to summary\n", 1)[1].split("\n    - name:", 1)[0]
        script = "\n".join(line[8:] for line in step.split("      run: |\n", 1)[1].splitlines())
        for outcome in ("failure", "skipped", "success"):
            for has_output in (True, False):
                with self.subTest(outcome=outcome, has_output=has_output), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    if has_output:
                        (root / "trivy-results.txt").write_text("scanner table output")
                    summary = root / "summary"
                    subprocess.run(["bash", "-eu", "-c", script], cwd=root,
                                   env=dict(os.environ, SCAN_OUTCOME=outcome, GITHUB_STEP_SUMMARY=str(summary)),
                                   check=True, timeout=10)
                    text = summary.read_text()
                    if outcome != "success":
                        self.assertIn("did not complete successfully", text)
                        self.assertNotIn("scanner table output", text)
                    elif has_output:
                        self.assertIn("scanner table output", text)
                    else:
                        self.assertIn("no table output", text)
                    self.assertNotIn("No vulnerabilities found", text)


if __name__ == "__main__":
    unittest.main()
