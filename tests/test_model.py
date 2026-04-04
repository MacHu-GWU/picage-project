# -*- coding: utf-8 -*-

"""
Tests for :mod:`picage.model` covering all supported installation formats.

Each test class targets one installation format and exercises the same set of
behaviours:

- :class:`TestFlatDistInfo`      — regular dist-info / wheel install
- :class:`TestEggLinkEditable`   — legacy ``.egg-link`` editable install
- :class:`TestPthEditable`       — PEP 660 Strategy A (``.pth`` path-insertion)
- :class:`TestImportlibFinder`   — PEP 660 Strategy B (custom importlib finder)
- :class:`TestEggDirectory`      — legacy egg-directory install

Standalone tests at module level cover error cases and cross-format concerns.
"""

import pytest
from pathlib import Path

from picage.model import Package, Module


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _all_names(pkg: Package, pkg_only: bool = False) -> set[str]:
    """Return the set of fully-qualified names from walk()."""
    return {item.name for item, *_ in pkg.walk(pkg_only=pkg_only)}


def _ascending(items: list) -> bool:
    return all(a.fullname < b.fullname for a, b in zip(items, items[1:]))


# ---------------------------------------------------------------------------
# Expected counts for the standard fake-package tree:
#
#   mypkg_XXX/                  ← root package
#       api.py
#       _internal.py
#       utils/                  ← sub-package
#           string_utils.py
#           number_utils.py
#           _helpers.py
#       commands/               ← sub-package
#           install.py
#           uninstall.py
#           _base.py
#           advanced/           ← deep sub-package
#               solver.py
#               _cache.py
#
#   Packages  : root, utils, commands, advanced   → 4
#   Modules   : api, _internal (root)             → 2
#               string_utils, number_utils, _helpers (utils) → 3
#               install, uninstall, _base (commands)         → 3
#               solver, _cache (advanced)                    → 2
#                                                  total      → 10
#   .py files : 4 __init__.py + 10 modules        → 14
# ---------------------------------------------------------------------------

EXPECTED_PKG_COUNT = 4
EXPECTED_MOD_COUNT = 10
EXPECTED_PY_FILES = 14   # == EXPECTED_PKG_COUNT + EXPECTED_MOD_COUNT


# ---------------------------------------------------------------------------
# Mixin: every format class inherits these tests
# The subclass only needs to set ``pkg_name`` and ``_make_pkg`` / ``_make_mod``.
# ---------------------------------------------------------------------------

