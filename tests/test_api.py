# -*- coding: utf-8 -*-

from picage import api


def test():
    _ = api


if __name__ == "__main__":
    from picage.tests import run_cov_test

    run_cov_test(
        __file__,
        "picage.api",
        preview=False,
    )
