Package Installation Formats in site-packages
==============================================================================
When a third-party Python package is installed, its source code and metadata end up in the ``site-packages`` directory. Over the years, multiple installation formats have been used. Below is a summary followed by detailed descriptions of each format.


Summary
------------------------------------------------------------------------------
- **Egg directory / zip** (setuptools legacy): ``packagename-1.0.0-py3.x.egg/`` containing both source and ``EGG-INFO/``; registered via ``easy-install.pth``.
- **Egg-info directory** (setuptools flat install): ``packagename-1.0.0-py3.x.egg-info/`` alongside the package directory in ``site-packages/``.
- **Egg-info single file** (distutils, removed in Python 3.12): ``packagename-1.0.0-py3.x.egg-info`` as a single PKG-INFO file, alongside the package directory.
- **Dist-info directory** (PEP 376 / PEP 427, current standard): ``packagename-1.0.0.dist-info/`` alongside the package directory; contains ``METADATA``, ``RECORD``, ``INSTALLER``, ``WHEEL``.
- **Editable install -- modern** (PEP 660): ``packagename-1.0.0.dist-info/`` with a ``.pth`` file or custom finder that redirects imports to the source tree.
- **Editable install -- legacy** (setuptools develop): ``packagename.egg-link`` + ``easy-install.pth`` pointing to the source tree; ``.egg-info/`` lives in the source tree.
- **Direct URL recording** (PEP 610): ``direct_url.json`` inside ``.dist-info/`` recording VCS, archive, or local directory origin.
- **Namespace packages** (implicit, Python 3.3+): directories without ``__init__.py``; multiple distributions contribute sub-packages under one namespace.
- **.pth files** (general mechanism): text files processed at startup to extend ``sys.path`` or execute import statements.


Setuptools Egg Format (Legacy)
------------------------------------------------------------------------------
No formal PEP standardized eggs. The egg format was invented by setuptools and was the de facto standard before wheels. Pip 23.3 (2023) dropped egg installation support.

Created by ``python setup.py install`` (with setuptools) or ``easy_install``.

There are two sub-formats:

**Egg directory or zip file** -- the package source lives inside a ``.egg`` directory (or zip):

.. code-block:: text

    site-packages/
        easy-install.pth                          # lists .egg paths
        packagename-1.0.0-py3.x.egg/             # directory or zip
            EGG-INFO/
                PKG-INFO
                SOURCES.txt
                dependency_links.txt
                entry_points.txt
                requires.txt
                top_level.txt
            packagename/
                __init__.py
                ...

**Egg-info directory** (flat install) -- created by pip's internal ``setup.py install --single-version-externally-managed``. Source code is installed flat in ``site-packages/``:

.. code-block:: text

    site-packages/
        packagename-1.0.0-py3.x.egg-info/        # metadata directory
            PKG-INFO
            SOURCES.txt
            dependency_links.txt
            requires.txt
            top_level.txt
        packagename/                              # source code, flat
            __init__.py
            ...


Distutils Source Install (Legacy, removed in Python 3.12)
------------------------------------------------------------------------------
- `PEP 632 -- Deprecate distutils <https://peps.python.org/pep-0632/>`_

Created by ``python setup.py install`` without setuptools. Distutils was deprecated in Python 3.10 and removed in Python 3.12.

The ``.egg-info`` was a **single file** (not a directory) containing only PKG-INFO metadata. No ``RECORD`` file, making clean uninstallation impossible.

.. code-block:: text

    site-packages/
        packagename-1.0.0-py3.x.egg-info         # single file, not a directory
        packagename/
            __init__.py
            ...


PEP 376 -- Database of Installed Python Distributions
------------------------------------------------------------------------------
- `PEP 376 <https://peps.python.org/pep-0376/>`_

PEP 376 defines the ``.dist-info`` directory structure that records metadata for an installed distribution. This is the current standard metadata format used by all modern installers (pip, uv, etc.).

.. code-block:: text

    site-packages/
        packagename-1.0.0.dist-info/
            METADATA          # mandatory, core metadata (PEP 566/643)
            RECORD            # mandatory, CSV of all installed files with hashes
            INSTALLER         # mandatory, name of the installing tool (e.g. "pip")
            WHEEL             # wheel metadata (generator, tags)
            REQUESTED         # optional, present if user explicitly requested it
            entry_points.txt  # optional, console_scripts etc.
            top_level.txt     # optional, legacy
            licenses/         # optional, license files (PEP 639)
        packagename/
            __init__.py
            ...

The ``RECORD`` file is a CSV with columns: filepath, hash (``sha256=...``), size. It enables clean uninstallation by listing every installed file.


PEP 427 -- The Wheel Binary Package Format
------------------------------------------------------------------------------
- `PEP 427 <https://peps.python.org/pep-0427/>`_

PEP 427 defines the ``.whl`` archive format (a zip file with a specific naming convention). When pip installs a wheel, it unpacks the archive into ``site-packages/`` resulting in the PEP 376 ``.dist-info`` layout described above.

A wheel filename encodes metadata: ``{name}-{version}(-{build})?-{python}-{abi}-{platform}.whl``.

