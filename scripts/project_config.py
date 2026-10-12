"""Validate product settings and emit an explicit, platform-only build contract."""

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEVELS = {"off": 0, "error": 1, "warn": 2, "info": 3, "debug": 4}
LIFECYCLE_DEFAULTS = {
    "lock_enabled": False,
    "status_left": "{time}",
    "status_right": "{wifi} {bt} {ble} {battery}",
    "saver_text": "{time}",
    "unlock_key": "POWER",
    "unlock_action": 2,
}
SYSTEM_UI_DEFAULTS = {
    **LIFECYCLE_DEFAULTS,
    "status_bar": False,
    "status_bar_height": 32,
    "screensaver": False,
    "idle_timeout_ms": 30000,
    "clock_move_interval_ms": 10000,
}
FIELDS = {
    "system_ui": set(SYSTEM_UI_DEFAULTS),
    "repositories": {"app", "kernel", "platform"},
    "display": {"width", "height", "cjk_font", "rotation", "brightness", "panel"},
    "keys": {"names", "single_min_ms", "double_gap_ms", "long_press_ms"},
    "components": {
        "network",
        "data",
        "display",
        "storage",
        "keys",
        "apps",
        "sqlite",
        "usb",
        "audio",
        "wireless",
    },
    "logging": {"enabled", "level"},
    "web": {"enabled", "port"},
    "app": {"startup", "grants"},
}


def require(condition, message):
    """Reject invalid settings before producing a build or touching application data."""
    if not condition:
        raise ValueError(message)


def integer(value, low, high, field):
    require(type(value) is int and low <= value <= high, f"{field}: integer {low}..{high} required")


def unique_object(pairs):
    """Do not silently accept duplicate JSON properties."""
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate configuration key: {key}")
        result[key] = value
    return result


