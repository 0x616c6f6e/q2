"""Exercise the Bash boundary: paths/arguments, tool failures and host cache isolation."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import q2


class BuildHostTests(unittest.TestCase):
    def test_default_build_is_host_specific(self):
        with patch.object(sys, "argv", ["q2.py", "build", "--target", "esp32s3"]):
            with patch.object(q2, "esp_build") as build:
                q2.main()
        expected = ROOT / "build"
        if os.name != "nt":
            expected /= sys.platform
        self.assertEqual(build.call_args.args[3], (expected / "esp32s3").resolve())

    @unittest.skipUnless(sys.platform == "linux", "Linux SDL2 profile")
    def test_x86_uses_linux_profile(self):
        with patch.object(sys, "argv", ["q2.py", "configure", "--target", "x86"]):
            with patch.object(q2, "configure") as configure:
                q2.main()
        args, config, build = configure.call_args.args
        self.assertEqual(args.config, ROOT / "q2.linux.json")
        self.assertTrue(config["components"]["network"])
        self.assertFalse(config["components"]["audio"])
        self.assertEqual(build, ROOT / "build/linux/x86")

    def test_explicit_build_directory_is_respected(self):
        with tempfile.TemporaryDirectory(prefix="q2 build ") as temp:
            path = Path(temp) / "custom"
            with patch.object(
                sys, "argv", ["q2.py", "build", "--target", "esp32s3", "--build-dir", str(path)]
            ):
                with patch.object(q2, "esp_build") as build:
                    q2.main()
            self.assertEqual(build.call_args.args[3], path.resolve())


@unittest.skipUnless(sys.platform == "linux", "Bash integration runs on Linux/WSL")
class LinuxEntryTests(unittest.TestCase):
    def test_spaces_arguments_and_exit_code(self):
        with tempfile.TemporaryDirectory(prefix="q2 shell ") as temp:
            root = Path(temp)
            shutil.copyfile(ROOT / "build.sh", root / "build.sh")
            interpreter = root / "python with spaces"
            interpreter.write_text(
                "#!/usr/bin/env python3\nimport json, sys\nprint(json.dumps(sys.argv[1:]))\nsys.exit(23)\n"
            )
            interpreter.chmod(0o755)
            result = subprocess.run(
                ["bash", str(root / "build.sh"), "--config", "config with spaces.json", "--target", "kernel"],
                env={**os.environ, "Q2_PYTHON": str(interpreter)},
                capture_output=True,
                text=True,
                cwd="/",
            )
            self.assertEqual(result.returncode, 23, result.stderr)
            self.assertEqual(
                json.loads(result.stdout),
                [
                    str(root / "q2.py"),
                    "build",
                    "--target",
                    "esp32s3",
                    "--config",
                    "config with spaces.json",
                    "--target",
                    "kernel",
                ],
            )

    def test_missing_python_is_actionable(self):
        result = subprocess.run(
            ["bash", str(ROOT / "build.sh")],
            env={**os.environ, "Q2_PYTHON": "/no-such-q2-python"},
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 127)
        self.assertIn("Activate ESP-IDF", result.stderr)


if __name__ == "__main__":
    unittest.main()
