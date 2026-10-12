"""Regression tests for SDK changes including a half-reconfigured nested bootloader."""

import contextlib
import io
import os
from pathlib import Path
import tempfile
import unittest
from esp_build_cache import prepare_esp_build


class EspBuildCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="q2-sdk-cache-")
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.build, self.sdk, self.source = root / "build", root / "new sdk", root / "source"
        self.python = root / "python"
        (self.build / "bootloader").mkdir(parents=True)
        self.settings = b"CONFIG_IDF_TARGET=esp32s3\r\nCONFIG_CUSTOM_OPTION=y\r\n"
        (self.build / "sdkconfig").write_bytes(self.settings)

    def prepare(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return prepare_esp_build(self.build, self.sdk, self.source, self.python, "esp32s3")

    def cache(self, path, **values):
        path.write_text("\n".join(f"{k}:INTERNAL={v}" for k, v in values.items()), encoding="utf8")

    def test_main_already_switched_but_bootloader_stale(self):
        self.cache(self.build / "CMakeCache.txt", CMAKE_HOME_DIRECTORY=self.source, PYTHON=self.python)
        self.cache(self.build / "bootloader/CMakeCache.txt", CMAKE_HOME_DIRECTORY="/old/sdk/bootloader")
        (self.build / "firmware.bin").write_bytes(b"previous output")
        backup = self.prepare()
        self.assertEqual((self.build / "sdkconfig").read_bytes(), self.settings)
        self.assertTrue((backup / "bootloader/CMakeCache.txt").is_file())
        self.assertEqual((backup / "firmware.bin").read_bytes(), b"previous output")
        self.assertFalse((self.build / "CMakeCache.txt").exists())
        self.assertIsNone(self.prepare())

    def test_matching_caches_are_not_changed(self):
        self.cache(self.build / "CMakeCache.txt", CMAKE_HOME_DIRECTORY=self.source, PYTHON=self.python)
        self.cache(
            self.build / "bootloader/CMakeCache.txt",
            CMAKE_HOME_DIRECTORY=self.sdk / "components/bootloader/subproject",
            IDF_PATH=self.sdk,
        )
        self.assertIsNone(self.prepare())
        self.assertTrue((self.build / "bootloader/CMakeCache.txt").is_file())

    def test_python_change_and_partial_cache(self):
        self.cache(self.build / "CMakeCache.txt", PYTHON="/old/python")
        self.assertIsNotNone(self.prepare())

    @unittest.skipUnless(os.name == "posix", "POSIX interpreter symlink aliases")
    def test_python_alias_change_uses_idf_exact_path_comparison(self):
        self.python.touch()
        alias = self.python.with_name("python3")
        alias.symlink_to(self.python)
        self.cache(self.build / "CMakeCache.txt", PYTHON=alias)
        backup = self.prepare()
        self.assertIsNotNone(backup)
        self.assertEqual((self.build / "sdkconfig").read_bytes(), self.settings)

    def test_source_directory_is_never_moved(self):
        self.cache(self.build / "CMakeCache.txt", IDF_PATH="/old/sdk")
        (self.build / "CMakeLists.txt").write_text("project(source)")
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertTrue((self.build / "sdkconfig").is_file())


if __name__ == "__main__":
    unittest.main()