class _FormatMixin:
    """
    Shared assertions run against every installation format.

    Subclasses must implement:
        ``pkg_name``   str  — e.g. "mypkg_flat"
        ``_pkg(info)`` → Package rooted at the fake install
        ``_mod(info, name)`` → Module (dot-qualified, e.g. "mypkg_flat.api")
    """

    pkg_name: str = ""

    # -- helpers the subclass must override ---------------------------------

    def _pkg(self, info: dict) -> Package:
        raise NotImplementedError

    def _sub_pkg(self, info: dict, rel: str) -> Package:
        """Return a sub-package by dot-relative name, e.g. 'commands.advanced'."""
        raise NotImplementedError

    def _mod(self, info: dict, rel: str) -> Module:
        """Return a module by dot-relative name, e.g. 'api'."""
        raise NotImplementedError

    # -- name / identity tests -----------------------------------------------

    def test_root_name(self, fake_sp):
        pkg = self._pkg(fake_sp)
        assert pkg.name == self.pkg_name
        assert pkg.fullname == self.pkg_name
        assert pkg.shortname == self.pkg_name

    def test_root_is_package(self, fake_sp):
        pkg = self._pkg(fake_sp)
        assert pkg.is_single_file is False
        assert pkg.path.is_dir()
        assert (pkg.path / "__init__.py").exists()

    def test_root_parent_is_none(self, fake_sp):
        pkg = self._pkg(fake_sp)
        assert pkg.parent is None

    # -- sub-package structure -----------------------------------------------

    def test_direct_sub_packages(self, fake_sp):
        pkg = self._pkg(fake_sp)
        assert set(pkg.sub_packages.keys()) == {"utils", "commands"}

    def test_deep_sub_package_exists(self, fake_sp):
        pkg = self._pkg(fake_sp)
        advanced = pkg["commands"]["advanced"]
        assert advanced.name == f"{self.pkg_name}.commands.advanced"
        assert advanced.shortname == "advanced"
        assert advanced.fullname == f"{self.pkg_name}.commands.advanced"

    def test_sub_package_parent_chain(self, fake_sp):
        pkg = self._pkg(fake_sp)
        commands = pkg["commands"]
        advanced = commands["advanced"]
        assert advanced.parent is commands
        assert commands.parent is pkg
        assert pkg.parent is None

    def test_sub_package_from_name(self, fake_sp):
        """Package constructed directly from a dotted name resolves correctly."""
        sub = self._sub_pkg(fake_sp, "commands")
        assert sub.name == f"{self.pkg_name}.commands"
        assert sub.shortname == "commands"
        assert sub.is_single_file is False

    def test_deep_sub_package_from_name(self, fake_sp):
        sub = self._sub_pkg(fake_sp, "commands.advanced")
        assert sub.name == f"{self.pkg_name}.commands.advanced"
        assert sub.shortname == "advanced"

    # -- module structure ----------------------------------------------------

    def test_root_modules(self, fake_sp):
        pkg = self._pkg(fake_sp)
        assert set(pkg.sub_modules.keys()) == {"api", "_internal"}

    def test_utils_modules(self, fake_sp):
        pkg = self._pkg(fake_sp)
        assert set(pkg["utils"].sub_modules.keys()) == {
            "string_utils", "number_utils", "_helpers"
        }

    def test_commands_modules(self, fake_sp):
        pkg = self._pkg(fake_sp)
        assert set(pkg["commands"].sub_modules.keys()) == {
            "install", "uninstall", "_base"
        }

    def test_advanced_modules(self, fake_sp):
        pkg = self._pkg(fake_sp)
        assert set(pkg["commands"]["advanced"].sub_modules.keys()) == {
            "solver", "_cache"
        }

    def test_module_from_name(self, fake_sp):
        mod = self._mod(fake_sp, "api")
        assert mod.name == f"{self.pkg_name}.api"
        assert mod.shortname == "api"
        assert mod.fullname == f"{self.pkg_name}.api"
        assert mod.is_single_file is True
        assert mod.path.is_file()
        assert mod.path.suffix == ".py"

    def test_private_module_included(self, fake_sp):
        """Modules whose names start with _ must be included."""
        pkg = self._pkg(fake_sp)
        assert "_internal" in pkg.sub_modules
        assert "_helpers" in pkg["utils"].sub_modules
        assert "_base" in pkg["commands"].sub_modules
        assert "_cache" in pkg["commands"]["advanced"].sub_modules

    # -- __getitem__ ---------------------------------------------------------

    def test_getitem_direct_package(self, fake_sp):
        pkg = self._pkg(fake_sp)
        utils = pkg["utils"]
        assert isinstance(utils, Package)
        assert utils.name == f"{self.pkg_name}.utils"

    def test_getitem_direct_module(self, fake_sp):
        pkg = self._pkg(fake_sp)
        api = pkg["api"]
        assert isinstance(api, Module)
        assert api.name == f"{self.pkg_name}.api"

    def test_getitem_dot_notation_package(self, fake_sp):
        pkg = self._pkg(fake_sp)
        assert pkg["commands.advanced"] == pkg["commands"]["advanced"]

    def test_getitem_dot_notation_module(self, fake_sp):
        pkg = self._pkg(fake_sp)
        assert pkg["commands.install"] == pkg["commands"]["install"]

    def test_getitem_deep_dot_notation(self, fake_sp):
        pkg = self._pkg(fake_sp)
        assert pkg["commands.advanced.solver"] == (
            pkg["commands"]["advanced"]["solver"]
        )

    def test_getitem_missing_raises(self, fake_sp):
        pkg = self._pkg(fake_sp)
        with pytest.raises(KeyError):
            pkg["does_not_exist"]

    # -- walk ----------------------------------------------------------------

    def test_walk_pkg_only_count(self, fake_sp):
        pkg = self._pkg(fake_sp)
        items = list(pkg.walk(pkg_only=True))
        assert len(items) == EXPECTED_PKG_COUNT

    def test_walk_all_count(self, fake_sp):
        pkg = self._pkg(fake_sp)
        items = list(pkg.walk(pkg_only=False))
        assert len(items) == EXPECTED_PY_FILES

    def test_walk_pkg_only_names(self, fake_sp):
        pkg = self._pkg(fake_sp)
        names = {item.name for item, *_ in pkg.walk(pkg_only=True)}
        assert names == {
            self.pkg_name,
            f"{self.pkg_name}.utils",
            f"{self.pkg_name}.commands",
            f"{self.pkg_name}.commands.advanced",
        }

    def test_walk_all_names(self, fake_sp):
        pkg = self._pkg(fake_sp)
        names = _all_names(pkg, pkg_only=False)
        assert names == {
            self.pkg_name,
            f"{self.pkg_name}.api",
            f"{self.pkg_name}._internal",
            f"{self.pkg_name}.utils",
            f"{self.pkg_name}.utils.string_utils",
            f"{self.pkg_name}.utils.number_utils",
            f"{self.pkg_name}.utils._helpers",
            f"{self.pkg_name}.commands",
            f"{self.pkg_name}.commands.install",
            f"{self.pkg_name}.commands.uninstall",
            f"{self.pkg_name}.commands._base",
            f"{self.pkg_name}.commands.advanced",
            f"{self.pkg_name}.commands.advanced.solver",
            f"{self.pkg_name}.commands.advanced._cache",
        }

    def test_walk_sub_packages_ascending(self, fake_sp):
        """sub_packages yielded by walk() are in ascending fullname order."""
        pkg = self._pkg(fake_sp)
        for _, _, sub_pkgs, _ in pkg.walk(pkg_only=True):
            assert _ascending(sub_pkgs), sub_pkgs

    def test_walk_sub_modules_ascending(self, fake_sp):
        """sub_modules yielded by walk() are in ascending fullname order."""
        pkg = self._pkg(fake_sp)
        for _, _, _, sub_mods in pkg.walk(pkg_only=True):
            assert _ascending(sub_mods), sub_mods

    def test_walk_py_file_count_matches(self, fake_sp):
        """walk(pkg_only=False) item count equals the number of .py files on disk."""
        pkg = self._pkg(fake_sp)
        py_files = list(Path(pkg.path).rglob("*.py"))
        walk_items = list(pkg.walk(pkg_only=False))
        assert len(py_files) == len(walk_items)

    # -- equality ------------------------------------------------------------

    def test_equality_same_path(self, fake_sp):
        pkg1 = self._pkg(fake_sp)
        pkg2 = self._pkg(fake_sp)
        assert pkg1 == pkg2

    def test_equality_different_objects_same_path(self, fake_sp):
        sub1 = self._sub_pkg(fake_sp, "utils")
        sub2 = self._pkg(fake_sp)["utils"]
        assert sub1 == sub2

    def test_inequality_different_packages(self, fake_sp):
        pkg = self._pkg(fake_sp)
        assert pkg != pkg["utils"]

    def test_equality_module(self, fake_sp):
        mod1 = self._mod(fake_sp, "api")
        mod2 = self._pkg(fake_sp)["api"]
        assert mod1 == mod2

    # -- display (smoke test) ------------------------------------------------

    def test_str(self, fake_sp):
        s = str(self._pkg(fake_sp))
        assert self.pkg_name in s
        assert "sub_packages" in s
        assert "sub_modules" in s

    def test_repr_package(self, fake_sp):
        pkg = self._pkg(fake_sp)
        r = repr(pkg)
        assert r.startswith("Package(")
        assert self.pkg_name in r

    def test_repr_module(self, fake_sp):
        mod = self._mod(fake_sp, "api")
        r = repr(mod)
        assert r.startswith("Module(")
        assert "api" in r

    def test_pprint_runs(self, fake_sp, capsys):
        self._pkg(fake_sp).pprint()
        out = capsys.readouterr().out
        assert self.pkg_name in out


