# -*- coding: utf-8 -*-

import pytest
from pytest import raises
from pathlib import Path

import sphinx
import sphinx.builders
import sphinx.builders.html

import picage
from picage.model import Package, Module


def assert_is_strictly_ascending(l):
    for i, j in zip(l[:-1], l[1:]):
        assert i < j


class BaseTest:
    importable = None
    pkg = None

    def setup_method(self):
        self.pkg = Package(self.importable.__name__)

    def test_display(self):
        print(self.pkg)
        self.pkg.pprint()


class TestSphinx(BaseTest):
    importable = sphinx

    def test_name(self):
        assert self.pkg.name == "sphinx"
        assert self.pkg.shortname == "sphinx"
        assert self.pkg.fullname == "sphinx"

    def test_parent(self):
        builders = self.pkg["builders"]
        html = builders["html"]

        assert builders.parent == self.pkg
        assert html.parent == builders

    def test_get_item(self):
        assert self.pkg["builders"] == Package("sphinx.builders")
        assert self.pkg["builders.html"] == Module("sphinx.builders.html")

        with raises(KeyError):
            self.pkg["Not Exists!"]

    def test_walk(self):
        for _, _, sub_packages, sub_modules in self.pkg.walk():
            assert_is_strictly_ascending([i.fullname for i in sub_packages])
            assert_is_strictly_ascending([i.fullname for i in sub_modules])

        assert len(list(Path(self.pkg.path).rglob("*.py"))) == len(
            list(self.pkg.walk(pkg_only=False))
        )


class TestSphinxBuilders(BaseTest):
    importable = sphinx.builders

    def test_name(self):
        assert self.pkg.name == "sphinx.builders"
        assert self.pkg.shortname == "builders"
        assert self.pkg.fullname == "sphinx.builders"


def test_module():
    module = Module(sphinx.builders.html.__name__)

    assert module.name == "sphinx.builders.html"
    assert module.shortname == "html"
    assert module.fullname == "sphinx.builders.html"


class TestPicage(BaseTest):
    importable = picage


def test_not_found():
    with raises(Exception):
        p = Package("not_existing_package")


if __name__ == "__main__":
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
