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
    egg_dir_src/
      mypkg_egg_dir-1.0.0-py3.12.egg/
        EGG-INFO/                 egg metadata
        mypkg_egg_dir/            package inside the .egg directory

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

_EGG_DIR = (
    _TSP
    / "egg_dir_src"
    / f"mypkg_egg_dir-1.0.0-py{sys.version_info.major}.{sys.version_info.minor}.egg"
)


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
    # The .egg directory acts as a standalone sys.path entry; the package
    # lives inside it.  The caller passes the .egg directory via
    # extra_sys_path.
    # ------------------------------------------------------------------
    # (no site-packages files needed; egg_dir is self-contained)

    return {
        "sp_dir": str(sp),
        "finder_src": str(finder_src),
        "egg_dir": str(_EGG_DIR),
    }
