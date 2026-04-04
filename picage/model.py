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
    Base Class to represent a module or package.
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
        with open(p, "rb") as f:
            return f.readline().decode("utf-8").strip()

    def _resolve_via_egg_link(self, root: str) -> str | None:
        """
        Legacy editable install created by ``python setup.py develop`` or
        ``pip install -e .`` with old setuptools (pre-PEP 660).

        Layout in site-packages::

            <root>.egg-link          # first line = path to source tree
            easy-install.pth         # adds that path to sys.path

        The ``.egg-link`` filename uses the distribution name, which may
        use hyphens where the import name uses underscores, so both
        variants are tried.
        """
        for stem in (root.replace("_", "-"), root):
            p = Path(SP_DIR, stem + ".egg-link")
            if p.is_file():
                return self._read_first_line(p)
        return None

    def _resolve_via_simple_pth(self, root: str) -> str | None:
        """
        PEP 660 editable install — Strategy A (path-insertion ``.pth``).

        Some build backends (e.g. hatchling, flit) write a plain
        ``<name>.pth`` file whose first line is an absolute directory
        path that is added to ``sys.path`` at interpreter startup::

            site-packages/
                <root>.pth           # first line = /path/to/source/src

        This is distinct from import-style ``.pth`` files (whose first
        line starts with ``import``) such as the
        ``__editable__.<pkg>-<ver>.pth`` files written by setuptools /
        uv (PEP 660 Strategy B), which are handled separately.
        """
        for stem in (root.replace("_", "-"), root):
            p = Path(SP_DIR, stem + ".pth")
            if p.is_file():
                first_line = self._read_first_line(p)
                # Reject import-style lines; accept only bare directory paths.
                if not first_line.startswith("import ") and Path(first_line).is_dir():
                    return first_line
        return None

    def _resolve_via_importlib(self, root: str) -> str | None:
        """
        Universal fallback using :func:`importlib.util.find_spec`.

        Covers every installation format that registers itself with
        Python's import machinery before this code runs, including:

        * **PEP 660 Strategy B** — setuptools / uv editable installs that
          drop an ``__editable__.<pkg>-<ver>.pth`` file which registers a
          custom :class:`importlib.abc.MetaPathFinder` with a ``MAPPING``
          dict pointing to the source tree.
        * **Egg directory** installs — ``easy-install.pth`` adds the
          ``.egg/`` directory to ``sys.path``, so importlib finds the
          package inside it.
        * **Flat dist-info / egg-info installs** (regular pip / uv
          installs, wheel installs) — the package lives directly in
          ``site-packages/``, which is always on ``sys.path``.
        * **Direct-URL non-editable installs** (PEP 610) — result is
          identical to a regular dist-info install.

        Returns the parent of the root package directory so that the
        subsequent ``Path(sp_dir, *chain)`` navigation works uniformly
        for all formats.
        """
        spec = importlib.util.find_spec(root)
        if spec is None:
            return None
        if spec.submodule_search_locations:
            # Package: first search location is the package directory itself.
            return str(Path(spec.submodule_search_locations[0]).parent)
        if spec.origin:
            # Single-file module: origin is the .py file.
            return str(Path(spec.origin).parent)
        return None

    def _find_sp_dir(self, root: str) -> str:
        """
        Return the source-tree root for *root* by trying each resolution
        strategy in priority order, falling back to ``SP_DIR``.
        """
        return (
            self._resolve_via_egg_link(root)
            or self._resolve_via_simple_pth(root)
            or self._resolve_via_importlib(root)
            or SP_DIR
        )

    def _locate_path(self) -> None:
        """
        Set ``self.path`` and ``self.is_single_file`` by navigating from
        the resolved source-tree root through the dot-separated name chain.
        """
        chain = self.name.split(".")  # "a.b.c" -> ["a", "b", "c"]
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
        Example: for package ``pip.commands.install``, it's
        ``pip.commands.install``.
        """
        return self.name

    @property
    def shortname(self) -> str:
        """
        Example: for package ``pip.commands.install``, it's ``install``.
        """
        if "." in self.name:
            return self.name.split(".")[-1]
        else:
            return self.name

    def __eq__(self, other: object) -> bool:
        return self.path == other.path


class Module(BaseModuleOrPackage):
    """
    Represent a module object in Python. Typically it's a ``*.py`` file.

    :param name: module name, e.g.: "pip.commands.install".
    :param path: module file absolute path.
    :param parent: default None, parent package name, list of package
    :param is_single_file: if it is a single file package/module.
    """

    def __repr__(self):
        return "Module(name=%r, path='%s')" % (self.name, self.path)


class Package(BaseModuleOrPackage):
    """
    Represent a package object in Python. It is a directory having a
    ``__init__.py`` file.

    :param name: dot seperated full name, e.g.: "pip.commands.install".
    :param path: package directory/file absolute path.
    :param parent parent: parent package, instance of :class:`Package`.

    **中文文档**

    是Python中Package概念的抽象类。指包含有 ``__init__.py`` 文件的文件夹。
    Package必须可以被import命令所导入, 换言之, 就是已经被成功安装了。

    Package的属性的解释:

    - name: 包名称
    - path: 包目录所在的路径
    - fullname: 包的全名, 带母包
    - shortname: 包的短名称, 也就是最后一个点之后的部分。
    - parent: 母包的实例。
    - is_single_file: 是否是单文件的包。
    - sub_packages: 有序字典, {子包的名称: Package对象}
    - sub_modules: 有序字典, {子模块的名称: Module对象}
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

        self.sub_packages = OrderedDict()
        self.sub_modules = OrderedDict()

        # walk through all sub packages and sub modules
        if self.is_single_file is False:
            for p in sorted(self.path.iterdir()):
                # if it's a directory
                if p.is_dir():
                    # if there is a __init__.py file, must be a sub package
                    if Path(p, "__init__.py").exists():
                        pkg = Package(
                            name=name + "." + p.name,
                            path=p,
                            parent=self,
                            is_single_file=False,
                        )
                        self.sub_packages[p.name] = pkg

                # if it's a file
                else:
                    # if it's a .py file, must be a module
                    if p.suffix == ".py" and p.stem != "__init__":
                        module = Module(
                            name=name + "." + p.stem,
                            path=p,
                            parent=self,
                            is_single_file=True,
                        )
                        self.sub_modules[p.stem] = module

    def __str__(self):
        tpl = (
            "Package("
            "\n{tab}name=%r,"
            "\n{tab}path='%s',"
            "\n{tab}sub_packages=%r,"
            "\n{tab}sub_modules=%r,"
            "\n)"
        ).format(tab=Tab)
        s = tpl % (
            self.name,
            self.path,
            list(self.sub_packages),
            list(self.sub_modules),
        )
        return s

    def __repr__(self):
        return "Package(name=%r, path='%s')" % (self.name, self.path)

    def __getitem__(self, name):
        if "." in name:
            item = self
            for _name in name.split("."):
                item = item[_name]
            return item
        else:
            try:
                return self.sub_packages[name]
            except KeyError:
                try:
                    return self.sub_modules[name]
                except KeyError:
                    raise KeyError("%r doesn't has sub module %r!" % (self.name, name))

    def walk(self, pkg_only=True):
        """
        A generator that walking through all sub packages and sub modules.

        :type pkg_only: bool
        :param pkg_only: if True, it only yields package (folder with __init__.py)
            if False, it also yields module, but they don't have
            sub_packages and sub_modules

        **中文文档**

        遍历一个包的所有子包以及子模块.

        1. current package object (包对象)
        2. current package's parent (当前包对象的母包)
        3. list of sub packages (所有子包)
        4. list of sub modules (所有模块)
        """
        current_module = self
        parent_module = self.parent
        sub_packages = list(self.sub_packages.values())
        sub_modules = list(self.sub_modules.values())

        yield (
            current_module,
            parent_module,
            sub_packages,
            sub_modules,
        )

        for pkg in self.sub_packages.values():
            for things in pkg.walk(pkg_only=pkg_only):
                yield things

        if pkg_only is False:
            for sub_module in self.sub_modules.values():
                yield sub_module, self, [], []

    def _tree_view_builder(self, indent=0, is_root=True):
        """
        Build a text to represent the package structure.
        """

        def pad_text(indent):
            return "    " * indent + "|-- "

        lines = list()

        if is_root:
            lines.append(SP_DIR)

        lines.append("%s%s (%s)" % (pad_text(indent), self.shortname, self.fullname))

        indent += 1

        # sub packages
        for pkg in self.sub_packages.values():
            lines.append(pkg._tree_view_builder(indent=indent, is_root=False))

        # __init__.py
        lines.append(
            "%s%s (%s)"
            % (
                pad_text(indent),
                "__init__.py",
                self.fullname,
            )
        )

        # sub modules
        for mod in self.sub_modules.values():
            lines.append(
                "%s%s (%s)"
                % (
                    pad_text(indent),
                    mod.shortname + ".py",
                    mod.fullname,
                )
            )

        return "\n".join(lines)

    def pprint(self):
        """
        Pretty print the package structure.
        """
        print(self._tree_view_builder(indent=0, is_root=True))
