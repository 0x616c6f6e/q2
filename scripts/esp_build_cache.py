"""Preserve SDK configuration while isolating incompatible ESP-IDF CMake caches."""

from datetime import datetime
import json
import os
from pathlib import Path
import shutil


def cache_values(path):
    """Read only CMake key/value entries; a partially configured cache is valid input."""
    if not path.is_file():
        return {}
    result = {}
    for line in path.read_text(encoding="utf8", errors="replace").splitlines():
        if not line or line.startswith(("#", "//")) or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.split(":", 1)[0]] = value
    return result


def same_path(left, right):
    """CMake uses forward slashes on Windows; normalize case and separators before comparing."""
    return os.path.normcase(str(Path(left).resolve())) == os.path.normcase(str(Path(right).resolve()))


def prepare_esp_build(build, sdk, source, python, target):
    """Archive incompatible generated state, keeping sdkconfig; return the backup path or None.

    Inspect bootloader separately: an interrupted SDK switch can already have rewritten the
    main cache, while the nested bootloader still points at the old SDK source directory.
    No recursive deletion is used; the complete previous build remains recoverable.
    """
    build, sdk, source = Path(build).resolve(), Path(sdk).resolve(), Path(source).resolve()
    root = cache_values(build / "CMakeCache.txt")
    boot = cache_values(build / "bootloader/CMakeCache.txt")
    reasons = []
    for label, values, expected in (
        ("main", root, {"CMAKE_HOME_DIRECTORY": source, "IDF_PATH": sdk, "PYTHON": python}),
        (
            "bootloader",
            boot,
            {
                "CMAKE_HOME_DIRECTORY": sdk / "components/bootloader/subproject",
                "IDF_PATH": sdk,
                "PYTHON": python,
            },
        ),
    ):
        for key, value in expected.items():
            if values.get(key) and not same_path(values[key], value):
                reasons.append(f"{label} {key}: {values[key]} -> {value}")
        if values.get("IDF_TARGET") and values["IDF_TARGET"] != target:
            reasons.append(f"{label} IDF_TARGET: {values['IDF_TARGET']} -> {target}")
    description = build / "project_description.json"
    if description.is_file():
        try:
            old_sdk = json.loads(description.read_text(encoding="utf8")).get("idf_path")
        except (ValueError, OSError):
            old_sdk = None
        if old_sdk and not same_path(old_sdk, sdk):
            reasons.append(f"project idf_path: {old_sdk} -> {sdk}")
    if not reasons:
        return None
    # Refuse source roots/ancestors even if someone has configured in-source before.
    if (
        (build / "CMakeLists.txt").exists()
        or (build / ".git").exists()
        or any(p.is_relative_to(build) for p in (sdk, source))
    ):
        raise ValueError("Refusing to archive a source directory; choose a dedicated --build-dir")
    backup = build.with_name(build.name + ".sdk-backup-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
    print("Q2: incompatible ESP build cache:\n  " + "\n  ".join(reasons), flush=True)
    build.rename(backup)
    print(f"Q2: previous build preserved at {backup}", flush=True)
    build.mkdir()
    # Keep user menuconfig settings byte-for-byte; all CMake/compiler paths are regenerated.
    for name in ("sdkconfig", "sdkconfig.old"):
        if (backup / name).is_file():
            shutil.copy2(backup / name, build / name)
    return backup
