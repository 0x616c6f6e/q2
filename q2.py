"""Unified Q2 entry: platform/config management, build/run/test/pack and ESP-IDF tools."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from scripts.entry_config import (
    ESP_TARGETS,
    PROFILES,
    TARGETS,
    build_directory,
    config_main,
    list_profiles,
    select_config,
)
from scripts.esp_build_cache import prepare_esp_build
from scripts.project_config import ROOT, generate, repository_paths, require


def command(args, **kwargs):
    """Use argument arrays so paths with spaces never become shell code."""
    print("+ " + subprocess.list2cmdline([str(x) for x in args]), flush=True)
    subprocess.run([str(x) for x in args], check=True, **kwargs)


def configure(args, config, build):
    """Configure the root product; all generated paths are scoped to this build directory."""
    cmake = [
        args.cmake,
        "-S",
        ROOT,
        "-B",
        build,
        "-G",
        "Ninja",
        f"-DQ2_TARGET={args.target}",
        f"-DQ2_CONFIG_FILE={args.config}",
        f"-DPython3_EXECUTABLE={sys.executable}",
    ]
    if args.compiler:
        compiler = Path(shutil.which(args.compiler) or args.compiler).resolve()
        cmake += [f"-DCMAKE_C_COMPILER={compiler}"]
        if compiler.stem == "zig":
            cmake += ["-DCMAKE_C_COMPILER_ARG1=cc"]
    if args.ninja:
        cmake += [f"-DCMAKE_MAKE_PROGRAM={Path(shutil.which(args.ninja) or args.ninja).resolve()}"]
    command(cmake)


def pack(config, paths, single=None):
    """Delegate package format/UUID ownership to the independent app repository."""
    dist = ROOT / "dist"
    if single:
        command(
            [
                sys.executable,
                paths["app"] / "scripts/q2app.py",
                "pack",
                paths["app"] / "apps" / single,
                "-o",
                dist / (single + ".q2app"),
            ]
        )
        return None
    command([sys.executable, paths["app"] / "scripts/q2app.py", "factory", paths["app"], "-o", dist])
    return json.loads((dist / "factory.json").read_text(encoding="utf8"))


def check_app(config, name, managed, target):
    """Reject required unavailable capabilities before opening windows or persistent media."""
    manifest = json.loads((ROOT / "dist" / (name + ".run") / "manifest.json").read_text(encoding="utf8"))
    c = config["components"]
    available = {"system.info"}
    if c["display"]:
        available.add("display.text")
        if target == "x86":
            available.update({"display.ui", "system.ui.read", "screensaver.inhibit"})
    if c["audio"] and target == "x86":
        available.add("audio.playback")
    if c["network"] and target == "x86":
        available.add("network.http")
    if c["data"]:
        available.update({"data.read", "power.read", "wireless.read", "clock.read"})
    if c["storage"]:
        available.add("storage.private")
    if c["keys"]:
        available.add("input.keys")
    if c["sqlite"]:
        available.add("storage.database")
    if config["logging"]["enabled"]:
        available.add("system.log")
    if managed:
        available.update({"system.lifecycle", "system.settings"})
        available.update({"apps.list", "apps.launch", "apps.navigate", "appearance.read", "appearance.write"})
    missing = set(manifest["capabilities"]["required"]) - (available & set(config["app"]["grants"]))
    require(not missing, f"APP {name} requires disabled/ungranted capabilities: {', '.join(sorted(missing))}")


def run(args, config, paths, build):
    """Launch a product or standalone app using root dist and root persistent data."""
    require(args.target in ("x86", "host"), "run currently supports x86 and host")
    name = args.app or config["app"]["startup"]
    require(name and all(c.isalnum() or c in "_-" for c in name), "Invalid APP directory")
    managed = args.target == "x86" and config["components"]["apps"] and not args.single_app
    catalog = pack(config, paths, None if managed else name)
    check_app(config, name, managed, args.target)
    if managed and name != catalog["default_app"]:
        check_app(config, catalog["default_app"], True, args.target)
    suffix = ".exe" if os.name == "nt" else ""
    argv = [build / "bin" / ("q2_" + args.target + suffix)]

    def app_files(app):
        return [ROOT / "dist" / (app + ".run") / p for p in ("manifest.json", "main.lua")]

    argv += app_files(name)
    if args.target == "host":
        command(argv + config["app"]["grants"])
        return
    if managed:
        entries = catalog["apps"]
        require(any(a["directory"] == name for a in entries), "Startup APP is absent from factory.json")
        home = next(a for a in entries if a["directory"] == catalog["default_app"])
        check_app(config, home["directory"], True, args.target)
        argv += ["--home", home["id"]]
        for entry in entries:
            if entry["directory"] == name:
                if entry["factory"]:
                    argv += ["--initial-factory"]
            else:
                argv += ["--factory-app" if entry["factory"] else "--app", *app_files(entry["directory"])]
    if config["components"]["storage"]:
        argv += ["--storage-file", args.storage_file or build / "app-data.lfs"]
    if config["web"]["enabled"] and not args.disable_web:
        argv += ["--web-port", str(config["web"]["port"])]
    argv += ["--log-level", config["logging"]["level"] if config["logging"]["enabled"] else "off"]
    for grant in config["app"]["grants"]:
        argv += ["--grant", grant]
    if args.headless:
        argv += ["--headless", "--frames", str(args.frames or 30)]
    elif args.frames:
        argv += ["--frames", str(args.frames)]
    if args.capture:
        argv += ["--capture", args.capture]
    command(argv)


def esp_build(args, config, paths, build):
    """Share generated configuration across ESP actions; only run/flash writes the device."""
    require(
        args.action in ("configure", "build", "menuconfig", "run", "flash", "monitor"),
        "ESP supports configure/build/menuconfig/run/flash/monitor",
    )
    if args.action in ("run", "flash", "monitor"):
        require(
            args.port and args.port.strip(), "Specify --port /dev/ttyUSB0 (Windows: COM3), or set Q2_PORT"
        )
    require(os.environ.get("IDF_PATH"), "Activate the ESP-IDF environment first")
    sdk = Path(os.environ["IDF_PATH"]).resolve()
    require((sdk / "tools/idf.py").is_file(), "IDF_PATH does not contain tools/idf.py")
    prepare_esp_build(build, sdk, paths["platform"] / args.target, sys.executable, args.target)
    generate(config, build / "generated", args.target)
    base = [
        sys.executable,
        sdk / "tools/idf.py",
        "-C",
        paths["platform"] / args.target,
        "-B",
        build,
        "-D",
        f"Q2_KERNEL_DIR={paths['kernel']}",
        "-D",
        f"Q2_GENERATED_DIR={build / 'generated'}",
        "-D",
        f"SDKCONFIG={build / 'sdkconfig'}",
    ]
    actions = ["reconfigure" if args.action == "configure" else args.action]
    if args.action == "run":
        actions = ["monitor"] if args.monitor_only else ["flash"] if args.flash_only else ["flash", "monitor"]
    # Separate calls keep a flash baud override from changing the monitor baud.
    # A failed build/flash raises before monitor can connect to a stale firmware image.
    for action in actions:
        argv = list(base)
        if action in ("flash", "monitor"):
            argv += ["-p", args.port]
        if action == "flash" and args.baud is not None:
            argv += ["-b", str(args.baud)]
        argv.append(action)
        if action == "monitor" and args.monitor_baud is not None:
            argv += ["--monitor-baud", str(args.monitor_baud)]
        command(argv)


def main(argv=None):
    """Dispatch management before build dependencies; keep existing script arguments compatible."""
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "config":
        config_main(argv[1:])
        return
    parser = argparse.ArgumentParser(description=__doc__, epilog="Configuration: q2.py config --help")
    parser.add_argument(
        "action",
        choices=("configure", "build", "run", "test", "pack", "menuconfig", "flash", "monitor", "platforms"),
    )
    parser.add_argument("--target", "--platform", choices=TARGETS, help="Platform (default: host x86)")
    parser.add_argument("--profile", choices=PROFILES, help="Platform/configuration preset")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--build-dir", type=Path)
    parser.add_argument("--cmake", default=os.environ.get("Q2_CMAKE", "cmake"))
    parser.add_argument("--compiler", default=os.environ.get("Q2_CC", ""))
    parser.add_argument("--ninja", default=os.environ.get("Q2_NINJA", ""))
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--app")
    parser.add_argument("--single-app", action="store_true")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--frames", type=int, default=0)
    parser.add_argument("--capture", type=Path)
    parser.add_argument("--storage-file", type=Path)
    parser.add_argument("--disable-web", action="store_true")
    parser.add_argument(
        "-p",
        "--port",
        default=os.environ.get("Q2_PORT") or os.environ.get("ESPPORT"),
        help="ESP serial port, e.g. /dev/ttyUSB0 or COM3; default Q2_PORT / ESPPORT",
    )
    parser.add_argument("--baud", type=int, help="ESP flashing baud (monitor rate is independent)")
    parser.add_argument("--monitor-baud", type=int, help="Monitor baud; otherwise use ESP-IDF/SDK defaults")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--monitor-only", action="store_true", help="ESP run: monitor without flashing")
    mode.add_argument("--flash-only", action="store_true", help="ESP run: flash without starting monitor")
    args = parser.parse_args(argv)
    if args.action == "platforms":
        list_profiles()
        return
    config = select_config(args)
    is_esp = args.target in ESP_TARGETS
    require(
        args.action not in ("menuconfig", "flash", "monitor") or is_esp,
        "menuconfig/flash/monitor require an ESP target",
    )
    require(
        not (args.monitor_only or args.flash_only) or (is_esp and args.action == "run"),
        "--monitor-only/--flash-only require run with an ESP target",
    )
    require(
        all(value is None or value > 0 for value in (args.baud, args.monitor_baud)),
        "Serial baud rates must be positive",
    )
    paths = repository_paths(config)
    for name, path in paths.items():
        require(path.is_dir(), f"Missing independent {name} checkout: {path}")
    require(args.jobs > 0 and 0 <= args.frames <= 1000000, "Invalid jobs/frames")
    build = build_directory(args)
    require(
        not any(path.is_relative_to(build) for path in (ROOT, *paths.values())),
        "Build directory cannot be a repository root or its ancestor",
    )
    require(args.action != "run" or args.target != "kernel", "kernel is a test target; use test, not run")
    if args.action == "pack":
        pack(config, paths)
        return
    require(
        args.target != "x86" or os.name == "nt" or sys.platform == "linux",
        "The x86 GUI backend supports Windows and Linux; use --target host or kernel elsewhere",
    )
    if args.target == "x86" and sys.platform == "linux":
        require(
            not config["components"]["audio"],
            "Linux SDL2 audio backend is not yet implemented; "
            "disable components.audio (see q2.linux.json)",
        )
    if args.target in ESP_TARGETS:
        esp_build(args, config, paths, build)
        return
    configure(args, config, build)
    if args.action == "configure":
        return
    command([args.cmake, "--build", build, "--parallel", args.jobs])
    if args.action == "run":
        run(args, config, paths, build)
    elif args.action == "test":
        ctest = (
            Path(shutil.which(args.cmake) or args.cmake)
            .resolve()
            .with_name("ctest.exe" if os.name == "nt" else "ctest")
        )
        command([ctest, "--test-dir", build, "--output-on-failure"])
        command([sys.executable, paths["kernel"] / "scripts/check_contracts.py"])
        command([sys.executable, paths["app"] / "scripts/test_apps.py"])


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Q2: {error}", file=sys.stderr)
        sys.exit(1)
