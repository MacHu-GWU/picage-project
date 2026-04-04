# -*- coding: utf-8 -*-

"""
:class:`Module`, :class:`Package` data model.
"""

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
    ) -> None:
        assert_is_valid_name(name)
        self.name = name
        self.parent = parent
        self.is_single_file = is_single_file

        if path is None:
            self._locate_path()
        else:
            self.path = path

    # ------------------------------------------------------------------
    # sp_dir resolution strategies
    # Each method returns the source-tree root (the directory that, when
    # joined with the dot-separated name chain, yields the package dir),
    # or None when the strategy does not apply.
    # ------------------------------------------------------------------

    @staticmethod
    def _read_first_line(p: Path) -> str:
        """
        Read and return the first line of a file as a UTF-8 string.

        :param p: Path to the file to read.
        :returns: The first line, stripped of leading and trailing whitespace.
        """
        with open(p, "rb") as f:
            return f.readline().decode("utf-8").strip()

    def _resolve_via_egg_link(
        self,
        root: str,
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
        :returns: Absolute path of the source-tree root, or ``None`` if no
            matching ``.egg-link`` file is found.
        """
        for stem in (root.replace("_", "-"), root):
            p = Path(SP_DIR, stem + ".egg-link")
            if p.is_file():
                return self._read_first_line(p)
        return None

    def _resolve_via_simple_pth(
        self,
        root: str,
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
        :returns: Absolute path of the source-tree root, or ``None`` if no
            suitable ``.pth`` file is found.
        """
        for stem in (root.replace("_", "-"), root):
            p = Path(SP_DIR, stem + ".pth")
            if p.is_file():
                first_line = self._read_first_line(p)
                if not first_line.startswith("import ") and Path(first_line).is_dir():
                    return first_line
        return None

    @staticmethod
    def _resolve_via_importlib(
        root: str,
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

        :param root: Top-level import name of the package (e.g. ``"my_pkg"``).
        :returns: Absolute path of the source-tree root, or ``None`` if
            :func:`importlib.util.find_spec` cannot locate the package.
        """
        spec = importlib.util.find_spec(root)
        if spec is None:
            return None
        if spec.submodule_search_locations:
            return str(Path(spec.submodule_search_locations[0]).parent)
        if spec.origin:
            return str(Path(spec.origin).parent)
        return None

    def _find_sp_dir(
        self,
        root: str,
    ) -> str:
        """
        Return the source-tree root for *root* by trying each resolution
        strategy in priority order, falling back to ``SP_DIR``.

        Resolution order:

        1. :meth:`_resolve_via_egg_link` — legacy ``.egg-link`` editable installs.
        2. :meth:`_resolve_via_simple_pth` — PEP 660 Strategy A plain ``.pth`` files.
        3. :meth:`_resolve_via_importlib` — importlib-based universal fallback.
        4. ``SP_DIR`` — the active interpreter's ``site-packages`` directory.

        :param root: Top-level import name of the package (e.g. ``"my_pkg"``).
        :returns: Absolute path of the directory from which *root* can be
            reached by following the dot-separated name chain.
        """
        return (
            self._resolve_via_egg_link(root)
            or self._resolve_via_simple_pth(root)
            or self._resolve_via_importlib(root)
            or SP_DIR
        )

    def _locate_path(self) -> None:
        """
        Set :attr:`path` and :attr:`is_single_file` by navigating from the
        resolved source-tree root through the dot-separated name chain.

        :raises ValueError: If neither a single-file module nor a package
            directory with ``__init__.py`` can be found for this name.
        """
        chain = self.name.split(".")
        root = chain[0]
        sp_dir = self._find_sp_dir(root)

        # Single-file module (e.g. sphinx.builders.html -> .../builders/html.py)
        p = Path(sp_dir, *chain).with_suffix(".py")
        if p.is_file():
            self.path = p
            self.is_single_file = True
            return

        # Package directory (must contain __init__.py)
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
            return self.name.split(".")[-1]
        else:
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
    ) -> None:
        super(Package, self).__init__(
            name,
            path=path,
            parent=parent,
            is_single_file=is_single_file,
        )

        self.sub_packages: OrderedDict[str, "Package"] = OrderedDict()
        self.sub_modules: OrderedDict[str, Module] = OrderedDict()

        if self.is_single_file is False:
            for p in sorted(self.path.iterdir()):
                if p.is_dir():
                    if Path(p, "__init__.py").exists():
                        pkg = Package(
                            name=name + "." + p.name,
                            path=p,
                            parent=self,
                            is_single_file=False,
                        )
                        self.sub_packages[p.name] = pkg
                else:
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
            item: "Package" = self
            for _name in name.split("."):
                item = item[_name]  # type: ignore[assignment]
            return item
        try:
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
        yield (
            self,
            self.parent,
            list(self.sub_packages.values()),
            list(self.sub_modules.values()),
        )

        for pkg in self.sub_packages.values():
            yield from pkg.walk(pkg_only=pkg_only)

        if not pkg_only:
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

        for pkg in self.sub_packages.values():
            lines.append(pkg._tree_view_builder(indent=indent, is_root=False))

        lines.append(
            "%s%s (%s)" % (pad_text(indent), "__init__.py", self.fullname)
        )

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