# ---------------------------------------------------------------------------
# Concrete test classes — one per installation format
# ---------------------------------------------------------------------------

class TestFlatDistInfo(_FormatMixin):
    """
    Flat dist-info / wheel install: the package directory is copied directly
    into site-packages alongside a ``<name>-<ver>.dist-info/`` directory.
    Resolution falls through egg-link → pth → importlib, hits the final
    ``sp_dir`` fallback, and finds the package there.
    """

    pkg_name = "mypkg_flat"

    def _pkg(self, info: dict) -> Package:
        return Package(self.pkg_name, sp_dir=info["sp_dir"])

    def _sub_pkg(self, info: dict, rel: str) -> Package:
        return Package(f"{self.pkg_name}.{rel}", sp_dir=info["sp_dir"])

    def _mod(self, info: dict, rel: str) -> Module:
        return Module(f"{self.pkg_name}.{rel}", sp_dir=info["sp_dir"])


class TestEggLinkEditable(_FormatMixin):
    """
    Legacy egg-link editable install: a ``<name>.egg-link`` file in
    site-packages whose first line is the path to the source tree.
    Resolution succeeds via :meth:`_resolve_via_egg_link`.
    """

    pkg_name = "mypkg_egg_link"

    def _pkg(self, info: dict) -> Package:
        return Package(self.pkg_name, sp_dir=info["sp_dir"])

    def _sub_pkg(self, info: dict, rel: str) -> Package:
        return Package(f"{self.pkg_name}.{rel}", sp_dir=info["sp_dir"])

    def _mod(self, info: dict, rel: str) -> Module:
        return Module(f"{self.pkg_name}.{rel}", sp_dir=info["sp_dir"])

    def test_egg_link_file_is_used(self, fake_sp):
        """Verify the resolved path actually lives in the egg_link source tree."""
        pkg = self._pkg(fake_sp)
        assert "egg_link_src" in str(pkg.path)


