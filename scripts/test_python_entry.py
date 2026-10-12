"""Unified CLI contracts: preset routing, safe configuration edits and platform dispatch."""

import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import q2
from scripts.entry_config import PROFILES, config_main
from scripts.project_config import load_config


class PythonEntryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="q2 cli ")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def config(self, *args):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            config_main(list(args))
        return output.getvalue()

    def test_all_profiles_validate_without_sdks(self):
        for name, profile in PROFILES.items():
            with self.subTest(profile=name):
                output = self.config("validate", "--profile", name)
                self.assertIn(f"platform={profile.target}", output)
                load_config(ROOT / profile.file, profile.target)

    def test_management_does_not_build_or_launch(self):
        with patch.object(q2, "command") as command:
            with contextlib.redirect_stdout(io.StringIO()):
                q2.main(["platforms"])
                q2.main(["config", "show", "--profile", "esp32s3-am213"])
            command.assert_not_called()

    def test_validated_transaction_and_failed_edit_preserve_source(self):
        path = self.directory / "configuration with spaces.json"
        self.config("init", "--profile", "esp32s3-am213", "--output", str(path))
        self.config(
            "set", "--profile", "esp32s3-am213", "--config", str(path),
            "display.rotation=0", "display.width=410", "display.height=502", "display.brightness=65"
        )
        data = load_config(path, "esp32s3")
        self.assertEqual((data["display"]["width"], data["display"]["height"]), (410, 502))
        original = path.read_bytes()
        for edits in (["display.width=0"], ["display.typo=2"], ["display.brightness=true"],
                      ["display.brightness=50", "display.brightness=70"], ["logging.level=bad"]):
            with self.subTest(edits=edits), self.assertRaises(ValueError):
                self.config("set", "--profile", "esp32s3-am213", "--config", str(path), *edits)
            self.assertEqual(path.read_bytes(), original)
        self.assertEqual(list(self.directory.iterdir()), [path])

    def test_copy_never_overwrites_existing_file(self):
        path = self.directory / "local.json"
        self.config("init", "--profile", "host", "--output", str(path))
        original = path.read_bytes()
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.config("init", "--profile", "kernel", "--output", str(path))
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.config("set", "--profile", "kernel", "--output", str(path), "logging.enabled=false")
        self.assertEqual(path.read_bytes(), original)

    def test_set_output_preserves_preset(self):
        source = ROOT / PROFILES["host"].file
        original = source.read_bytes()
        path = self.directory / "local.json"
        self.config("set", "--profile", "host", "--output", str(path), 'logging.level="debug"')
        self.assertEqual(load_config(path, "host")["logging"]["level"], "debug")
        self.assertEqual(source.read_bytes(), original)

    def test_profile_conflict_is_rejected_before_build(self):
        with patch.object(q2, "configure") as configure, self.assertRaisesRegex(ValueError, "conflicts"):
            q2.main(["build", "--platform", "host", "--profile", "esp32s3-am213"])
        configure.assert_not_called()

    def test_native_platform_dispatch(self):
        for profile in ("host", "kernel", "x86-linux"):
            with self.subTest(profile=profile), patch.object(q2, "configure") as configure:
                q2.main(["configure", "--profile", profile])
                args, config, build = configure.call_args.args
                self.assertEqual(args.target, PROFILES[profile].target)
                self.assertEqual(args.config, ROOT / PROFILES[profile].file)
        with patch.object(q2, "command") as command, self.assertRaisesRegex(ValueError, "test target"):
            q2.main(["run", "--profile", "kernel"])
        command.assert_not_called()

    def test_known_files_select_platform_and_panel_cache(self):
        directories = []
        for name in ("esp32s3-am178", "esp32s3-am213"):
            with patch.object(q2, "esp_build") as esp:
                q2.main(["build", "--config", str(ROOT / PROFILES[name].file)])
                args, _, _, build = esp.call_args.args
                self.assertEqual(args.target, "esp32s3")
                self.assertEqual(build.name, PROFILES[name].build_name)
                directories.append(build)
        self.assertNotEqual(*directories)

    def test_custom_configs_have_distinct_caches(self):
        directories = []
        for name in ("one", "two"):
            folder = self.directory / name
            folder.mkdir()
            path = folder / "same name.json"
            self.config("init", "--profile", "host", "--output", str(path))
            with patch.object(q2, "configure") as configure:
                q2.main(["configure", "--platform", "host", "--config", str(path)])
                directories.append(configure.call_args.args[2])
        self.assertNotEqual(*directories)

    def test_esp_flash_and_monitor_have_separate_arguments_and_fail_fast(self):
        sdk = self.directory / "sdk with spaces"
        (sdk / "tools").mkdir(parents=True)
        (sdk / "tools/idf.py").touch()
        args = ["run", "--profile", "esp32s3-am213", "--port", "/dev/ttyUSB1",
                "--baud", "460800", "--monitor-baud", "115200"]
        with patch.dict(os.environ, {"IDF_PATH": str(sdk)}), patch.object(q2, "prepare_esp_build"), \
                patch.object(q2, "generate"), patch.object(q2, "command") as command:
            q2.main(args)
            flash, monitor = [call.args[0] for call in command.call_args_list]
            self.assertEqual(flash[-3:], ["-b", "460800", "flash"])
            self.assertEqual(monitor[-3:], ["monitor", "--monitor-baud", "115200"])
            self.assertIn("/dev/ttyUSB1", flash)
            self.assertNotIn("-b", monitor)
            command.reset_mock()
            command.side_effect = subprocess.CalledProcessError(1, "idf.py")
            with self.assertRaises(subprocess.CalledProcessError):
                q2.main(args)
            self.assertEqual(command.call_count, 1)

    def test_esp32_sdk_actions_and_serial_requirements(self):
        sdk = self.directory / "esp32 sdk"
        (sdk / "tools").mkdir(parents=True)
        (sdk / "tools/idf.py").touch()
        with (
            patch.dict(os.environ, {"IDF_PATH": str(sdk)}, clear=True),
            patch.object(q2, "prepare_esp_build"),
            patch.object(q2, "generate"),
            patch.object(q2, "command") as command,
        ):
            for action in ("configure", "build", "menuconfig", "flash", "monitor", "run"):
                with self.subTest(action=action):
                    command.reset_mock()
                    args = [action, "--platform", "esp32"]
                    if action in ("flash", "monitor", "run"):
                        args += ["--port", "/dev/ttyUSB2"]
                    q2.main(args)
                    commands = [call.args[0] for call in command.call_args_list]
                    expected = ["flash", "monitor"] if action == "run" else [
                        "reconfigure" if action == "configure" else action
                    ]
                    self.assertEqual([argv[-1] for argv in commands], expected)
                    for argv in commands:
                        self.assertEqual(argv[1], sdk / "tools/idf.py")
                        self.assertEqual(argv[argv.index("-C") + 1], ROOT / "platform/esp32")
                        self.assertEqual(argv[argv.index("-B") + 1].name, "esp32")
            command.reset_mock()
            with self.assertRaisesRegex(ValueError, "Specify --port"):
                q2.main(["run", "--profile", "esp32"])
            command.assert_not_called()

    def test_invalid_cli_config_returns_nonzero_without_traceback(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "q2.py"), "config", "set", "--profile", "host",
             "--output", str(self.directory / "invalid.json"), "display.width=0"],
            capture_output=True, text=True, cwd=self.directory,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("display.width", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse((self.directory / "invalid.json").exists())


if __name__ == "__main__":
    unittest.main()
