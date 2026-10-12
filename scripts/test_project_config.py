"""Product configuration contracts: strict schema, feature dependencies and generated values."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

from project_config import ROOT, generate, load_config


class ProductConfigTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "q2.json").read_text(encoding="utf8"))
        # Keep test policy stable when a developer edits the live product's settings.
        self.config["components"].update(
            display=True,
            storage=True,
            keys=True,
            apps=True,
            sqlite=False,
            usb=False,
            audio=False,
            wireless=False,
            network=False,
        )
        self.config["keys"].update(
            names=["POWER", "PLAY"], single_min_ms=20, double_gap_ms=300, long_press_ms=800
        )
        self.config["system_ui"] = dict(
            status_bar=True,
            status_bar_height=32,
            screensaver=True,
            idle_timeout_ms=30000,
            clock_move_interval_ms=10000,
        )
        self.config["web"].update(enabled=True, port=8765)
        self.temp = tempfile.TemporaryDirectory(prefix="q2-config-")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "q2.json"

    def load(self, config=None, target="x86"):
        self.path.write_text(json.dumps(config or self.config), encoding="utf8")
        return load_config(self.path, target)

    def test_generated_values_and_incremental_build(self):
        self.config["display"] = {"width": 320, "height": 320}
        self.config["keys"].update(single_min_ms=30, double_gap_ms=250, long_press_ms=900)
        data = self.load()
        out = Path(self.temp.name) / "generated"
        generate(data, out, "x86")
        header = (out / "q2_project_config.h").read_text()
        for expected in ("Q2_DISPLAY_WIDTH 320u", "Q2_KEY_DOUBLE_GAP_MS 250u", "Q2_KEY_LONG_PRESS_MS 900u"):
            self.assertIn(expected, header)
        stamp = (out / "q2_project_config.h").stat().st_mtime_ns
        generate(data, out, "x86")
        self.assertEqual((out / "q2_project_config.h").stat().st_mtime_ns, stamp)

    def test_disabled_features_are_not_reenabled(self):
        self.config["components"].update(storage=False, keys=False, apps=False)
        self.config["web"]["enabled"] = False
        self.config["logging"]["enabled"] = False
        data = self.load()
        out = Path(self.temp.name) / "generated"
        generate(data, out, "x86")
        self.assertIn("set(Q2_WITH_STORAGE OFF", (out / "project.cmake").read_text())
        self.assertIn("set(Q2_ENABLE_LOG OFF", (out / "project.cmake").read_text())
        self.assertIn("Q2_COMPONENT_KEYS 0u", (out / "q2_project_config.h").read_text())

    def test_reject_invalid_or_unsupported_settings(self):
        mutations = [
            ("system_ui", "idle_timeout_ms", 0),
            ("system_ui", "clock_move_interval_ms", -1),
            ("system_ui", "status_bar_height", 65),
            ("system_ui", "screensaver", "false"),
            ("display", "width", 0),
            ("display", "height", True),
            ("keys", "single_min_ms", 0),
            ("keys", "long_press_ms", 10),
            ("keys", "names", ["POWER", "POWER"]),
            ("keys", "names", ["bad name"]),
            ("components", "storage", "false"),
            ("components", "keys", False),
            ("components", "usb", True),
            ("components", "wireless", True),
            ("components", "display", False),
            ("web", "port", 65536),
            ("logging", "level", "verbose"),
            ("app", "startup", "../escape"),
            ("app", "grants", ["bad capability"]),
        ]
        for group, key, value in mutations:
            with self.subTest(group=group, key=key, value=value):
                config = copy.deepcopy(self.config)
                config[group][key] = value
                with self.assertRaises(ValueError):
                    self.load(config)
        self.config["display"]["typo"] = 1
        with self.assertRaises(ValueError):
            self.load()

    def test_cjk_font_switch_and_legacy_config(self):
        out = Path(self.temp.name) / "font-generated"
        self.config["display"].pop("cjk_font", None)
        self.assertTrue(self.load()["display"]["cjk_font"])
        for enabled in (True, False):
            self.config["display"]["cjk_font"] = enabled
            generate(self.load(), out, "x86")
            state = "ON" if enabled else "OFF"
            self.assertIn(f"set(Q2_ENABLE_CJK_FONT {state}", (out / "project.cmake").read_text())
        for invalid in ("false", 0, None):
            self.config["display"]["cjk_font"] = invalid
            with self.assertRaisesRegex(ValueError, "display.cjk_font must be boolean"):
                self.load()

    def test_audio_provider(self):
        self.config["components"]["audio"] = True
        out = Path(self.temp.name) / "audio-generated"
        generate(self.load(), out, "x86")
        self.assertIn("Q2_COMPONENT_AUDIO 1u", (out / "q2_project_config.h").read_text())
        self.config["system_ui"].update(status_bar=False, screensaver=False)
        with self.assertRaisesRegex(ValueError, "Audio backend is x86 only"):
            self.load(target="host")

    def test_network_provider_and_legacy_config(self):
        self.config["components"]["network"] = True
        out = Path(self.temp.name) / "network-generated"
        generate(self.load(), out, "x86")
        self.assertIn("Q2_COMPONENT_NETWORK 1u", (out / "q2_project_config.h").read_text())
        del self.config["components"]["network"]
        self.assertFalse(self.load()["components"]["network"])

    def test_system_ui_values_and_legacy_profiles(self):
        out = Path(self.temp.name) / "generated"
        generate(self.load(), out, "x86")
        header = (out / "q2_project_config.h").read_text()
        for expected in (
            "Q2_STATUS_BAR_ENABLED 1u",
            "Q2_IDLE_TIMEOUT_MS 30000u",
            "Q2_CLOCK_MOVE_INTERVAL_MS 10000u",
        ):
            self.assertIn(expected, header)
        self.config["display"]["height"] = 64
        self.config["system_ui"]["status_bar_height"] = 40
        with self.assertRaises(ValueError):
            self.load()
        del self.config["system_ui"]
        legacy = self.load()
        self.assertFalse(legacy["system_ui"]["status_bar"])
        self.assertFalse(legacy["system_ui"]["screensaver"])

    def test_data_switch_and_old_profiles(self):
        self.config["components"]["data"] = False
        out = Path(self.temp.name) / "generated-data"
        generate(self.load(), out, "x86")
        self.assertIn("Q2_COMPONENT_DATA 0u", (out / "q2_project_config.h").read_text())
        del self.config["components"]["data"]
        self.assertTrue(self.load()["components"]["data"])
        for name in self.config["components"]:
            self.config["components"][name] = False
        self.config["web"]["enabled"] = False
        self.config["system_ui"].update(status_bar=False, screensaver=False, lock_enabled=False)
        self.assertFalse(self.load(target="esp32s31")["components"]["data"])

    def test_esp32s3_display_profile(self):
        self.config = json.loads((ROOT / "q2.esp32s3.json").read_text())
        self.load(target="esp32s3")
        self.config["display"] = {"width": 448, "height": 368}
        self.load(target="esp32s3")
        self.config["display"]["width"] = 502
        with self.assertRaises(ValueError):
            self.load(target="esp32s3")
        self.config["display"]["width"] = 448
        self.config["components"]["storage"] = True
        with self.assertRaises(ValueError):
            self.load(target="esp32s3")

    def test_esp32s3_rotations(self):
        self.config = json.loads((ROOT / "q2.esp32s3.json").read_text())
        out = Path(self.temp.name) / "rotation-generated"
        for rotation in (0, 90, 180, 270):
            w, h = (448, 368) if rotation in (90, 270) else (368, 448)
            self.config["display"].update(width=w, height=h, rotation=rotation)
            data = self.load(target="esp32s3")
            generate(data, out, "esp32s3")
            self.assertIn(f"Q2_DISPLAY_ROTATION {rotation}u", (out / "q2_project_config.h").read_text())
            self.config["display"].update(width=h, height=w)
            with self.assertRaisesRegex(ValueError, "AM178 rotation"):
                self.load(target="esp32s3")
        self.config["display"].update(width=368, height=448)
        for invalid in (True, "90", 90.0, -90, 45, 360):
            self.config["display"]["rotation"] = invalid
            with self.assertRaisesRegex(ValueError, "display.rotation"):
                self.load(target="esp32s3")
        del self.config["display"]["rotation"]
        self.assertEqual(self.load(target="esp32s3")["display"]["rotation"], 0)
        self.config["display"].update(width=448, height=368)
        self.assertEqual(self.load(target="esp32s3")["display"]["rotation"], 90)

    def test_am213_panel_and_rotations(self):
        self.config = json.loads((ROOT / "q2.esp32s3-am213.json").read_text())
        out = Path(self.temp.name) / "am213-generated"
        for rotation in (0, 90, 180, 270):
            w, h = (502, 410) if rotation in (90, 270) else (410, 502)
            self.config["display"].update(width=w, height=h, rotation=rotation)
            data = self.load(target="esp32s3")
            generate(data, out, "esp32s3")
            self.assertIn("Q2_DISPLAY_PANEL_AM213 1u", (out / "q2_project_config.h").read_text())
            self.config["display"].update(width=h, height=w)
            with self.assertRaisesRegex(ValueError, "AM213 rotation"):
                self.load(target="esp32s3")
        self.config["display"].update(width=502, height=410)
        self.config["display"].pop("rotation")
        self.assertEqual(self.load(target="esp32s3")["display"]["rotation"], 90)
        self.config["display"]["panel"] = "am178"
        with self.assertRaisesRegex(ValueError, "AM178 rotation"):
            self.load(target="esp32s3")
        for invalid in ("unknown", 213, None, "generic"):
            self.config["display"]["panel"] = invalid
            with self.assertRaisesRegex(ValueError, "display.panel"):
                self.load(target="esp32s3")

    def test_other_targets_reject_unimplemented_rotation(self):
        self.config["display"]["rotation"] = 180
        with self.assertRaisesRegex(ValueError, "requires ESP32-S3"):
            self.load()

    def test_display_brightness(self):
        self.config = json.loads((ROOT / "q2.esp32s3.json").read_text())
        out = Path(self.temp.name) / "brightness-generated"
        for percent in (0, 25, 100):
            self.config["display"]["brightness"] = percent
            generate(self.load(target="esp32s3"), out, "esp32s3")
            self.assertIn(f"Q2_DISPLAY_BRIGHTNESS {percent}u", (out / "q2_project_config.h").read_text())
        for invalid in (-1, 101, True, 25.5, "25", None):
            self.config["display"]["brightness"] = invalid
            with self.assertRaisesRegex(ValueError, "display.brightness"):
                self.load(target="esp32s3")
        del self.config["display"]["brightness"]
        self.assertEqual(self.load(target="esp32s3")["display"]["brightness"], 100)

    def test_duplicate_json_properties_are_errors(self):
        self.path.write_text('{"format":1,"format":1}')
        with self.assertRaises(ValueError):
            load_config(self.path)

    def test_minimal_host_and_esp_profiles(self):
        for name in self.config["components"]:
            self.config["components"][name] = False
        self.config["web"]["enabled"] = False
        self.config["system_ui"].update(status_bar=False, screensaver=False)
        self.load(target="host")
        self.load(target="esp32s31")


if __name__ == "__main__":
    unittest.main()
