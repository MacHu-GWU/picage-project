Implementation Internals
==============================================================================
This document explains how ``picage`` resolves a Python package or module name
to a file-system path, and how the resulting object tree is built.  It is aimed
at maintainers and contributors who need to understand or extend the library.


Class Hierarchy
------------------------------------------------------------------------------
Everything in the public API descends from
:class:`picage.model.BaseModuleOrPackage`.  This base class holds the common
attributes (``name``, ``path``, ``parent``, ``is_single_file``) and owns the
entire path-resolution pipeline.

:class:`picage.model.Module` inherits from the base class without adding new
behaviour.  It represents a single ``.py`` file.

:class:`picage.model.Package` also inherits from the base class, but its
``__init__`` additionally walks the resolved directory on disk and populates
``sub_packages`` and ``sub_modules`` by recursively constructing child
:class:`~picage.model.Package` and :class:`~picage.model.Module` instances.
Child objects are always constructed with an explicit ``path=`` argument, so
the path-resolution pipeline is only invoked once — for the root object the
caller creates.


Construction Flow
------------------------------------------------------------------------------
When a :class:`~picage.model.Package` or :class:`~picage.model.Module` is
instantiated without an explicit ``path`` argument, the constructor delegates
to :meth:`picage.model.BaseModuleOrPackage._locate_path`, which orchestrates
the two-step resolution:

1. **Find the source-tree root** — call
   :meth:`picage.model.BaseModuleOrPackage._find_sp_dir` to obtain the
   directory from which the dot-separated name chain can be navigated.

2. **Navigate the chain** — walk ``Path(sp_dir, *chain)`` to locate the
   concrete file or directory, then set ``self.path`` and
   ``self.is_single_file`` accordingly.  A path ending in ``.py`` that exists
   as a file is classified as a single-file module; a directory that contains
   an ``__init__.py`` is classified as a package.

If neither form is found, :meth:`~picage.model.BaseModuleOrPackage._locate_path`
raises :exc:`ValueError`.

When an explicit ``path`` is provided (as happens for all recursively created
children), the constructor stores it directly and skips the pipeline entirely.


