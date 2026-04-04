# -*- coding: utf-8 -*-

"""
:class:`Module`, :class:`Package` data model.
"""

import sys
import importlib.util
from pathlib import Path
from collections import OrderedDict
from .helpers import SP_DIR, assert_is_valid_name

Tab = " " * 4


class BaseModuleOrPackage:
    """
    Base class representing either a Python module or a package.
    """

    def __init__(
        self,
        name: str,
        path: Path | None = None,
        parent: "BaseModuleOrPackage | None" = None,
        is_single_file: bool | None = None,
        sp_dir: str = SP_DIR,
        extra_sys_path: list[str] | None = None,
    ) -> None:
        assert_is_valid_name(name)
        self.name = name
        self.parent = parent
        self.is_single_file = is_single_file

        if path is None:
            # No explicit path provided: resolve it from the installed package.
            self._locate_path(sp_dir=sp_dir, extra_sys_path=extra_sys_path)
        else:
            # Caller supplied an explicit path (e.g. when building the tree
            # recursively for sub-packages that are already known).
            self.path = path

    # ------------------------------------------------------------------
    # sp_dir resolution strategies
    # Each method returns the source-tree root (the directory that, when
    # joined with the dot-separated name chain, yields the package dir),
    # or None when the strategy does not apply.
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_via_egg_link(
        root: str,
        sp_dir: str = SP_DIR,
    ) -> str | None:
        """
        Resolve the source-tree root from a legacy ``.egg-link`` file.

        This covers editable installs created by ``python setup.py develop``
        or ``pip install -e .`` with old setuptools (pre-PEP 660).

        Layout in site-packages::

            <root>.egg-link          # first line = path to source tree
            easy-install.pth         # adds that path to sys.path

        The ``.egg-link`` filename uses the distribution name, which may
        substitute hyphens for underscores, so both variants are tried.

        :param root: Top-level import name of the package (e.g. ``"my_pkg"``).
        :param sp_dir: Site-packages directory to search for the ``.egg-link``
            file.  Defaults to the active interpreter's ``site-packages``.
        :returns: Absolute path of the source-tree root, or ``None`` if no
            matching ``.egg-link`` file is found.
        """
        # Distribution names may use hyphens where import names use underscores
        # (e.g. "my-pkg" on disk vs "my_pkg" in import statements), so try
        # the hyphenated variant first, then the original.
        for stem in (root.replace("_", "-"), root):
            p = Path(sp_dir, stem + ".egg-link")
            if p.is_file():
                # The .egg-link format is a text file whose first line is the
                # absolute path to the project source directory, followed by
                # an optional second line containing ".".
                with open(p, "rb") as f:
                    return f.readline().decode("utf-8").strip()
        return None

    @staticmethod
    def _resolve_via_simple_pth(
        root: str,
        sp_dir: str = SP_DIR,
    ) -> str | None:
        """
        Resolve the source-tree root from a plain path-insertion ``.pth`` file.

        This covers PEP 660 editable installs using Strategy A, where build
        backends such as hatchling or flit write a ``<name>.pth`` file whose
        first line is an absolute directory path added to ``sys.path`` at
        interpreter startup::

            site-packages/
                <root>.pth           # first line = /path/to/source/src

        Import-style ``.pth`` files — whose first line begins with
        ``import`` — are explicitly rejected to avoid matching the
        ``__editable__.<pkg>-<ver>.pth`` files written by setuptools/uv
        (PEP 660 Strategy B), which are handled by
        :meth:`_resolve_via_importlib`.

        :param root: Top-level import name of the package (e.g. ``"my_pkg"``).
        :param sp_dir: Site-packages directory to search for the ``.pth`` file.
            Defaults to the active interpreter's ``site-packages``.
        :returns: Absolute path of the source-tree root, or ``None`` if no
            suitable ``.pth`` file is found.
        """
        # Same hyphen/underscore duality as in _resolve_via_egg_link.
        for stem in (root.replace("_", "-"), root):
            p = Path(sp_dir, stem + ".pth")
            if p.is_file():
                with open(p, "rb") as f:
                    first_line = f.readline().decode("utf-8").strip()
                # Reject import-style lines such as:
                #   "import __editable___mypkg_1_0_finder; ..."
                # Those are PEP 660 Strategy B files; we must not misread them
                # as a plain directory path.  Only accept lines that are an
                # existing directory on disk.
                if not first_line.startswith("import ") and Path(first_line).is_dir():
                    return first_line
        return None

    @staticmethod
    def _resolve_via_importlib(
        root: str,
        extra_sys_path: list[str] | None = None,
    ) -> str | None:
        """
        Resolve the source-tree root via :func:`importlib.util.find_spec`.

        This is a universal fallback that covers every installation format
        that registers itself with Python's import machinery before this
        code runs, including:

        * **PEP 660 Strategy B** — setuptools/uv editable installs that drop
          an ``__editable__.<pkg>-<ver>.pth`` file registering a custom
          :class:`importlib.abc.MetaPathFinder` with a ``MAPPING`` dict
          pointing to the source tree.
        * **Egg directory installs** — ``easy-install.pth`` adds the ``.egg/``
          directory to ``sys.path``, so importlib finds the package inside it.
        * **Flat dist-info / egg-info installs** — regular pip/uv installs and
          wheel installs where the package lives directly in ``site-packages/``.
        * **Direct-URL non-editable installs** (PEP 610) — result is identical
          to a regular dist-info install.

        When *extra_sys_path* is provided those directories are temporarily
        prepended to :data:`sys.path` for the duration of the
        :func:`~importlib.util.find_spec` call, then restored.  This is the
        dependency-injection interface for testing: callers supply real source
        directories rather than relying on global interpreter state.

        :param root: Top-level import name of the package (e.g. ``"my_pkg"``).
        :param extra_sys_path: Additional directories to prepend to
            :data:`sys.path` before calling :func:`~importlib.util.find_spec`.
            ``None`` (default) leaves :data:`sys.path` untouched.
        :returns: Absolute path of the source-tree root, or ``None`` if
            :func:`importlib.util.find_spec` cannot locate the package.
        """
        if extra_sys_path:
            # Temporarily extend sys.path so find_spec can see the injected
            # directories.  The original list is restored in the finally block
            # regardless of whether find_spec raises.
            saved = sys.path[:]
            sys.path = list(extra_sys_path) + sys.path
            try:
                spec = importlib.util.find_spec(root)
            finally:
                sys.path = saved
        else:
            spec = importlib.util.find_spec(root)

        if spec is None:
            # importlib has no knowledge of this package at all.
            return None

        if spec.submodule_search_locations:
            # spec.submodule_search_locations is a list of directories on the
            # file system that Python will search for sub-modules / sub-packages
            # of this package.  For a regular package the list contains exactly
            # one entry: the package directory itself (e.g. ".../site-packages/
            # sphinx/").  Taking its parent gives us the sp_dir equivalent
            # (e.g. ".../site-packages/"), from which the full name chain can be
            # reconstructed by _locate_path.
            return str(Path(spec.submodule_search_locations[0]).parent)

        # spec.origin is the path to the file that implements the module.  For
        # a normal package this would be its __init__.py, but packages always
        # have submodule_search_locations set, so we only reach here for
        # single-file modules (e.g. a legacy "six.py" top-level module that
        # lives directly in site-packages).  Taking the parent of origin gives
        # the directory that contains the .py file, which serves as sp_dir for
        # _locate_path.
        if spec.origin:
            return str(Path(spec.origin).parent)

        # spec exists but carries neither search locations nor an origin path.
        # This is not expected for any real installed package; return None so
        # _find_sp_dir falls through to the sp_dir default.
        return None

    def _find_sp_dir(
        self,
        root: str,
        sp_dir: str = SP_DIR,
        extra_sys_path: list[str] | None = None,
    ) -> str:
        """
        Return the source-tree root for *root* by trying each resolution
        strategy in priority order, falling back to *sp_dir*.

        Resolution order:

        1. :meth:`_resolve_via_egg_link` — legacy ``.egg-link`` editable installs.
        2. :meth:`_resolve_via_simple_pth` — PEP 660 Strategy A plain ``.pth`` files.
        3. :meth:`_resolve_via_importlib` — importlib-based universal fallback.
        4. *sp_dir* — falls back to the provided site-packages directory.

        :param root: Top-level import name of the package (e.g. ``"my_pkg"``).
        :param sp_dir: Site-packages directory passed to file-based strategies
            and used as the final fallback.
        :param extra_sys_path: Forwarded to :meth:`_resolve_via_importlib`.
        :returns: Absolute path of the directory from which *root* can be
            reached by following the dot-separated name chain.
        """
        return (
            self._resolve_via_egg_link(root, sp_dir=sp_dir)
            or self._resolve_via_simple_pth(root, sp_dir=sp_dir)
            or self._resolve_via_importlib(root, extra_sys_path=extra_sys_path)
            or sp_dir  # last resort: the package lives directly in sp_dir
        )

    def _locate_path(
        self,
        sp_dir: str = SP_DIR,
        extra_sys_path: list[str] | None = None,
    ) -> None:
        """
        Set :attr:`path` and :attr:`is_single_file` by navigating from the
        resolved source-tree root through the dot-separated name chain.

        :param sp_dir: Forwarded to :meth:`_find_sp_dir`.
        :param extra_sys_path: Forwarded to :meth:`_find_sp_dir`.
        :raises ValueError: If neither a single-file module nor a package
            directory with ``__init__.py`` can be found for this name.
        """
        # "a.b.c" → ["a", "b", "c"]; root is always chain[0].
        chain = self.name.split(".")
        root = chain[0]
        sp_dir = self._find_sp_dir(root, sp_dir=sp_dir, extra_sys_path=extra_sys_path)

        # Try single-file module first: e.g. "sphinx.builders.html" maps to
        # <sp_dir>/sphinx/builders/html.py.
        p = Path(sp_dir, *chain).with_suffix(".py")
        if p.is_file():
            self.path = p
            self.is_single_file = True
            return

        # Otherwise expect a package directory that contains an __init__.py.
        # The presence of __init__.py distinguishes a real package from an
        # arbitrary directory that happens to share the package name.
        p = Path(sp_dir, *chain)
        if p.is_dir() and Path(p, "__init__.py").exists():
            self.path = p
            self.is_single_file = False
            return

        raise ValueError("Can't found '%s'!" % self.name)

    @property
    def fullname(self) -> str:
        """
        Fully qualified import name.

        Example: for ``sphinx.builders.html`` the fullname is
        ``"sphinx.builders.html"``.
        """
        return self.name

    @property
    def shortname(self) -> str:
        """
        Unqualified (leaf) import name.

        Example: for ``sphinx.builders.html`` the shortname is ``"html"``.
        """
        if "." in self.name:
            # "a.b.c" → "c"
            return self.name.split(".")[-1]
        else:
            # Top-level name with no dots: shortname == fullname.
            return self.name

    def __eq__(
        self,
        other: object,
    ) -> bool:
        if not isinstance(other, BaseModuleOrPackage):
            return NotImplemented
        return self.path == other.path