class TestPthEditable(_FormatMixin):
    """
    PEP 660 Strategy A: a plain ``<name>.pth`` file whose first line is an
    absolute directory path.  Resolution succeeds via
    :meth:`_resolve_via_simple_pth`.
    """

    pkg_name = "mypkg_pth"

    def _pkg(self, info: dict) -> Package:
        return Package(self.pkg_name, sp_dir=info["sp_dir"])

    def _sub_pkg(self, info: dict, rel: str) -> Package:
        return Package(f"{self.pkg_name}.{rel}", sp_dir=info["sp_dir"])

    def _mod(self, info: dict, rel: str) -> Module:
        return Module(f"{self.pkg_name}.{rel}", sp_dir=info["sp_dir"])

    def test_pth_file_is_used(self, fake_sp):
        """Verify the resolved path actually lives in the pth source tree."""
        pkg = self._pkg(fake_sp)
        assert "pth_src" in str(pkg.path)


class TestImportlibFinder(_FormatMixin):
    """
    PEP 660 Strategy B: no ``.egg-link`` or plain ``.pth`` file in
    site-packages.  The caller provides ``extra_sys_path`` pointing to the
    source tree, which :meth:`_resolve_via_importlib` temporarily prepends to
    ``sys.path`` so that ``importlib.util.find_spec`` can find the package.
    This mirrors the runtime effect of the ``__editable__.<pkg>-<ver>.pth``
    / custom-finder mechanism used by uv and setuptools.
    """

    pkg_name = "mypkg_finder"

    def _pkg(self, info: dict) -> Package:
        return Package(
            self.pkg_name,
            sp_dir=info["sp_dir"],
            extra_sys_path=[info["finder_src"]],
        )

    def _sub_pkg(self, info: dict, rel: str) -> Package:
        return Package(
            f"{self.pkg_name}.{rel}",
            sp_dir=info["sp_dir"],
            extra_sys_path=[info["finder_src"]],
        )

    def _mod(self, info: dict, rel: str) -> Module:
        return Module(
            f"{self.pkg_name}.{rel}",
            sp_dir=info["sp_dir"],
            extra_sys_path=[info["finder_src"]],
        )

    def test_finder_src_is_used(self, fake_sp):
        """Verify the resolved path actually lives in finder_src."""
        pkg = self._pkg(fake_sp)
        assert "finder_src" in str(pkg.path)

    def test_sys_path_not_polluted(self, fake_sp):
        """extra_sys_path must not leak into sys.path after resolution."""
        import sys
        before = sys.path[:]
        self._pkg(fake_sp)
        assert sys.path == before


