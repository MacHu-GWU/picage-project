#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from pytest import raises

import pip
import pip._internal.commands
import pip._internal.commands.install

import six
import picage
from picage.model import Package, Module


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
        commands = self.pkg["_internal"]["commands"]
        install = commands["install"]

        assert commands.parent.parent == self.pkg
        assert install.parent == commands

    def test_get_item(self):
        assert self.pkg["_internal"]["commands"] == Package(
            "pip._internal.commands")
        assert self.pkg["_internal"]["basecommand"] == Module(
            "pip._internal.basecommand")
        assert self.pkg["_internal"]["commands.install"] == Module(
            "pip._internal.commands.install")

        with raises(KeyError):
            self.pkg["Not Exists!"]

    def test_walk(self):
        for tp in self.pkg.walk():
            pass


class TestPipCommands(BaseTest):
    importable = pip._internal.commands

    def test_name(self):
        assert self.pkg.name == "pip._internal.commands"
        assert self.pkg.shortname == "commands"
        assert self.pkg.fullname == "pip._internal.commands"


def test_module():
    module = Module(pip._internal.commands.install.__name__)

    assert module.name == "pip._internal.commands.install"
    assert module.shortname == "install"
    assert module.fullname == "pip._internal.commands.install"


class TestSix(BaseTest):
    importable = six


class TestPicage(BaseTest):
    importable = picage


def test_not_found():
    with raises(Exception):
        p = Package("not_existing_package")


if __name__ == "__main__":
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