Source-Tree Root Resolution
------------------------------------------------------------------------------
:meth:`picage.model.BaseModuleOrPackage._find_sp_dir` tries three specialised
strategies in order and returns the result of the first one that succeeds.  If
all three return ``None`` it falls back to the ``sp_dir`` parameter itself
(which defaults to the active interpreter's ``site-packages`` directory).


Strategy 1 — Legacy egg-link
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:meth:`picage.model.BaseModuleOrPackage._resolve_via_egg_link` looks for a
``<root>.egg-link`` file in ``sp_dir``.  Because distribution names may use
hyphens where import names use underscores, it tries the hyphenated variant
first (``my-pkg.egg-link``) and then the original (``my_pkg.egg-link``).

The ``.egg-link`` format is a plain text file.  Its first line is the absolute
path to the project source directory — the directory that contains the
top-level package folder.  Reading that first line gives the source-tree root
directly.

This strategy covers editable installs created by ``python setup.py develop``
or ``pip install -e .`` with old setuptools (pre-PEP 660).


Strategy 2 — Plain path-insertion ``.pth`` file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:meth:`picage.model.BaseModuleOrPackage._resolve_via_simple_pth` looks for a
``<root>.pth`` (or ``<root-hyphenated>.pth``) file in ``sp_dir``.

A ``.pth`` file can contain either a bare directory path or a Python ``import``
statement (Python processes both at interpreter startup).  The method reads the
first line and accepts it **only** if it does not start with ``import `` and
the path it names is an existing directory.  This filter is essential: it
prevents the method from misidentifying the ``__editable__.<pkg>-<ver>.pth``
files used by PEP 660 Strategy B — those files start with
``import __editable___...`` and are intentionally left for Strategy 3 to
handle.

When the check passes, the first line is the source-tree root.

This strategy covers PEP 660 Strategy A editable installs produced by build
backends such as hatchling and flit.


Strategy 3 — importlib universal fallback
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:meth:`picage.model.BaseModuleOrPackage._resolve_via_importlib` calls
:func:`importlib.util.find_spec` with the root package name and derives the
source-tree root from the returned :class:`~importlib.machinery.ModuleSpec`.

The ``ModuleSpec`` carries two relevant attributes:

``submodule_search_locations``
    A list of directories that Python searches for the package's sub-modules
    and sub-packages.  For a regular package this list contains exactly one
    entry — the package directory itself (e.g. ``.../site-packages/sphinx/``).
    Taking the parent of that directory yields the source-tree root
    (e.g. ``.../site-packages/``).

``origin``
    The absolute path to the file that implements the module.  For a package
    this is usually its ``__init__.py``, but ``submodule_search_locations`` is
    always set for packages, so the method only reaches ``origin`` for
    single-file modules (e.g. a ``six.py`` that lives directly in
    ``site-packages``).  Taking the parent of ``origin`` gives the containing
    directory.

Because :func:`~importlib.util.find_spec` consults the entirety of
``sys.path`` and all registered :class:`~importlib.abc.MetaPathFinder`
instances, this single strategy covers several installation formats at once:

* **PEP 660 Strategy B** — the ``__editable__.<pkg>-<ver>.pth`` file was
  processed at interpreter startup, which imported the custom finder module and
  registered it in ``sys.meta_path``.  Any subsequent call to
  :func:`~importlib.util.find_spec` therefore goes through that finder and
  returns the spec pointing to the source tree.

* **Egg directory installs** — ``easy-install.pth`` added the ``.egg``
  directory to ``sys.path`` at startup, so :func:`~importlib.util.find_spec`
  finds the package inside it.

* **Flat dist-info / egg-info installs** — the package directory sits directly
  in ``site-packages``, which is always on ``sys.path``.

* **Direct-URL non-editable installs** (PEP 610) — result is identical to a
  flat dist-info install from the import-machinery perspective.

The method also accepts an ``extra_sys_path`` argument.  When provided, those
directories are temporarily prepended to ``sys.path`` before
:func:`~importlib.util.find_spec` is called and restored afterwards.  This is
the dependency-injection seam used by the test suite: rather than depending on
global interpreter state (real installs in the active environment), tests pass
a directory containing a fake package tree.


Dependency Injection for Testing
------------------------------------------------------------------------------
Both :class:`~picage.model.Package` and :class:`~picage.model.Module` expose
two optional constructor parameters that make the entire resolution pipeline
testable in isolation without touching the real ``site-packages`` directory:

``sp_dir``
    Overrides the site-packages directory used by
    :meth:`~picage.model.BaseModuleOrPackage._resolve_via_egg_link`,
    :meth:`~picage.model.BaseModuleOrPackage._resolve_via_simple_pth`, and
    the final fallback in
    :meth:`~picage.model.BaseModuleOrPackage._find_sp_dir`.
    Tests point this at a temporary directory populated by the ``fake_sp``
    pytest fixture.

``extra_sys_path``
    Forwarded to
    :meth:`~picage.model.BaseModuleOrPackage._resolve_via_importlib`.
    Tests use this to make a fake package tree visible to
    :func:`~importlib.util.find_spec` without permanently modifying
    ``sys.path``.

These two parameters together mean every resolution code-path can be exercised
against a fully controlled, hermetic fake installation — no real packages need
to be installed and no global state is mutated between tests.


Package Tree Construction
------------------------------------------------------------------------------
Once :meth:`~picage.model.BaseModuleOrPackage._locate_path` has set
``self.path`` and ``self.is_single_file``, the :class:`~picage.model.Package`
constructor iterates over the resolved directory with
:py:func:`~pathlib.Path.iterdir`.

For each entry it applies two classification rules:

* A **sub-directory** that contains an ``__init__.py`` is treated as a
  sub-package.  A :class:`~picage.model.Package` is constructed with
  ``path=<directory>`` (bypassing resolution) and stored in ``sub_packages``
  under the directory's bare name.

* A **``.py`` file** whose stem is not ``__init__`` is treated as a
  sub-module.  A :class:`~picage.model.Module` is constructed with
  ``path=<file>`` and stored in ``sub_modules`` under the file stem.

All other entries (data directories, ``__pycache__``, compiled extensions,
etc.) are silently skipped.  The process recurses automatically because each
child :class:`~picage.model.Package` repeats the same walk during its own
construction.  The result is a fully populated, eagerly built tree rooted at
the object the caller created.