def load_config(path, target="x86"):
    """Load the single product configuration; never merge stale generated files or defaults."""
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"), object_pairs_hook=unique_object)
    if isinstance(data, dict) and "system_ui" not in data:
        # Older product files retain their original full-screen behavior.
        data["system_ui"] = dict(SYSTEM_UI_DEFAULTS)
    if isinstance(data, dict) and isinstance(data.get("system_ui"), dict):
        for key, value in LIFECYCLE_DEFAULTS.items():
            data["system_ui"].setdefault(key, value)
    if isinstance(data, dict) and isinstance(data.get("components"), dict):
        data["components"].setdefault("data", target in ("x86", "kernel"))
        data["components"].setdefault("network", False)
    if isinstance(data, dict) and isinstance(data.get("display"), dict):
        data["display"].setdefault("panel", "am178" if target == "esp32s3" else "generic")
        # Old profiles keep Chinese song titles enabled.
        data["display"].setdefault("cjk_font", True)
        data["display"].setdefault("brightness", 100)
        # Preserve the old AM178 landscape mapping when a profile has no explicit angle.
        data["display"].setdefault(
            "rotation", 90 if target == "esp32s3" and data["display"].get("width") == (502 if data["display"]["panel"] == "am213" else 448) else 0
        )
    require(type(data) is dict and set(data) == {"format", *FIELDS}, "Unknown/missing top-level fields")
    require(type(data["format"]) is int and data["format"] == 1, "Unsupported q2.json format")
    for name, fields in FIELDS.items():
        require(type(data[name]) is dict and set(data[name]) == fields, f"Unknown/missing {name} fields")
    for name, path in data["repositories"].items():
        require(
            isinstance(path, str) and path and not any(c in path for c in ';\n\r"'),
            f"Invalid {name} repository path",
        )
    for name, value in data["components"].items():
        require(type(value) is bool, f"components.{name} must be boolean")
    for group in ("logging", "web"):
        require(type(data[group]["enabled"]) is bool, f"{group}.enabled must be boolean")
    panel = data["display"]["panel"]
    require(isinstance(panel, str) and panel in ("generic", "am178", "am213"),
            "display.panel must be generic, am178 or am213")
    require((target == "esp32s3" and panel in ("am178", "am213"))
            or (target != "esp32s3" and panel == "generic"), "display.panel does not match target")
    require(type(data["display"]["cjk_font"]) is bool, "display.cjk_font must be boolean")
    for axis in ("width", "height"):
        integer(data["display"][axis], 64, 1024, f"display.{axis}")
    integer(data["display"]["brightness"], 0, 100, "display.brightness")
    rotation = data["display"]["rotation"]
    require(type(rotation) is int and rotation in (0, 90, 180, 270),
            "display.rotation must be 0, 90, 180 or 270")
    require(target == "esp32s3" or rotation == 0, "Nonzero display.rotation requires ESP32-S3")
    ui = data["system_ui"]
    for field in ("status_bar", "screensaver", "lock_enabled"):
        require(type(ui[field]) is bool, f"system_ui.{field} must be boolean")
    integer(ui["status_bar_height"], 24, 64, "system_ui.status_bar_height")
    integer(ui["idle_timeout_ms"], 1000, 3600000, "system_ui.idle_timeout_ms")
    integer(ui["clock_move_interval_ms"], 1000, 3600000, "system_ui.clock_move_interval_ms")
    require(
        not ui["status_bar"] or ui["status_bar_height"] + 32 <= data["display"]["height"],
        "Status bar must leave at least 32 content pixels",
    )
    require(
        not (ui["status_bar"] or ui["screensaver"])
        or (data["components"]["display"] and target in ("x86", "kernel", "esp32s3")),
        "System UI requires an LVGL display backend",
    )
    integer(ui["unlock_action"], 1, 3, "system_ui.unlock_action")
    for key in ("status_left", "status_right", "saver_text"):
        require(
            type(ui[key]) is str and len(ui[key].encode("utf8")) < 128 and "\0" not in ui[key],
            f"system_ui.{key} must be a UTF-8 string shorter than 128 bytes",
        )
    require(
        type(ui["unlock_key"]) is str and ui["unlock_key"] in data["keys"]["names"],
        "system_ui.unlock_key must name a registered key",
    )
    require(not ui["lock_enabled"] or data["components"]["keys"], "Lock requires keys")
    keys = data["keys"]
    for name in ("single_min_ms", "double_gap_ms", "long_press_ms"):
        integer(keys[name], 1, 60000, f"keys.{name}")
    require(keys["long_press_ms"] > keys["single_min_ms"], "Long press must exceed minimum click duration")
    names = keys["names"]
    require(type(names) is list and 1 <= len(names) <= 32, "Register 1..32 key names")
    require(
        all(isinstance(n, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,30}", n) for n in names),
        "Invalid key name",
    )
    require(len(set(names)) == len(names), "Duplicate key names")
    require(
        isinstance(data["logging"]["level"], str) and data["logging"]["level"] in LEVELS,
        "Invalid logging.level",
    )
    integer(data["web"]["port"], 0, 65535, "web.port")
    require(
        isinstance(data["app"]["startup"], str)
        and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", data["app"]["startup"]),
        "Invalid startup APP directory",
    )
    grants = data["app"]["grants"]
    require(
        type(grants) is list
        and len(grants) <= 32
        and all(isinstance(g, str) and re.fullmatch(r"[a-z][a-z0-9_.]*", g) for g in grants),
        "Invalid grants",
    )
    require(len(set(grants)) == len(grants), "Duplicate grants")
    c = data["components"]
    require(not c["network"] or target in ("x86", "kernel"), "Network backend is x86 only")
    require(not c["audio"] or target in ("x86", "kernel"), "Audio backend is x86 only")
    require(not c["wireless"], "Wireless provider is not implemented")
    require(
        target == "kernel" or not c["usb"],
        "This platform has no USB DCD; USB is available in kernel tests only",
    )
    require(not data["web"]["enabled"] or c["keys"], "Web key simulator requires components.keys")
    if target == "x86":
        require(c["display"], "x86 window runner requires display; use host for a display-free runtime")
    elif target == "host":
        require(
            not c["data"] and not c["keys"] and not c["apps"] and not data["web"]["enabled"],
            "host supports text display/storage/sqlite; disable keys/apps/web for this target",
        )
    elif target == "esp32s3":
        require(
            c["display"]
            and c["apps"]
            and not any(v for k, v in c.items() if k not in ("display", "apps"))
            and not data["web"]["enabled"],
            "ESP32-S3 implements display/touch and factory apps; enable display/apps, disable other components/web",
        )
        native = (410, 502) if panel == "am213" else (368, 448)
        require(
            (data["display"]["width"], data["display"]["height"])
            == (native[::-1] if rotation in (90, 270) else native),
            f"{panel.upper()} rotation 0/180 requires {native[0]}x{native[1]}; "
            f"rotation 90/270 requires {native[1]}x{native[0]}",
        )
        require(
            data["app"]["startup"] == "homepage",
            "ESP32-S3 boots the resident homepage and embedded factory apps",
        )
    elif target in ("esp32", "esp32s31"):
        require(
            not any(c.values()) and not data["web"]["enabled"],
            f"{target.upper()} is a minimal port: "
            "disable all product components and web until drivers are implemented",
        )
    else:
        require(target == "kernel", "Unknown build target")
    return data


def repository_paths(config):
    """Paths are relative to the q2 workspace, even when selecting an external configuration file."""
    return {name: (ROOT / path).resolve() for name, path in config["repositories"].items()}


def generate(config, output, target):
    """Write derived C/CMake settings only when content changes, preserving incremental builds."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    ui = config["system_ui"]
    definitions = {
        "Q2_LOCK_ENABLED": int(ui["lock_enabled"]),
        "Q2_UNLOCK_ACTION": ui["unlock_action"],
        "Q2_STATUS_BAR_ENABLED": int(ui["status_bar"]),
        "Q2_STATUS_BAR_HEIGHT": ui["status_bar_height"],
        "Q2_SCREENSAVER_ENABLED": int(ui["screensaver"]),
        "Q2_IDLE_TIMEOUT_MS": ui["idle_timeout_ms"],
        "Q2_CLOCK_MOVE_INTERVAL_MS": ui["clock_move_interval_ms"],
        "Q2_DISPLAY_PANEL_AM213": int(config["display"]["panel"] == "am213"),
        "Q2_DISPLAY_WIDTH": config["display"]["width"],
        "Q2_DISPLAY_HEIGHT": config["display"]["height"],
        "Q2_DISPLAY_ROTATION": config["display"]["rotation"],
        "Q2_DISPLAY_BRIGHTNESS": config["display"]["brightness"],
        "Q2_KEY_SINGLE_MIN_MS": config["keys"]["single_min_ms"],
        "Q2_KEY_DOUBLE_GAP_MS": config["keys"]["double_gap_ms"],
        "Q2_KEY_LONG_PRESS_MS": config["keys"]["long_press_ms"],
        "Q2_DEFAULT_LOG_LEVEL": LEVELS[config["logging"]["level"]],
        **{"Q2_COMPONENT_" + name.upper(): int(value) for name, value in config["components"].items()},
        "Q2_WEB_ENABLED": int(config["web"]["enabled"]),
    }
    header = "/* Generated from q2.json. Edit the product configuration, not this file. */\n"
    header += "#ifndef Q2_PROJECT_CONFIG_H\n#define Q2_PROJECT_CONFIG_H\n"
    header += "".join(f"#define {key} {value}u\n" for key, value in definitions.items())
    for key in ("status_left", "status_right", "saver_text", "unlock_key"):
        header += f"#define Q2_{key.upper()} {json.dumps(ui[key], ensure_ascii=True)}\n"
    header += (
        "#define Q2_DEFAULT_KEY_NAMES {"
        + ", ".join(json.dumps(n) for n in config["keys"]["names"])
        + "}\n#endif\n"
    )
    c = config["components"]
    cmake = "# Generated product options; imported only by platform/product CMake.\n"
    options = {
        "Q2_WITH_STORAGE": c["storage"],
        "Q2_WITH_LVGL": c["display"] and target != "host",
        "Q2_WITH_SQLITE": c["sqlite"],
        "Q2_WITH_USB": c["usb"],
        "Q2_ENABLE_LOG": config["logging"]["enabled"],
        "Q2_ENABLE_CJK_FONT": config["display"]["cjk_font"],
        "Q2_BUILD_LVGL_TESTS": c["display"] and target in ("x86", "kernel"),
        "Q2_BUILD_KEYS_TESTS": True,
        "Q2_BUILD_AUDIO_TESTS": c["audio"],
        "Q2_BUILD_APPS_TESTS": True,
        "Q2_BUILD_LOG_TESTS": True,
        "Q2_BUILD_TESTS": target == "kernel" and c["storage"] and c["sqlite"] and c["usb"],
    }
    for key, value in options.items():
        cmake += f'set({key} {"ON" if value else "OFF"} CACHE BOOL "Product setting" FORCE)\n'
    for name, path in repository_paths(config).items():
        cmake += f'set(Q2_{name.upper()}_DIR "{path.as_posix()}" CACHE PATH "Explicit repository" FORCE)\n'
    for name, content in {
        "q2_project_config.h": header,
        "project.cmake": cmake,
        "resolved.json": json.dumps(config, indent=2) + "\n",
    }.items():
        path = output / name
        if not path.exists() or path.read_text(encoding="utf8") != content:
            path.write_text(content, encoding="utf8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--target", default="x86")
    args = parser.parse_args()
    try:
        generate(load_config(args.config, args.target), args.output, args.target)
    except (ValueError, OSError) as error:
        parser.exit(2, f"Q2 configuration error: {error}\n")
