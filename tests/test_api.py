# -*- coding: utf-8 -*-

from picage import api


def test():
    _ = api
    _ = api.SP_DIR
    _ = api.get_sp_dir
    _ = api.is_valid_package_module_name
    _ = api.Module
    _ = api.Package


if __name__ == "__main__":
    from picage.tests import run_cov_test

    run_cov_test(
        __file__,
        "picage.api",
        preview=False,
    )
