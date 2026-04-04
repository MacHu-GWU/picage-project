# -*- coding: utf-8 -*-

"""
Pytest fixtures that build a temporary fake site-packages directory covering
every supported installation format.


Two-tier file organisation
--------------------------

``tests/test-site-packages/`` (committed to the repo, static)
    Contains only the **package source trees** — the ``mypkg_*/`` directories
    full of ``.py`` files.  These never mention an absolute path, so they work
    identically on every machine and checkout location.

    flat_src/mypkg_flat/          source tree for flat dist-info install
    egg_link_src/mypkg_egg_link/  source tree for legacy .egg-link editable
    pth_src/mypkg_pth/            source tree for PEP 660 Strategy A editable
    finder_src/mypkg_finder/      source tree for PEP 660 Strategy B editable

The egg-directory format (Format 5) is **not** stored on disk.  The ``.egg``
directory name embeds the Python version tag (e.g. ``py3.10``), and
``*.egg`` is listed in ``.gitignore``.  The ``fake_sp`` fixture therefore
builds the egg directory structure from scratch under ``tmp_path`` at test
time, which works on every Python version without any committed binary blobs.

``tmp_path/site-packages/`` (generated at test time by the ``fake_sp`` fixture)
    Contains the **format-specific metadata files** that must embed the
    absolute path of the source tree for the current machine:

    * ``.egg-link`` — first line is an absolute path to the source tree.
    * ``.pth`` (Strategy A) — first line is an absolute path to the source tree.
    * ``.dist-info/`` — metadata directory for flat installs (no absolute path,
      but created here for completeness and isolation).

    These files cannot be committed to the repo because their content changes
    with every checkout location.


Why Strategy B needs no files in site-packages
-----------------------------------------------

The real PEP 660 Strategy B mechanism works as follows at interpreter startup:

    1. Python reads ``__editable__.<pkg>-<ver>.pth`` from site-packages.
    2. That file executes ``import __editable___<pkg>_<ver>_finder``.
    3. The finder module registers a :class:`~importlib.abc.MetaPathFinder`
       into ``sys.meta_path`` whose ``MAPPING`` dict maps the package name to
       its source directory.
    4. Any subsequent call to ``importlib.util.find_spec("<pkg>")`` is
       intercepted by the registered finder and returns the correct spec.

``picage.model`` never reads or executes those ``.pth`` / finder files itself.
It only calls ``importlib.util.find_spec(root)`` (step 4 above).  The test for
Strategy B therefore skips steps 1–3 and achieves the same observable outcome
by passing ``extra_sys_path=[finder_src]`` to the ``Package`` / ``Module``
constructor, which causes ``_resolve_via_importlib`` to temporarily prepend
``finder_src`` to ``sys.path`` before calling ``find_spec``.  The standard
:class:`~importlib.machinery.FileFinder` then finds the package there, just as
the custom MetaPathFinder would in a real install.

The same reasoning applies to the egg-directory format: instead of relying on
``easy-install.pth`` having been processed at interpreter startup (which adds
the ``.egg`` directory to ``sys.path``), the test passes
``extra_sys_path=[egg_dir]`` directly.
"""

import sys
import shutil
import pytest
from pathlib import Path

# Root of the static fake-package source trees committed to the repo.
_TSP = Path(__file__).parent / "test-site-packages"

# Each format's source root and the import name of its top-level package.
_FORMATS = {
    "flat": (_TSP / "flat_src", "mypkg_flat"),
    "egg_link": (_TSP / "egg_link_src", "mypkg_egg_link"),
    "pth": (_TSP / "pth_src", "mypkg_pth"),
    "finder": (_TSP / "finder_src", "mypkg_finder"),
}


