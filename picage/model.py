# -*- coding: utf-8 -*-

"""
:class:`Module`, :class:`Package` data model.
"""

from pathlib_mate import Path
from collections import OrderedDict
from .helpers import SP_DIR, assert_is_valid_name

Tab = " " * 4


class BaseModuleOrPackage(object):
    """
    Base Class to represent a module or package.
    """

    def __init__(self, name, path=None, parent=None, is_single_file=None):
        assert_is_valid_name(name)

        self.name = name
        self.parent = parent
        self.is_single_file = is_single_file

        if path is None:
            chain = self.name.split(".")  # "a.b.c" -> ["a", "b", "c"]
            root = chain[0]

            # test if using .egg-link
            p = Path(SP_DIR, root.replace("_", "-") + ".egg-link")
            if p.is_file() and p.exists():
                with open(p.abspath, "rb") as f:
                    sp_dir = f.readline().decode("utf-8").strip()
            else:
                sp_dir = SP_DIR

            # is single file package
            p = Path(Path(sp_dir, *chain).abspath + ".py")
            if p.is_file() and p.exists():
                self.path = p
                self.is_single_file = True
                return

            # then has to be a directory having __init__.py file
            p = Path(sp_dir, *chain)
            if p.is_dir() and p.exists() and Path(p, "__init__.py").exists():
                self.path = Path(sp_dir, *chain)
                self.is_single_file = False
                return

            raise ValueError("Can't found '%s'!" % self.name)
        else:
            self.path = path

    @property
    def fullname(self):
        """
        Example: for package ``pip.commands.install``, it's
        ``pip.commands.install``.
        """
        return self.name

    @property
    def shortname(self):
        """
        Example: for package ``pip.commands.install``, it's ``install``.
        """
        if "." in self.name:
            return self.name.split(".")[-1]
        else:
            return self.name

    def __eq__(self, other):
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

    def __init__(self, name, path=None, parent=None, is_single_file=None):
        super(Package, self).__init__(
            name, path=path, parent=parent, is_single_file=is_single_file)

        self.sub_packages = OrderedDict()
        self.sub_modules = OrderedDict()

        # walk through all sub packages and sub modules
        if self.is_single_file is False:
            for p in Path.sort_by_abspath(self.path.iterdir()):
                # if it's a directory
                if p.is_dir():
                    # if there is a __init__.py file, must be a sub package
                    if Path(p, "__init__.py").exists():
                        pkg = Package(
                            name=name + "." + p.basename,
                            path=p,
                            parent=self,
                            is_single_file=False,
                        )
                        self.sub_packages[p.basename] = pkg

                # if it's a file
                else:
                    # if it's a .py file, must be a module
                    if p.ext == ".py" and p.fname != "__init__":
                        module = Module(
                            name=name + "." + p.fname,
                            path=p,
                            parent=self,
                            is_single_file=True,
                        )
                        self.sub_modules[p.fname] = module

    def __str__(self):
        tpl = ("Package("
               "\n{tab}name=%r,"
               "\n{tab}path='%s',"
               "\n{tab}sub_packages=%r,"
               "\n{tab}sub_modules=%r,"
               "\n)").format(tab=Tab)
        s = tpl % (
            self.name, self.path,
            list(self.sub_packages), list(self.sub_modules),
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
                    raise KeyError("%r doesn't has sub module %r!" % (
                        self.name, name))

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

        lines.append(
            "%s%s (%s)" % (pad_text(indent), self.shortname, self.fullname)
        )

        indent += 1

        # sub packages
        for pkg in self.sub_packages.values():
            lines.append(pkg._tree_view_builder(indent=indent, is_root=False))

        # __init__.py
        lines.append(
            "%s%s (%s)" % (
                pad_text(indent), "__init__.py", self.fullname,
            )
        )

        # sub modules
        for mod in self.sub_modules.values():
            lines.append(
                "%s%s (%s)" % (
                    pad_text(indent), mod.shortname + ".py", mod.fullname,
                )
            )

        return "\n".join(lines)

    def pprint(self):
        """
        Pretty print the package structure.
        """
        print(self._tree_view_builder(indent=0, is_root=True))
