"""Product CLI profiles and transactional configuration management (Python standard library only)."""

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

from scripts.project_config import ROOT, load_config, require, unique_object

ESP_TARGETS = ("esp32", "esp32s31", "esp32s3")
TARGETS = ("x86", "host", "kernel", *ESP_TARGETS)


@dataclass(frozen=True)
class Profile:
    """A product preset selects a target, one JSON source and its own build cache."""

    target: str
    file: str
    build_name: str
    description: str


PROFILES = {
    "x86-linux": Profile(
        "x86", "q2.linux.json", "x86", "Linux SDL2; HTTP/HTTPS; no audio backend"
    ),
    "x86-windows": Profile(
        "x86", "q2.json", "x86", "Windows window; HTTP/HTTPS and audio"
    ),
    "esp32s3-am178": Profile(
        "esp32s3", "q2.esp32s3.json", "esp32s3", "AM178 display/touch and factory apps"
    ),
    "esp32s3-am213": Profile(
        "esp32s3", "q2.esp32s3-am213.json", "esp32s3-am213", "AM213 display/touch and factory apps"
    ),
    "host": Profile(
        "host", "q2.host.json", "host", "Portable text runtime; device-info app"
    ),
    "kernel": Profile(
        "kernel", "q2.kernel.json", "kernel", "Portable contract tests, including fake USB DCD"
    ),
    "esp32": Profile(
        "esp32", "q2.esp32.json", "esp32", "Minimal ESP32 SDK port; product peripherals not implemented"
    ),
    "esp32s31": Profile(
        "esp32s31", "q2.esp32s31.json", "esp32s31", "Minimal SDK port; product peripherals not implemented"
    ),
}


def default_profile(target):
    """Choose host defaults without modifying any product configuration."""
    if target == "x86":
        return "x86-linux" if sys.platform == "linux" else "x86-windows"
    return "esp32s3-am178" if target == "esp32s3" else target


def select_config(args):
    """Resolve explicit target/profile/config; reject ambiguous mismatched selections."""
    if args.profile:
        profile = PROFILES[args.profile]
        require(args.target is None or args.target == profile.target, "--target conflicts with --profile")
        args.target = profile.target
    if args.config:
        args.config = args.config.resolve()
        # Known product files can select a platform even when invoked from another directory.
        matches = [name for name, p in PROFILES.items() if ROOT / p.file == args.config]
        if matches and args.target is None:
            args.target = PROFILES[matches[0]].target
        if matches and args.profile is None and args.target == PROFILES[matches[0]].target:
            args.profile = matches[0]
    args.target = args.target or "x86"
    args.profile = args.profile or default_profile(args.target)
    if args.config is None:
        args.config = (ROOT / PROFILES[args.profile].file).resolve()
    return load_config(args.config, args.target)


def build_directory(args):
    """Isolate OS, panel presets and custom configurations, while honoring --build-dir."""
    if args.build_dir:
        return args.build_dir.resolve()
    profile = PROFILES[args.profile]
    name = profile.build_name
    if args.config != (ROOT / profile.file).resolve():
        # Different external files can share a basename; include the absolute source identity.
        digest = hashlib.sha256(str(args.config).encode("utf8")).hexdigest()[:10]
        name = f"{args.target}-custom-{digest}"
    parent = ROOT / "build" if os.name == "nt" else ROOT / "build" / sys.platform
    return parent / name


def list_profiles():
    """List presets, not claims that the local SDK or hardware has been verified."""
    print(f"{'PROFILE':20} {'PLATFORM':10} {'CONFIG':24} DESCRIPTION")
    for name, p in PROFILES.items():
        print(f"{name:20} {p.target:10} {p.file:24} {p.description}")


def write_config(config, destination, target, overwrite=False):
    """Validate the complete candidate before atomically publishing it; preserve invalid edits."""
    destination = Path(destination).resolve()
    require(overwrite or not destination.exists(), f"Configuration already exists: {destination}")
    require(destination.parent.is_dir(), f"Output parent directory does not exist: {destination.parent}")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf8", newline="\n", dir=destination.parent, suffix=".json", delete=False
        ) as stream:
            temporary = Path(stream.name)
            json.dump(config, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        load_config(temporary, target)
        if overwrite:
            os.replace(temporary, destination)
        else:
            # Hard-link publication cannot overwrite a file created by another process.
            os.link(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def update_config(config, assignments):
    """Apply dotted-key JSON values together, allowing related fields to change in one transaction."""
    seen = set()
    for assignment in assignments:
        key, separator, encoded = assignment.partition("=")
        require(
            separator and key,
            'Use KEY=JSON_VALUE, e.g. display.brightness=80 or logging.level="debug"',
        )
        require(key not in seen, f"Duplicate assignment: {key}")
        seen.add(key)
        parts = key.split(".")
        current = config
        for part in parts[:-1]:
            require(isinstance(current, dict) and part in current, f"Unknown configuration key: {key}")
            current = current[part]
        require(isinstance(current, dict) and parts[-1] in current, f"Unknown configuration key: {key}")
        current[parts[-1]] = json.loads(encoded, object_pairs_hook=unique_object)
    return config


def config_main(argv):
    """Manage configurations without a compiler, ESP-IDF or initialized child checkouts."""
    parser = argparse.ArgumentParser(
        prog="q2.py config", description="List, inspect, validate or edit product JSON"
    )
    commands = parser.add_subparsers(dest="operation", required=True)
    commands.add_parser("list", help="List platform presets")
    for operation in ("show", "validate", "init", "set"):
        sub = commands.add_parser(operation)
        sub.add_argument("--target", "--platform", choices=TARGETS)
        sub.add_argument("--profile", choices=PROFILES)
        sub.add_argument("--config", type=Path)
        if operation in ("init", "set"):
            sub.add_argument("--output", type=Path, help="Write a new config instead of editing the source")
        if operation == "set":
            sub.add_argument("assignments", nargs="+", metavar="KEY=JSON_VALUE")
    args = parser.parse_args(argv)
    if args.operation == "list":
        list_profiles()
        return
    config = select_config(args)
    if args.operation == "show":
        print(json.dumps(config, indent=2, ensure_ascii=False))
    elif args.operation == "validate":
        print(f"OK platform={args.target} config={args.config}")
    else:
        destination = args.output or (ROOT / "q2.local.json" if args.operation == "init" else args.config)
        if args.operation == "set":
            update_config(config, args.assignments)
        write_config(
            config, destination, args.target, overwrite=args.operation == "set" and args.output is None
        )
        print(f"Saved platform={args.target} config={destination.resolve()}")
