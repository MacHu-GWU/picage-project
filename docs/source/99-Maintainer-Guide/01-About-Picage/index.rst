About Picage
==============================================================================
``picage`` is a lightweight utility library that provides an object-oriented interface for inspecting Python package and module structure. The core idea is simple:

.. code-block:: python

    from picage.api import Package

    pkg = Package("package_name")

Given any installed package name, ``picage`` automatically locates the source code on the current Python import path and lets you walk through its structure. You can access a package's sub-packages, sub-modules, parent package, and recursively traverse the entire tree -- all through a clean, Pythonic API.
