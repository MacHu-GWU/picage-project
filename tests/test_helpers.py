# -*- coding: utf-8 -*-

import pytest
from picage.helpers import get_sp_dir, is_valid_package_module_name


def test_get_sp_dir():
    get_sp_dir()


def test_is_valid_package_module_name():
    assert is_valid_package_module_name("a") is True
    assert is_valid_package_module_name("a.b.c") is True
    assert is_valid_package_module_name("_a") is True
    assert is_valid_package_module_name("_a._b._c") is True

    assert is_valid_package_module_name("A") is False
    assert is_valid_package_module_name("0") is False
    assert is_valid_package_module_name(".a") is False
    assert is_valid_package_module_name("a#b") is False


if __name__ == "__main__":
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