class Module(BaseModuleOrPackage):
    """
    Represent a Python module — typically a single ``*.py`` file.

    :param name: Fully qualified module name, e.g. ``"sphinx.builders.html"``.
    :param path: Absolute path to the module file.  When omitted the path is
        resolved automatically from the installed package.
    :param parent: Parent :class:`Package`, or ``None`` for top-level modules.
    :param is_single_file: ``True`` if this is a single-file module.
    :param sp_dir: Site-packages directory used for path resolution when
        *path* is omitted.  Defaults to the active interpreter's
        ``site-packages``.
    :param extra_sys_path: Additional directories prepended to
        :data:`sys.path` during importlib-based resolution.  ``None`` by
        default.
    """

    def __repr__(self) -> str:
        return "Module(name=%r, path='%s')" % (self.name, self.path)


class Package(BaseModuleOrPackage):
    """
    Represent a Python package — a directory containing an ``__init__.py`` file.

    On construction the package tree is walked eagerly: every sub-directory
    that contains an ``__init__.py`` becomes a child :class:`Package`, and
    every other ``*.py`` file (except ``__init__.py``) becomes a child
    :class:`Module`.

    :param name: Dot-separated fully qualified name, e.g. ``"sphinx.builders"``.
    :param path: Absolute path to the package directory.  When omitted the path
        is resolved automatically from the installed package.
    :param parent: Parent :class:`Package`, or ``None`` for top-level packages.
    :param is_single_file: Must be ``False`` for packages; exposed for
        interface consistency with :class:`BaseModuleOrPackage`.
    :param sp_dir: Site-packages directory used for path resolution when
        *path* is omitted.  Defaults to the active interpreter's
        ``site-packages``.
    :param extra_sys_path: Additional directories prepended to
        :data:`sys.path` during importlib-based resolution.  ``None`` by
        default.

    Attributes:

    - ``name``: Fully qualified package name.
    - ``path``: Absolute path to the package directory.
    - ``fullname``: Same as ``name``.
    - ``shortname``: Leaf component of ``name`` (part after the last dot).
    - ``parent``: Parent :class:`Package` instance, or ``None``.
    - ``is_single_file``: Always ``False`` for directory-based packages.
    - ``sub_packages``: :class:`~collections.OrderedDict` mapping child package
      names to :class:`Package` instances.
    - ``sub_modules``: :class:`~collections.OrderedDict` mapping child module
      names to :class:`Module` instances.
    """

    def __init__(
        self,
        name: str,
        path: Path | None = None,
        parent: "Package | None" = None,
        is_single_file: bool | None = None,
        sp_dir: str = SP_DIR,
        extra_sys_path: list[str] | None = None,
    ) -> None:
        super(Package, self).__init__(
            name,
            path=path,
            parent=parent,
            is_single_file=is_single_file,
            sp_dir=sp_dir,
            extra_sys_path=extra_sys_path,
        )

        self.sub_packages: OrderedDict[str, "Package"] = OrderedDict()
        self.sub_modules: OrderedDict[str, Module] = OrderedDict()

        # Only walk the directory tree when this is a proper package directory
        # (is_single_file=False).  is_single_file=True means the "package" is
        # a single .py file (e.g. a legacy six.py), which has no children.
        if self.is_single_file is False:
            for p in sorted(self.path.iterdir()):
                if p.is_dir():
                    # A sub-directory is a sub-package only if it contains an
                    # __init__.py; bare directories (data dirs, __pycache__,
                    # etc.) are skipped.
                    if Path(p, "__init__.py").exists():
                        pkg = Package(
                            name=name + "." + p.name,
                            path=p,
                            parent=self,
                            is_single_file=False,
                        )
                        self.sub_packages[p.name] = pkg
                else:
                    # A .py file is a sub-module unless it is __init__.py,
                    # which represents the package itself rather than a module.
                    if p.suffix == ".py" and p.stem != "__init__":
                        module = Module(
                            name=name + "." + p.stem,
                            path=p,
                            parent=self,
                            is_single_file=True,
                        )
                        self.sub_modules[p.stem] = module

    def __str__(self) -> str:
        tpl = (
            "Package("
            "\n{tab}name=%r,"
            "\n{tab}path='%s',"
            "\n{tab}sub_packages=%r,"
            "\n{tab}sub_modules=%r,"
            "\n)"
        ).format(tab=Tab)
        return tpl % (
            self.name,
            self.path,
            list(self.sub_packages),
            list(self.sub_modules),
        )

    def __repr__(self) -> str:
        return "Package(name=%r, path='%s')" % (self.name, self.path)

    def __getitem__(
        self,
        name: str,
    ) -> "Package | Module":
        """
        Retrieve a direct child package or module by name, supporting
        dot-separated paths for deeper traversal.

        :param name: Child name (e.g. ``"builders"``) or dot-separated path
            (e.g. ``"builders.html"``).
        :returns: The matching :class:`Package` or :class:`Module`.
        :raises KeyError: If no child with the given name exists.
        """
        if "." in name:
            # Dot notation: traverse one component at a time.
            # e.g. "commands.advanced.solver" → pkg["commands"]["advanced"]["solver"]
            item: "Package" = self
            for _name in name.split("."):
                item = item[_name]  # type: ignore[assignment]
            return item
        try:
            # Check sub-packages first; a package and a module cannot share the
            # same stem inside a single directory, so the order does not matter
            # in practice, but packages are conventionally more prominent.
            return self.sub_packages[name]
        except KeyError:
            try:
                return self.sub_modules[name]
            except KeyError:
                raise KeyError("%r doesn't has sub module %r!" % (self.name, name))

    def walk(
        self,
        pkg_only: bool = True,
    ):
        """
        Recursively yield the package tree.

        Each iteration yields a 4-tuple:

        1. *current* — the current :class:`Package` (or :class:`Module` when
           ``pkg_only=False``).
        2. *parent* — the parent :class:`Package`, or ``None`` for the root.
        3. *sub_packages* — list of direct child :class:`Package` instances.
        4. *sub_modules* — list of direct child :class:`Module` instances.

        :param pkg_only: When ``True`` (default) only packages are yielded.
            When ``False`` leaf modules are also yielded as 4-tuples whose
            *sub_packages* and *sub_modules* lists are empty.
        """
        # Yield this package node first (pre-order traversal).
        yield (
            self,
            self.parent,
            list(self.sub_packages.values()),
            list(self.sub_modules.values()),
        )

        # Recurse into sub-packages.
        for pkg in self.sub_packages.values():
            yield from pkg.walk(pkg_only=pkg_only)

        if not pkg_only:
            # When the caller wants all nodes, emit leaf modules as 4-tuples
            # with empty child lists (modules have no children of their own).
            for sub_module in self.sub_modules.values():
                yield sub_module, self, [], []

    def _tree_view_builder(
        self,
        indent: int = 0,
        is_root: bool = True,
    ) -> str:
        """
        Build and return a text representation of the package tree.

        :param indent: Current indentation level (increases with each level).
        :param is_root: When ``True`` the ``SP_DIR`` header line is prepended.
        :returns: Multi-line string representing the subtree rooted at this
            package.
        """

        def pad_text(level: int) -> str:
            return "    " * level + "|-- "

        lines: list[str] = []

        if is_root:
            lines.append(SP_DIR)

        lines.append("%s%s (%s)" % (pad_text(indent), self.shortname, self.fullname))
        indent += 1

        # Sub-packages come before __init__.py and modules in the display.
        for pkg in self.sub_packages.values():
            lines.append(pkg._tree_view_builder(indent=indent, is_root=False))

        # __init__.py is shown as belonging to this package's namespace.
        lines.append(
            "%s%s (%s)" % (pad_text(indent), "__init__.py", self.fullname)
        )

        # Leaf modules follow __init__.py.
        for mod in self.sub_modules.values():
            lines.append(
                "%s%s (%s)" % (pad_text(indent), mod.shortname + ".py", mod.fullname)
            )

        return "\n".join(lines)

    def pprint(self) -> None:
        """
        Print the package tree to stdout.
        """
        print(self._tree_view_builder(indent=0, is_root=True))
