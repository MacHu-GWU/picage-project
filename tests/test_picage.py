#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from pytest import raises

import pip
import pip.commands
import pip.commands.install

import six
import picage
from picage import assert_is_valid_name, Package, Module


def test_assert_is_valid_name():
    assert_is_valid_name("a")
    assert_is_valid_name("a.b.c")

    assert_is_valid_name("_a")
    assert_is_valid_name("_a._b._c")

    with raises(ValueError):
        assert_is_valid_name("A")

    with raises(ValueError):
        assert_is_valid_name("0")

    with raises(ValueError):
        assert_is_valid_name(".a")

    with raises(ValueError):
        assert_is_valid_name("a#b")


class BaseTest:
    importable = None
    pkg = None

    def setup_method(self):
        self.pkg = Package(self.importable.__name__)

    def test_display(self):
        print(self.pkg)
        self.pkg.pprint()


class TestPip(BaseTest):
    importable = pip

    def test_name(self):
        assert self.pkg.name == "pip"
        assert self.pkg.shortname == "pip"
        assert self.pkg.fullname == "pip"

    def test_parent(self):
        commands = self.pkg["commands"]
        install = commands["install"]

        assert commands.parent == self.pkg
        assert install.parent == commands

    def test_get_item(self):
        assert self.pkg["commands"] == Package("pip.commands")
        assert self.pkg["basecommand"] == Module("pip.basecommand")
        assert self.pkg["commands.install"] == Module("pip.commands.install")

        with raises(KeyError):
            self.pkg["Not Exists!"]

    def test_walk(self):
        for tp in self.pkg.walk():
            pass


class TestPipCommands(BaseTest):
    importable = pip.commands

    def test_name(self):
        assert self.pkg.name == "pip.commands"
        assert self.pkg.shortname == "commands"
        assert self.pkg.fullname == "pip.commands"


def test_module():
    module = Module(pip.commands.install.__name__)

    assert module.name == "pip.commands.install"
    assert module.shortname == "install"
    assert module.fullname == "pip.commands.install"


class TestSix(BaseTest):
    importable = six


class TestPicage(BaseTest):
    importable = picage


if __name__ == "__main__":
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
