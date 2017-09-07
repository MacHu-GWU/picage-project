#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
import os
import sys
import string
import platform
from collections import OrderedDict

try:
    from pathlib_mate.pathlib import Path
except: # pragma: no cover
    pass

__version__ = "0.0.3"
__short_description__ = "Object style interface for package/module."
__license__ = "MIT"
__author__ = "Sanhe Hu"
__author_email__ = "husanhe@gmail.com"
__maintainer__ = "Sanhe Hu"
__maintainer_email__ = "husanhe@gmail.com"
__github_username__ = "MacHu-GWU"

Tab = " " * 4


def get_sp_dir():  # pragma: no cover
    """Get the absolute path of the ``site-packages`` directory.
    """
    py_ver_major = sys.version_info.major
    py_ver_minor = sys.version_info.minor

    system_name = platform.system()
    if system_name == "Windows":
        site_packages_path = os.path.join(
            os.path.dirname(os.path.dirname(sys.executable)),
            "Lib",
            "site-packages",
        )
    elif system_name in ["Darwin", "Linux"]:
        site_packages_path = os.path.join(
            os.path.dirname(os.path.dirname(sys.executable)),
            "lib",
            "python%s.%s" % (py_ver_major, py_ver_minor),
            "site-packages",
        )
    else:
        raise Exception("Unknown Operation System!")
    return site_packages_path


SP_DIR = get_sp_dir()
"""Current system's site-packages directory..
"""

_first_letter_for_valid_name = set(string.ascii_lowercase + "_")
_char_set_for_valid_name = set(string.ascii_letters + string.digits + "_-")


def assert_is_valid_name(name, error=None):
    """Test it's a valid package or module name.

    - a-z, 0-9, and underline
    - starts with underline or alpha letter
    """
    if error is None:
        error = ValueError("%r is not a valid package or module name!" % name)
    try:
        if "." in name:
            for n in name.split("."):
                assert_is_valid_name(n, error=error)
        else:
            if name[0] not in _first_letter_for_valid_name:
                raise error

            if len(set(name).difference(_char_set_for_valid_name)):
                raise error

    except:
        raise error


class BaseModuleOrPackage(object):
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
            print(p)
            if p.is_dir() and p.exists() and Path(p, "__init__.py").exists():
                self.path = Path(sp_dir, *chain)
                self.is_single_file = False
                return

            raise ValueError("Can't found '%s'!" % self.name)
        else:
            self.path = path

    @property
    def fullname(self):
        """Example: ``sphinx.environment.adapter``.
        """
        return self.name

    @property
    def shortname(self):
        """Example: for package ``sphinx.environment.adapter``,
        it's ``adapter``.
        """
        if "." in self.name:
            return self.name.split(".")[-1]
        else:
            return self.name

    def __eq__(self, other):
        return self.path == other.path


class Module(BaseModuleOrPackage):
    """Represent a module object in Python. Typically it's a ``*.py`` file.

    :param name: module name, e.g.: "pip.commands.install".
    :param path: module file absolute path.
    :param parent: default None, parent package name, list of package
    :param is_single_file: if it is a single file package/module.
    """

    def __repr__(self):
        return "Module(name=%r, path='%s')" % (self.name, self.path)


class Package(BaseModuleOrPackage):
    """Represent a package object in Python. It is a directory having a
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
            for p in self.path.iterdir():
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

    def walk(self):
        """A generator that walking through all sub packages and sub modules.

        1. current package object (包对象)
        2. current package's parent (当前包对象的母包)
        3. list of sub packages (所有子包)
        4. list of sub modules (所有模块)
        """
        yield (
            self,
            self.parent,
            list(self.sub_packages.values()),
            list(self.sub_modules.values()),
        )

        for pkg in self.sub_packages.values():
            for things in pkg.walk():
                yield things

    def _tree_view_builder(self, indent=0, is_root=True):
        """Build a text to represent the package structure.
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
        """Pretty print the package structure.
        """
        print(self._tree_view_builder(indent=0, is_root=True))
