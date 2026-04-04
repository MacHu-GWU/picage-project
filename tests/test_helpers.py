# -*- coding: utf-8 -*-

import pytest

from picage.helpers import get_sp_dir
from picage.helpers import is_valid_package_module_name
from picage.helpers import assert_is_valid_name


def test_get_sp_dir():
    get_sp_dir()


class TestIsValidPackageModuleName:
    def test_single_lowercase(self):
        assert is_valid_package_module_name("a") is True

    def test_dotted_name(self):
        assert is_valid_package_module_name("a.b.c") is True

    def test_underscore_prefix(self):
        assert is_valid_package_module_name("_a") is True

    def test_underscore_prefix_dotted(self):
        assert is_valid_package_module_name("_a._b._c") is True

    def test_name_with_digits(self):
        assert is_valid_package_module_name("abc123") is True

    def test_name_with_hyphen(self):
        assert is_valid_package_module_name("my-package") is True

    def test_mixed_case_after_first(self):
        assert is_valid_package_module_name("aBC") is True

    def test_uppercase_first(self):
        assert is_valid_package_module_name("A") is False

    def test_digit_first(self):
        assert is_valid_package_module_name("0") is False

    def test_leading_dot(self):
        assert is_valid_package_module_name(".a") is False

    def test_trailing_dot(self):
        assert is_valid_package_module_name("a.") is False

    def test_consecutive_dots(self):
        assert is_valid_package_module_name("a..b") is False

    def test_illegal_char(self):
        assert is_valid_package_module_name("a#b") is False

    def test_empty_string(self):
        assert is_valid_package_module_name("") is False

    def test_dotted_with_invalid_part(self):
        assert is_valid_package_module_name("a.0b.c") is False

    def test_space_in_name(self):
        assert is_valid_package_module_name("a b") is False


class TestAssertIsValidName:
    def test_valid_name_no_error(self):
        assert_is_valid_name("my_package")

    def test_invalid_name_default_error(self):
        with pytest.raises(ValueError):
            assert_is_valid_name("0bad")

    def test_invalid_name_custom_error(self):
        with pytest.raises(TypeError, match="custom"):
            assert_is_valid_name("0bad", error=TypeError("custom"))


if __name__ == "__main__":
    from picage.tests import run_cov_test

    run_cov_test(
        __file__,
        "picage.helpers",
        preview=False,
    )