After installation, the result in ``site-packages/`` is identical to the PEP 376 format. For single-file modules:

.. code-block:: text

    site-packages/
        packagename-1.0.0.dist-info/
            METADATA
            RECORD
            INSTALLER
            WHEEL
        packagename.py                            # single-file module


PEP 517/518 -- Build System Interface
------------------------------------------------------------------------------
- `PEP 517 <https://peps.python.org/pep-0517/>`_
- `PEP 518 <https://peps.python.org/pep-0518/>`_

These PEPs do **not** define a new format in ``site-packages``. They define the interface between build frontends (pip) and build backends (setuptools, hatchling, flit, etc.).

PEP 518 introduced ``pyproject.toml`` with the ``[build-system]`` table. PEP 517 defines the hooks backends must implement (``build_wheel()``, ``build_sdist()``).

The end result in ``site-packages/`` is still a standard ``.dist-info`` installation (PEP 376/427).


PEP 610 -- Recording the Direct URL Origin
------------------------------------------------------------------------------
- `PEP 610 <https://peps.python.org/pep-0610/>`_

When a package is installed from a direct URL (not from PyPI index), a ``direct_url.json`` file is added inside the ``.dist-info/`` directory.

Contents vary by install source:

.. code-block:: text

    # VCS install (pip install git+https://...)
    {"url": "https://github.com/...", "vcs_info": {"vcs": "git", "commit_id": "abc123"}}

    # Local directory install
    {"url": "file:///path/to/project", "dir_info": {"editable": false}}

    # Editable install
    {"url": "file:///path/to/project", "dir_info": {"editable": true}}


PEP 660 -- Editable Installs (Modern)
------------------------------------------------------------------------------
- `PEP 660 <https://peps.python.org/pep-0660/>`_

Created by ``pip install -e .`` with a PEP 517-compliant backend (setuptools >= 64, hatchling, flit, etc.). The build backend produces an "editable wheel" that redirects imports to the source tree.

The actual mechanism depends on the backend. Two common strategies:

**Strategy A: .pth file with path insertion**

.. code-block:: text

    site-packages/
        packagename-1.0.0.dist-info/
            METADATA
            RECORD
            INSTALLER
            WHEEL
            direct_url.json                       # {"dir_info": {"editable": true}}
        packagename.pth                           # contains: /path/to/source/project/src

**Strategy B: .pth file + custom finder module** (setuptools default)

.. code-block:: text

    site-packages/
        packagename-1.0.0.dist-info/
            METADATA
            RECORD
            INSTALLER
            WHEEL
            direct_url.json
        __editable__.packagename-1.0.0.pth        # imports the finder module
        __editable___packagename_1_0_0_finder.py   # MetaPathFinder with MAPPING dict

The ``.pth`` file imports the finder module at startup. The finder module contains a ``MAPPING`` dictionary that redirects imports to the source tree.


Legacy Editable Install (.egg-link)
------------------------------------------------------------------------------
No formal PEP. This was the setuptools mechanism before PEP 660.

Created by ``python setup.py develop`` or ``pip install -e .`` with old setuptools.

.. code-block:: text

    site-packages/
        packagename.egg-link                      # text file: path to source dir
        easy-install.pth                          # modified to include source path

    /path/to/source/project/
        packagename-1.0.0-py3.x.egg-info/        # metadata in SOURCE tree
            PKG-INFO
            ...
        packagename/
            __init__.py
            ...

The ``.egg-link`` file contains the path to the project source directory. The ``easy-install.pth`` file adds that path to ``sys.path`` at startup.


Namespace Packages
------------------------------------------------------------------------------
Namespace packages allow a single logical package to be split across multiple distributions. There are three mechanisms:

**Implicit namespace packages** (Python 3.3+, current standard): a directory without ``__init__.py`` is treated as a namespace package. Multiple distributions contribute sub-packages:

.. code-block:: text

    site-packages/
        mynamespace/                              # NO __init__.py
            subpkg_a/                             # from distribution A
                __init__.py
            subpkg_b/                             # from distribution B
                __init__.py
        mynamespace_subpkg_a-1.0.dist-info/
        mynamespace_subpkg_b-2.0.dist-info/

**pkgutil-style** (legacy, still works): each portion has an ``__init__.py`` with ``__path__ = __import__('pkgutil').extend_path(__path__, __name__)``.

**setuptools pkg_resources-style** (legacy): each portion has an ``__init__.py`` with ``__import__('pkg_resources').declare_namespace(__name__)``, plus a ``mynamespace-nspkg.pth`` file in ``site-packages/``.


.pth Files (General Mechanism)
------------------------------------------------------------------------------
``.pth`` files are processed by Python at startup. Any file with a ``.pth`` extension in ``site-packages/`` is read line by line:

- Lines that are directory paths: added to ``sys.path``
- Lines starting with ``import``: executed as Python code

Common examples:

.. code-block:: text

    easy-install.pth                  # setuptools: lists .egg paths
    packagename.pth                   # editable install: adds source dir
    __editable__.pkg-1.0.pth          # PEP 660: imports a custom finder
    mynamespace-nspkg.pth             # setuptools namespace package setup
