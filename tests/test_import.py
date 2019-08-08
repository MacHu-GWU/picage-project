# -*- coding: utf-8 -*-

import pytest
from pytest import raises, approx


def test():
    import picage
    picage.SP_DIR
    picage.is_valid_package_module_name
    picage.Module
    picage.Package


if __name__ == "__main__":
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