def _build_egg_dir(base: Path) -> Path:
    """
    Create a minimal ``mypkg_egg_dir-1.0.0-pyX.Y.egg`` directory under *base*
    and return its path.

    The egg name embeds the running interpreter's major/minor version so that
    Python's import machinery recognises it as compatible.  The structure
    mirrors a real ``python setup.py bdist_egg`` output::

        mypkg_egg_dir-1.0.0-pyX.Y.egg/
            EGG-INFO/
                PKG-INFO
                top_level.txt
            mypkg_egg_dir/
                __init__.py
                _internal.py
                api.py
                commands/
                    __init__.py
                    _base.py
                    install.py
                    uninstall.py
                    advanced/
                        __init__.py
                        _cache.py
                        solver.py
                utils/
                    __init__.py
                    _helpers.py
                    number_utils.py
                    string_utils.py
    """
    ver = f"{sys.version_info.major}.{sys.version_info.minor}"
    egg = base / f"mypkg_egg_dir-1.0.0-py{ver}.egg"

    # EGG-INFO
    egg_info = egg / "EGG-INFO"
    egg_info.mkdir(parents=True)
    (egg_info / "PKG-INFO").write_text(
        "Metadata-Version: 1.0\nName: mypkg-egg-dir\nVersion: 1.0.0\n"
        "Summary: Fake egg-directory package for testing.\n"
    )
    (egg_info / "top_level.txt").write_text("mypkg_egg_dir\n")

    # mypkg_egg_dir (root package)
    pkg = egg / "mypkg_egg_dir"
    pkg.mkdir()
    (pkg / "__init__.py").write_text('# mypkg_egg_dir\n__version__ = "1.0.0"\n')
    (pkg / "_internal.py").write_text(
        "# Private implementation details — not part of the public API.\n"
        "_REGISTRY: dict = {}\n"
    )
    (pkg / "api.py").write_text(
        "# Public API surface for mypkg_egg_dir.\n"
        "def get_version() -> str:\n"
        "    from . import __version__\n"
        "    return __version__\n"
    )

    # commands sub-package
    cmd = pkg / "commands"
    cmd.mkdir()
    (cmd / "__init__.py").write_text(
        "# Command registry for mypkg_egg_dir.\nCOMMANDS: dict = {}\n"
    )
    (cmd / "_base.py").write_text(
        "# Base class for all commands — internal, not part of public API.\n"
        "class BaseCommand:\n"
        "    name: str = ''\n"
        "    def execute(self) -> None:\n"
        "        raise NotImplementedError\n"
    )
    (cmd / "install.py").write_text(
        "# Install command implementation.\n"
        "def run(package: str, version: str = 'latest') -> bool:\n"
        "    return True\n"
    )
    (cmd / "uninstall.py").write_text(
        "# Uninstall command implementation.\n"
        "def run(package: str, force: bool = False) -> bool:\n"
        "    return True\n"
    )

    # commands/advanced sub-package
    adv = cmd / "advanced"
    adv.mkdir()
    (adv / "__init__.py").write_text("# Advanced commands — experimental features.\n")
    (adv / "_cache.py").write_text(
        "# Internal caching layer for the solver — not public.\n"
        "_CACHE: dict = {}\n\n"
        "def invalidate() -> None:\n"
        "    _CACHE.clear()\n"
    )
    (adv / "solver.py").write_text(
        "# Dependency solver.\n"
        "def solve(requirements: list[str]) -> list[str]:\n"
        "    return sorted(set(requirements))\n"
    )

    # utils sub-package
    utils = pkg / "utils"
    utils.mkdir()
    (utils / "__init__.py").write_text("# Utility helpers for mypkg_egg_dir.\n")
    (utils / "_helpers.py").write_text(
        "# Internal utilities — not exported from the utils package.\n"
        "def _coerce(value) -> str:\n"
        "    return str(value)\n"
    )
    (utils / "number_utils.py").write_text(
        "# Numeric helpers.\n"
        "def clamp(value: float, lo: float, hi: float) -> float:\n"
        "    return max(lo, min(hi, value))\n\n"
        "def is_even(n: int) -> bool:\n"
        "    return n % 2 == 0\n"
    )
    (utils / "string_utils.py").write_text(
        "# String manipulation utilities.\n"
        "def slugify(text: str) -> str:\n"
        "    return text.lower().replace(' ', '-')\n\n"
        "def truncate(text: str, max_len: int = 80) -> str:\n"
        "    return text[:max_len] if len(text) > max_len else text\n"
    )

    return egg


