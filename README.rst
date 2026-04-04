
.. image:: https://readthedocs.org/projects/picage/badge/?version=latest
    :target: https://picage.readthedocs.io/en/latest/
    :alt: Documentation Status

.. image:: https://github.com/MacHu-GWU/picage-project/actions/workflows/main.yml/badge.svg
    :target: https://github.com/MacHu-GWU/picage-project/actions?query=workflow:CI

.. image:: https://codecov.io/gh/MacHu-GWU/picage-project/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/MacHu-GWU/picage-project

.. image:: https://img.shields.io/pypi/v/picage.svg
    :target: https://pypi.python.org/pypi/picage

.. image:: https://img.shields.io/pypi/l/picage.svg
    :target: https://pypi.python.org/pypi/picage

.. image:: https://img.shields.io/pypi/pyversions/picage.svg
    :target: https://pypi.python.org/pypi/picage

.. image:: https://img.shields.io/badge/✍️_Release_History!--None.svg?style=social&logo=github
    :target: https://github.com/MacHu-GWU/picage-project/blob/main/release-history.rst

.. image:: https://img.shields.io/badge/⭐_Star_me_on_GitHub!--None.svg?style=social&logo=github
    :target: https://github.com/MacHu-GWU/picage-project

------

.. image:: https://img.shields.io/badge/Link-API-blue.svg
    :target: https://picage.readthedocs.io/en/latest/py-modindex.html

.. image:: https://img.shields.io/badge/Link-Install-blue.svg
    :target: `install`_

.. image:: https://img.shields.io/badge/Link-GitHub-blue.svg
    :target: https://github.com/MacHu-GWU/picage-project

.. image:: https://img.shields.io/badge/Link-Submit_Issue-blue.svg
    :target: https://github.com/MacHu-GWU/picage-project/issues

.. image:: https://img.shields.io/badge/Link-Request_Feature-blue.svg
    :target: https://github.com/MacHu-GWU/picage-project/issues

.. image:: https://img.shields.io/badge/Link-Download-blue.svg
    :target: https://pypi.org/pypi/picage#files


Welcome to ``picage`` Documentation
==============================================================================
``picage`` is a lightweight utility library that provides an object-oriented interface for inspecting Python package and module structure. Given any installed package name, it automatically locates the source code on the current Python import path and lets you explore its structure. You can access:

- fully qualified name and short name of any package or module
- parent package, sub-packages, and sub-modules
- recursively walk through all sub-packages and sub-modules
- pretty-print the entire package tree

``picage`` supports all common installation formats including flat dist-info/wheel installs, legacy egg-link editable installs, PEP 660 editable installs (both path-insertion and custom-finder strategies), and legacy egg-directory installs.


Usage
------------------------------------------------------------------------------

.. code-block:: python

    >>> from picage.api import Package

    >>> pkg = Package("requests")
    >>> pkg
    Package(name='requests', path='/.../site-packages/requests')

    >>> print(pkg)
    Package(
        name='requests',
        path='/.../site-packages/requests',
        sub_packages=[...],
        sub_modules=['adapters', 'api', 'auth', ...],
    )

    # Access sub-packages and sub-modules
    >>> for name, sub_pkg in pkg.sub_packages.items():
    ...     print(name, sub_pkg.fullname)

    >>> for name, mod in pkg.sub_modules.items():
    ...     print(name, mod.fullname)

    # Use dot notation to access nested children
    >>> mod = pkg["api"]              # direct child module
    >>> deep = pkg["commands.install"]  # dot notation for deeper access

    # Walk through the entire package tree
    >>> for node, parent, sub_pkgs, sub_mods in pkg.walk():
    ...     print(node.fullname)

    # Include leaf modules in the walk
    >>> for node, parent, sub_pkgs, sub_mods in pkg.walk(pkg_only=False):
    ...     print(node.fullname)

    # Navigate the parent chain
    >>> child = pkg["utils"]
    >>> child.parent is pkg
    True
    >>> pkg.parent is None
    True

    # Pretty-print the package tree
    >>> pkg.pprint()
    /.../site-packages
    |-- requests (requests)
        |-- ...


.. _install:

Install
------------------------------------------------------------------------------

``picage`` is released on PyPI, so all you need is:

.. code-block:: console

    $ pip install picage

To upgrade to latest version:

.. code-block:: console

    $ pip install --upgrade picage
