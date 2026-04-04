.. _release_history:

Release and Version History
==============================================================================


Backlog (TODO)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

**Minor Improvements**

**Bugfixes**

**Miscellaneous**


1.0.0 (2026-04-04)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- Rewrote path resolution pipeline to support all known PEP installation formats: flat dist-info/wheel installs (PEP 376/427), legacy egg-link editable installs, PEP 660 Strategy A (``.pth`` path-insertion), PEP 660 Strategy B (custom importlib finder), and legacy egg-directory installs.
- Added ``sp_dir`` and ``extra_sys_path`` constructor parameters to ``Package`` and ``Module`` for dependency injection, enabling hermetic testing without touching real ``site-packages``.
- Introduced ``BaseModuleOrPackage`` base class with a clean three-strategy resolution pipeline (egg-link → simple pth → importlib fallback).
- Improved code quality: added comprehensive type annotations, detailed docstrings, and clearer class hierarchy.

**Minor Improvements**

- Migrated project tooling to mise + uv + Claude Code for faster development workflow.
- Refactored internal helpers into a dedicated ``picage.helpers`` module.

**Miscellaneous**

- Significantly expanded test suite with a mixin-based approach covering all five installation formats, walk behavior, equality semantics, and error cases.
- Updated README with modern usage examples reflecting the 1.0.0 API.


0.2.2 (2024-01-12)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- Add support for both hyphen and underscore in the ``.egg-link`` or ``.pth`` file.


0.2.1 (2023-02-27)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- add support to ``*.pth`` file


0.1.0 (2019-10-01)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- First Stable Version


0.0.1 (2017-09-06)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- First release