class TestEggDirectory(_FormatMixin):
    """
    Legacy egg-directory install: a ``<name>-<ver>.egg/`` directory acts as a
    self-contained sys.path entry; the package lives inside it.  The caller
    provides ``extra_sys_path=[egg_dir]`` so that importlib can locate the
    package.
    """

    pkg_name = "mypkg_egg_dir"

    def _pkg(self, info: dict) -> Package:
        return Package(
            self.pkg_name,
            sp_dir=info["sp_dir"],
            extra_sys_path=[info["egg_dir"]],
        )

    def _sub_pkg(self, info: dict, rel: str) -> Package:
        return Package(
            f"{self.pkg_name}.{rel}",
            sp_dir=info["sp_dir"],
            extra_sys_path=[info["egg_dir"]],
        )

    def _mod(self, info: dict, rel: str) -> Module:
        return Module(
            f"{self.pkg_name}.{rel}",
            sp_dir=info["sp_dir"],
            extra_sys_path=[info["egg_dir"]],
        )

    def test_package_is_inside_egg(self, fake_sp):
        """Verify the resolved path lives inside the .egg directory."""
        pkg = self._pkg(fake_sp)
        assert ".egg" in str(pkg.path)

    def test_sys_path_not_polluted(self, fake_sp):
        import sys
        before = sys.path[:]
        self._pkg(fake_sp)
        assert sys.path == before


# ---------------------------------------------------------------------------
# Standalone / cross-format tests
# ---------------------------------------------------------------------------

def test_package_not_found(fake_sp):
    """Requesting a non-existent package raises ValueError."""
    with pytest.raises(ValueError, match="Can't found"):
        Package("package_that_does_not_exist", sp_dir=fake_sp["sp_dir"])


def test_module_not_found(fake_sp):
    """Requesting a non-existent module raises ValueError."""
    with pytest.raises(ValueError, match="Can't found"):
        Module("module_that_does_not_exist", sp_dir=fake_sp["sp_dir"])


def test_invalid_name_raises():
    """A name with an uppercase first letter must be rejected immediately."""
    with pytest.raises(ValueError):
        Package("NotValid")


def test_getitem_missing_key_message(fake_sp):
    """KeyError message includes both the package name and the missing key."""
    pkg = Package("mypkg_flat", sp_dir=fake_sp["sp_dir"])
    with pytest.raises(KeyError, match="mypkg_flat"):
        pkg["no_such_child"]


def test_equality_cross_type(fake_sp):
    """A Package and a Module are never equal even if they share a path."""
    pkg = Package("mypkg_flat", sp_dir=fake_sp["sp_dir"])
    assert pkg.__eq__("not a package") is NotImplemented


def test_walk_tuple_structure(fake_sp):
    """Each walk() tuple must have exactly four elements."""
    pkg = Package("mypkg_flat", sp_dir=fake_sp["sp_dir"])
    for item in pkg.walk(pkg_only=False):
        assert len(item) == 4


def test_walk_leaf_module_empty_children(fake_sp):
    """Modules yielded by walk(pkg_only=False) must have empty child lists."""
    pkg = Package("mypkg_flat", sp_dir=fake_sp["sp_dir"])
    for node, parent, sub_pkgs, sub_mods in pkg.walk(pkg_only=False):
        if isinstance(node, Module):
            assert sub_pkgs == []
            assert sub_mods == []


def test_sub_package_equality_across_formats(fake_sp):
    """Two packages at the same filesystem path compare equal regardless of
    how they were resolved."""
    pkg_flat = Package("mypkg_flat", sp_dir=fake_sp["sp_dir"])
    utils_via_root = pkg_flat["utils"]
    utils_direct = Package("mypkg_flat.utils", sp_dir=fake_sp["sp_dir"])
    assert utils_via_root == utils_direct


if __name__ == "__main__":
    import os
    import pytest as _pytest
    _pytest.main([os.path.basename(__file__), "-s", "--tb=native"])
