"""Pack the AnimeFlow project into a single ZIP archive for local use.

Usage:
    python pack_project.py

Produces ``AnimeFlow_Full_Project.zip`` in the project root, containing all
source files, templates, static assets and the SQLite database, while
skipping virtual environments, Python caches and Replit/IDE metadata.
"""
import os
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ARCHIVE_NAME = "AnimeFlow_Final_Ultra.zip"
ARCHIVE_PATH = ROOT / ARCHIVE_NAME

IGNORED_DIRS = {
    "venv",
    ".venv",
    "env",
    "__pycache__",
    ".replit",
    ".local",
    ".cache",
    ".git",
    ".pythonlibs",
    ".upm",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "attached_assets",
}

IGNORED_FILES = {
    ARCHIVE_NAME,
    ".replit",
    "replit.nix",
    ".gitignore",
    ".DS_Store",
}

IGNORED_SUFFIXES = {".pyc", ".pyo", ".pyd", ".log"}


def _should_skip_dir(dirname: str) -> bool:
    return dirname in IGNORED_DIRS or dirname.startswith(".")


def _should_skip_file(filename: str) -> bool:
    if filename in IGNORED_FILES:
        return True
    suffix = os.path.splitext(filename)[1].lower()
    if suffix in IGNORED_SUFFIXES:
        return True
    return False


def main() -> int:
    if ARCHIVE_PATH.exists():
        ARCHIVE_PATH.unlink()

    files_added = 0
    total_bytes = 0

    print("[pack] Создаю архив: {}".format(ARCHIVE_PATH.name))

    with zipfile.ZipFile(
        ARCHIVE_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6
    ) as zf:
        for current_dir, dirs, files in os.walk(ROOT):
            # In-place prune of ignored directories so os.walk skips them.
            dirs[:] = [d for d in dirs if not _should_skip_dir(d)]

            for fname in files:
                if _should_skip_file(fname):
                    continue
                fpath = Path(current_dir) / fname
                if fpath.resolve() == ARCHIVE_PATH:
                    continue
                rel = fpath.relative_to(ROOT)
                # Wrap everything inside an "AnimeFlow/" top-level folder so
                # the archive expands cleanly on the user's machine.
                arcname = os.path.join("AnimeFlow", str(rel))
                zf.write(fpath, arcname)
                files_added += 1
                try:
                    total_bytes += fpath.stat().st_size
                except OSError:
                    pass

    size_mb = ARCHIVE_PATH.stat().st_size / (1024 * 1024)
    src_mb = total_bytes / (1024 * 1024)
    print("[pack] Готово: {} файлов, исходный размер {:.2f} МБ, архив {:.2f} МБ".format(
        files_added, src_mb, size_mb
    ))
    print("[pack] Путь к архиву: {}".format(ARCHIVE_PATH))
    return 0


if __name__ == "__main__":
    sys.exit(main())