@pytest.fixture()
def fake_sp(tmp_path: Path) -> dict:
    """
    Build a complete fake site-packages directory under *tmp_path* and return
    a dict with the paths needed by tests.

    Returned keys:

    ``sp_dir``
        Absolute path of the fake site-packages directory.  Pass as
        ``sp_dir=`` to :class:`~picage.model.Package` /
        :class:`~picage.model.Module`.

    ``finder_src``
        Directory containing ``mypkg_finder/``.  Pass as
        ``extra_sys_path=[info["finder_src"]]`` to exercise the importlib
        Strategy-B path.

    ``egg_dir``
        Path to the ``mypkg_egg_dir-*.egg`` directory.  Pass as
        ``extra_sys_path=[info["egg_dir"]]`` to exercise the egg-directory
        path.
    """
    sp = tmp_path / "site-packages"
    sp.mkdir()

    # ------------------------------------------------------------------
    # Format 1: flat dist-info install
    # The package directory is copied directly into site-packages.
    # ------------------------------------------------------------------
    flat_src, flat_name = _FORMATS["flat"]
    shutil.copytree(flat_src / flat_name, sp / flat_name)
    dist_info = sp / "mypkg-flat-1.0.0.dist-info"
    dist_info.mkdir()
    (dist_info / "METADATA").write_text(
        "Metadata-Version: 2.3\nName: mypkg-flat\nVersion: 1.0.0\n"
    )
    (dist_info / "INSTALLER").write_text("pip\n")
    (dist_info / "WHEEL").write_text(
        "Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: true\n"
    )

    # ------------------------------------------------------------------
    # Format 2: legacy .egg-link editable install
    # A <name>.egg-link file in site-packages whose first line is the
    # path to the source tree.  A second line "." is conventional.
    # ------------------------------------------------------------------
    egg_link_src, _ = _FORMATS["egg_link"]
    (sp / "mypkg-egg-link.egg-link").write_text(
        str(egg_link_src) + "\n.\n"
    )
    # easy-install.pth adds the source tree to sys.path at startup.
    (sp / "easy-install.pth").write_text(str(egg_link_src) + "\n")

    # ------------------------------------------------------------------
    # Format 3: PEP 660 Strategy A — plain path-insertion .pth file
    # A <name>.pth file whose first line is an absolute directory path.
    # ------------------------------------------------------------------
    pth_src, _ = _FORMATS["pth"]
    (sp / "mypkg-pth.pth").write_text(str(pth_src) + "\n")

    # ------------------------------------------------------------------
    # Format 4: PEP 660 Strategy B — importlib custom finder (uv / setuptools)
    # No files are written to site-packages; the caller passes finder_src
    # via extra_sys_path so that importlib.util.find_spec can locate the
    # package.  This mirrors what the __editable__ finder registration
    # achieves at interpreter startup in real installs.
    # ------------------------------------------------------------------
    finder_src, _ = _FORMATS["finder"]
    # (no site-packages files needed)

    # ------------------------------------------------------------------
    # Format 5: egg directory install
    # The .egg directory name embeds the Python version tag (e.g. py3.10)
    # and *.egg is listed in .gitignore, so we build the directory
    # programmatically at test time rather than committing it to the repo.
    # ------------------------------------------------------------------
    egg_dir = _build_egg_dir(tmp_path)

    return {
        "sp_dir": str(sp),
        "finder_src": str(finder_src),
        "egg_dir": str(egg_dir),
    }
