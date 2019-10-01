
.. image:: https://readthedocs.org/projects/picage/badge/?version=latest
    :target: https://picage.readthedocs.io/index.html
    :alt: Documentation Status

.. image:: https://travis-ci.org/MacHu-GWU/picage-project.svg?branch=master
    :target: https://travis-ci.org/MacHu-GWU/picage-project?branch=master

.. image:: https://codecov.io/gh/MacHu-GWU/picage-project/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/MacHu-GWU/picage-project

.. image:: https://img.shields.io/pypi/v/picage.svg
    :target: https://pypi.python.org/pypi/picage

.. image:: https://img.shields.io/pypi/l/picage.svg
    :target: https://pypi.python.org/pypi/picage

.. image:: https://img.shields.io/pypi/pyversions/picage.svg
    :target: https://pypi.python.org/pypi/picage

.. image:: https://img.shields.io/badge/STAR_Me_on_GitHub!--None.svg?style=social
    :target: https://github.com/MacHu-GWU/picage-project

------


.. image:: https://img.shields.io/badge/Link-Document-blue.svg
      :target: https://picage.readthedocs.io/index.html

.. image:: https://img.shields.io/badge/Link-API-blue.svg
      :target: https://picage.readthedocs.io/py-modindex.html

.. image:: https://img.shields.io/badge/Link-Source_Code-blue.svg
      :target: https://picage.readthedocs.io/py-modindex.html

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
``picage`` provides a object style interface to handle Python package module / file structure. It gives you simple api to access:

- a fullname, shortname of a python module
- parent, sub packages and sub modules
- recursively walk through all sub packages and sub modules

.. note::

    Python is a Dyanamic Type Programming language, everything in Python
    is an object, including python package and module.


Usage
------------------------------------------------------------------------------

.. code-block:: python

    >>> from picage import Package

    >>> pip = Package("pip")
    >>> pip
    Package(name='pip', path='./venv/lib/python2.7/site-packages/pip')

    >>> print(pip)
    Package(
        name='pip',
        path='./venv/lib/python2.7/site-packages/pip',
        sub_packages=['_vendor', 'commands', 'compat', 'models', 'operations', 'req', 'utils', 'vcs'],
        sub_modules=['__main__', 'basecommand', 'baseparser', 'cmdoptions', 'download', 'exceptions', 'index', 'locations', 'pep425tags', 'status_codes', 'wheel'],
    )

    # visit sub packages
    >>> for package_name, package in pip.sub_packages().items():
        ...

    # visit sub modules
    >>> for module_name, module in pip.sub_modules().items():
        ...

    # walk through all sub packages modules
    >>> for pkg, parent_pkg, sub_pkg_list, sub_module_list in pip.walk():
        ...

    >>> commands = pip["commands"] # it's a sub package
    >>> commands = Package("pip.commands") # or you can create it from dot notation

    >>> commands.parent == pip # visit parent package
    True
    >>> pip.parent
    None

    >>> print(commands)
    Package(
        name='pip.commands',
        path='./venv/lib/python2.7/site-packages/pip/commands',
        sub_packages=[],
        sub_modules=['check', 'completion', 'download', 'freeze', 'hash', 'help', 'install', 'list', 'search', 'show', 'uninstall', 'wheel'],
    )

    >>> install = commands["install"] # it's a module
    >>> install = Module("pip.commands.install") # or you can create it from dot notation

    # Display package structure
    >>> pip.pprint()
    |-- pip (pip)
        |-- _vendor (pip._vendor)
            |-- cachecontrol (pip._vendor.cachecontrol)
                |-- caches (pip._vendor.cachecontrol.caches)
                    |-- __init__.py (pip._vendor.cachecontrol.caches)
                    |-- file_cache.py (pip._vendor.cachecontrol.caches.file_cache)
                    |-- redis_cache.py (pip._vendor.cachecontrol.caches.redis_cache)
                |-- __init__.py (pip._vendor.cachecontrol)
                |-- _cmd.py (pip._vendor.cachecontrol._cmd)
                |-- adapter.py (pip._vendor.cachecontrol.adapter)
                |-- cache.py (pip._vendor.cachecontrol.cache)
                |-- compat.py (pip._vendor.cachecontrol.compat)
                |-- controller.py (pip._vendor.cachecontrol.controller)
                |-- filewrapper.py (pip._vendor.cachecontrol.filewrapper)
                |-- heuristics.py (pip._vendor.cachecontrol.heuristics)
                |-- serialize.py (pip._vendor.cachecontrol.serialize)
                |-- wrapper.py (pip._vendor.cachecontrol.wrapper)
            |-- colorama (pip._vendor.colorama)
                |-- __init__.py (pip._vendor.colorama)
                |-- ansi.py (pip._vendor.colorama.ansi)
                |-- ansitowin32.py (pip._vendor.colorama.ansitowin32)
                |-- initialise.py (pip._vendor.colorama.initialise)
                |-- win32.py (pip._vendor.colorama.win32)
                |-- winterm.py (pip._vendor.colorama.winterm)
            |-- distlib (pip._vendor.distlib)
                |-- _backport (pip._vendor.distlib._backport)
                    |-- __init__.py (pip._vendor.distlib._backport)
                    |-- misc.py (pip._vendor.distlib._backport.misc)
                    |-- shutil.py (pip._vendor.distlib._backport.shutil)
                    |-- sysconfig.py (pip._vendor.distlib._backport.sysconfig)
                    |-- tarfile.py (pip._vendor.distlib._backport.tarfile)
                |-- __init__.py (pip._vendor.distlib)
                |-- compat.py (pip._vendor.distlib.compat)
                |-- database.py (pip._vendor.distlib.database)
                |-- index.py (pip._vendor.distlib.index)
                |-- locators.py (pip._vendor.distlib.locators)
                |-- manifest.py (pip._vendor.distlib.manifest)
                |-- markers.py (pip._vendor.distlib.markers)
                |-- metadata.py (pip._vendor.distlib.metadata)
                |-- resources.py (pip._vendor.distlib.resources)
                |-- scripts.py (pip._vendor.distlib.scripts)
                |-- util.py (pip._vendor.distlib.util)
                |-- version.py (pip._vendor.distlib.version)
                |-- wheel.py (pip._vendor.distlib.wheel)
            |-- html5lib (pip._vendor.html5lib)
                |-- _trie (pip._vendor.html5lib._trie)
                    |-- __init__.py (pip._vendor.html5lib._trie)
                    |-- _base.py (pip._vendor.html5lib._trie._base)
                    |-- datrie.py (pip._vendor.html5lib._trie.datrie)
                    |-- py.py (pip._vendor.html5lib._trie.py)
                |-- filters (pip._vendor.html5lib.filters)
                    |-- __init__.py (pip._vendor.html5lib.filters)
                    |-- alphabeticalattributes.py (pip._vendor.html5lib.filters.alphabeticalattributes)
                    |-- base.py (pip._vendor.html5lib.filters.base)
                    |-- inject_meta_charset.py (pip._vendor.html5lib.filters.inject_meta_charset)
                    |-- lint.py (pip._vendor.html5lib.filters.lint)
                    |-- optionaltags.py (pip._vendor.html5lib.filters.optionaltags)
                    |-- sanitizer.py (pip._vendor.html5lib.filters.sanitizer)
                    |-- whitespace.py (pip._vendor.html5lib.filters.whitespace)
                |-- treeadapters (pip._vendor.html5lib.treeadapters)
                    |-- __init__.py (pip._vendor.html5lib.treeadapters)
                    |-- genshi.py (pip._vendor.html5lib.treeadapters.genshi)
                    |-- sax.py (pip._vendor.html5lib.treeadapters.sax)
                |-- treebuilders (pip._vendor.html5lib.treebuilders)
                    |-- __init__.py (pip._vendor.html5lib.treebuilders)
                    |-- base.py (pip._vendor.html5lib.treebuilders.base)
                    |-- dom.py (pip._vendor.html5lib.treebuilders.dom)
                    |-- etree.py (pip._vendor.html5lib.treebuilders.etree)
                    |-- etree_lxml.py (pip._vendor.html5lib.treebuilders.etree_lxml)
                |-- treewalkers (pip._vendor.html5lib.treewalkers)
                    |-- __init__.py (pip._vendor.html5lib.treewalkers)
                    |-- base.py (pip._vendor.html5lib.treewalkers.base)
                    |-- dom.py (pip._vendor.html5lib.treewalkers.dom)
                    |-- etree.py (pip._vendor.html5lib.treewalkers.etree)
                    |-- etree_lxml.py (pip._vendor.html5lib.treewalkers.etree_lxml)
                    |-- genshi.py (pip._vendor.html5lib.treewalkers.genshi)
                |-- __init__.py (pip._vendor.html5lib)
                |-- _ihatexml.py (pip._vendor.html5lib._ihatexml)
                |-- _inputstream.py (pip._vendor.html5lib._inputstream)
                |-- _tokenizer.py (pip._vendor.html5lib._tokenizer)
                |-- _utils.py (pip._vendor.html5lib._utils)
                |-- constants.py (pip._vendor.html5lib.constants)
                |-- html5parser.py (pip._vendor.html5lib.html5parser)
                |-- serializer.py (pip._vendor.html5lib.serializer)
            |-- lockfile (pip._vendor.lockfile)
                |-- __init__.py (pip._vendor.lockfile)
                |-- linklockfile.py (pip._vendor.lockfile.linklockfile)
                |-- mkdirlockfile.py (pip._vendor.lockfile.mkdirlockfile)
                |-- pidlockfile.py (pip._vendor.lockfile.pidlockfile)
                |-- sqlitelockfile.py (pip._vendor.lockfile.sqlitelockfile)
                |-- symlinklockfile.py (pip._vendor.lockfile.symlinklockfile)
            |-- packaging (pip._vendor.packaging)
                |-- __init__.py (pip._vendor.packaging)
                |-- __about__.py (pip._vendor.packaging.__about__)
                |-- _compat.py (pip._vendor.packaging._compat)
                |-- _structures.py (pip._vendor.packaging._structures)
                |-- markers.py (pip._vendor.packaging.markers)
                |-- requirements.py (pip._vendor.packaging.requirements)
                |-- specifiers.py (pip._vendor.packaging.specifiers)
                |-- utils.py (pip._vendor.packaging.utils)
                |-- version.py (pip._vendor.packaging.version)
            |-- pkg_resources (pip._vendor.pkg_resources)
                |-- __init__.py (pip._vendor.pkg_resources)
            |-- progress (pip._vendor.progress)
                |-- __init__.py (pip._vendor.progress)
                |-- bar.py (pip._vendor.progress.bar)
                |-- counter.py (pip._vendor.progress.counter)
                |-- helpers.py (pip._vendor.progress.helpers)
                |-- spinner.py (pip._vendor.progress.spinner)
            |-- requests (pip._vendor.requests)
                |-- packages (pip._vendor.requests.packages)
                    |-- chardet (pip._vendor.requests.packages.chardet)
                        |-- __init__.py (pip._vendor.requests.packages.chardet)
                        |-- big5freq.py (pip._vendor.requests.packages.chardet.big5freq)
                        |-- big5prober.py (pip._vendor.requests.packages.chardet.big5prober)
                        |-- chardetect.py (pip._vendor.requests.packages.chardet.chardetect)
                        |-- chardistribution.py (pip._vendor.requests.packages.chardet.chardistribution)
                        |-- charsetgroupprober.py (pip._vendor.requests.packages.chardet.charsetgroupprober)
                        |-- charsetprober.py (pip._vendor.requests.packages.chardet.charsetprober)
                        |-- codingstatemachine.py (pip._vendor.requests.packages.chardet.codingstatemachine)
                        |-- compat.py (pip._vendor.requests.packages.chardet.compat)
                        |-- constants.py (pip._vendor.requests.packages.chardet.constants)
                        |-- cp949prober.py (pip._vendor.requests.packages.chardet.cp949prober)
                        |-- escprober.py (pip._vendor.requests.packages.chardet.escprober)
                        |-- escsm.py (pip._vendor.requests.packages.chardet.escsm)
                        |-- eucjpprober.py (pip._vendor.requests.packages.chardet.eucjpprober)
                        |-- euckrfreq.py (pip._vendor.requests.packages.chardet.euckrfreq)
                        |-- euckrprober.py (pip._vendor.requests.packages.chardet.euckrprober)
                        |-- euctwfreq.py (pip._vendor.requests.packages.chardet.euctwfreq)
                        |-- euctwprober.py (pip._vendor.requests.packages.chardet.euctwprober)
                        |-- gb2312freq.py (pip._vendor.requests.packages.chardet.gb2312freq)
                        |-- gb2312prober.py (pip._vendor.requests.packages.chardet.gb2312prober)
                        |-- hebrewprober.py (pip._vendor.requests.packages.chardet.hebrewprober)
                        |-- jisfreq.py (pip._vendor.requests.packages.chardet.jisfreq)
                        |-- jpcntx.py (pip._vendor.requests.packages.chardet.jpcntx)
                        |-- langbulgarianmodel.py (pip._vendor.requests.packages.chardet.langbulgarianmodel)
                        |-- langcyrillicmodel.py (pip._vendor.requests.packages.chardet.langcyrillicmodel)
                        |-- langgreekmodel.py (pip._vendor.requests.packages.chardet.langgreekmodel)
                        |-- langhebrewmodel.py (pip._vendor.requests.packages.chardet.langhebrewmodel)
                        |-- langhungarianmodel.py (pip._vendor.requests.packages.chardet.langhungarianmodel)
                        |-- langthaimodel.py (pip._vendor.requests.packages.chardet.langthaimodel)
                        |-- latin1prober.py (pip._vendor.requests.packages.chardet.latin1prober)
                        |-- mbcharsetprober.py (pip._vendor.requests.packages.chardet.mbcharsetprober)
                        |-- mbcsgroupprober.py (pip._vendor.requests.packages.chardet.mbcsgroupprober)
                        |-- mbcssm.py (pip._vendor.requests.packages.chardet.mbcssm)
                        |-- sbcharsetprober.py (pip._vendor.requests.packages.chardet.sbcharsetprober)
                        |-- sbcsgroupprober.py (pip._vendor.requests.packages.chardet.sbcsgroupprober)
                        |-- sjisprober.py (pip._vendor.requests.packages.chardet.sjisprober)
                        |-- universaldetector.py (pip._vendor.requests.packages.chardet.universaldetector)
                        |-- utf8prober.py (pip._vendor.requests.packages.chardet.utf8prober)
                    |-- urllib3 (pip._vendor.requests.packages.urllib3)
                        |-- contrib (pip._vendor.requests.packages.urllib3.contrib)
                            |-- __init__.py (pip._vendor.requests.packages.urllib3.contrib)
                            |-- appengine.py (pip._vendor.requests.packages.urllib3.contrib.appengine)
                            |-- ntlmpool.py (pip._vendor.requests.packages.urllib3.contrib.ntlmpool)
                            |-- pyopenssl.py (pip._vendor.requests.packages.urllib3.contrib.pyopenssl)
                            |-- socks.py (pip._vendor.requests.packages.urllib3.contrib.socks)
                        |-- packages (pip._vendor.requests.packages.urllib3.packages)
                            |-- ssl_match_hostname (pip._vendor.requests.packages.urllib3.packages.ssl_match_hostname)
                                |-- __init__.py (pip._vendor.requests.packages.urllib3.packages.ssl_match_hostname)
                                |-- _implementation.py (pip._vendor.requests.packages.urllib3.packages.ssl_match_hostname._implementation)
                            |-- __init__.py (pip._vendor.requests.packages.urllib3.packages)
                            |-- ordered_dict.py (pip._vendor.requests.packages.urllib3.packages.ordered_dict)
                            |-- six.py (pip._vendor.requests.packages.urllib3.packages.six)
                        |-- util (pip._vendor.requests.packages.urllib3.util)
                            |-- __init__.py (pip._vendor.requests.packages.urllib3.util)
                            |-- connection.py (pip._vendor.requests.packages.urllib3.util.connection)
                            |-- request.py (pip._vendor.requests.packages.urllib3.util.request)
                            |-- response.py (pip._vendor.requests.packages.urllib3.util.response)
                            |-- retry.py (pip._vendor.requests.packages.urllib3.util.retry)
                            |-- ssl_.py (pip._vendor.requests.packages.urllib3.util.ssl_)
                            |-- timeout.py (pip._vendor.requests.packages.urllib3.util.timeout)
                            |-- url.py (pip._vendor.requests.packages.urllib3.util.url)
                        |-- __init__.py (pip._vendor.requests.packages.urllib3)
                        |-- _collections.py (pip._vendor.requests.packages.urllib3._collections)
                        |-- connection.py (pip._vendor.requests.packages.urllib3.connection)
                        |-- connectionpool.py (pip._vendor.requests.packages.urllib3.connectionpool)
                        |-- exceptions.py (pip._vendor.requests.packages.urllib3.exceptions)
                        |-- fields.py (pip._vendor.requests.packages.urllib3.fields)
                        |-- filepost.py (pip._vendor.requests.packages.urllib3.filepost)
                        |-- poolmanager.py (pip._vendor.requests.packages.urllib3.poolmanager)
                        |-- request.py (pip._vendor.requests.packages.urllib3.request)
                        |-- response.py (pip._vendor.requests.packages.urllib3.response)
                    |-- __init__.py (pip._vendor.requests.packages)
                |-- __init__.py (pip._vendor.requests)
                |-- adapters.py (pip._vendor.requests.adapters)
                |-- api.py (pip._vendor.requests.api)
                |-- auth.py (pip._vendor.requests.auth)
                |-- certs.py (pip._vendor.requests.certs)
                |-- compat.py (pip._vendor.requests.compat)
                |-- cookies.py (pip._vendor.requests.cookies)
                |-- exceptions.py (pip._vendor.requests.exceptions)
                |-- hooks.py (pip._vendor.requests.hooks)
                |-- models.py (pip._vendor.requests.models)
                |-- sessions.py (pip._vendor.requests.sessions)
                |-- status_codes.py (pip._vendor.requests.status_codes)
                |-- structures.py (pip._vendor.requests.structures)
                |-- utils.py (pip._vendor.requests.utils)
            |-- webencodings (pip._vendor.webencodings)
                |-- __init__.py (pip._vendor.webencodings)
                |-- labels.py (pip._vendor.webencodings.labels)
                |-- mklabels.py (pip._vendor.webencodings.mklabels)
                |-- tests.py (pip._vendor.webencodings.tests)
                |-- x_user_defined.py (pip._vendor.webencodings.x_user_defined)
            |-- __init__.py (pip._vendor)
            |-- appdirs.py (pip._vendor.appdirs)
            |-- distro.py (pip._vendor.distro)
            |-- ipaddress.py (pip._vendor.ipaddress)
            |-- ordereddict.py (pip._vendor.ordereddict)
            |-- pyparsing.py (pip._vendor.pyparsing)
            |-- re-vendor.py (pip._vendor.re-vendor)
            |-- retrying.py (pip._vendor.retrying)
            |-- six.py (pip._vendor.six)
        |-- commands (pip.commands)
            |-- __init__.py (pip.commands)
            |-- check.py (pip.commands.check)
            |-- completion.py (pip.commands.completion)
            |-- download.py (pip.commands.download)
            |-- freeze.py (pip.commands.freeze)
            |-- hash.py (pip.commands.hash)
            |-- help.py (pip.commands.help)
            |-- install.py (pip.commands.install)
            |-- list.py (pip.commands.list)
            |-- search.py (pip.commands.search)
            |-- show.py (pip.commands.show)
            |-- uninstall.py (pip.commands.uninstall)
            |-- wheel.py (pip.commands.wheel)
        |-- compat (pip.compat)
            |-- __init__.py (pip.compat)
            |-- dictconfig.py (pip.compat.dictconfig)
        |-- models (pip.models)
            |-- __init__.py (pip.models)
            |-- index.py (pip.models.index)
        |-- operations (pip.operations)
            |-- __init__.py (pip.operations)
            |-- check.py (pip.operations.check)
            |-- freeze.py (pip.operations.freeze)
        |-- req (pip.req)
            |-- __init__.py (pip.req)
            |-- req_file.py (pip.req.req_file)
            |-- req_install.py (pip.req.req_install)
            |-- req_set.py (pip.req.req_set)
            |-- req_uninstall.py (pip.req.req_uninstall)
        |-- utils (pip.utils)
            |-- __init__.py (pip.utils)
            |-- appdirs.py (pip.utils.appdirs)
            |-- build.py (pip.utils.build)
            |-- deprecation.py (pip.utils.deprecation)
            |-- encoding.py (pip.utils.encoding)
            |-- filesystem.py (pip.utils.filesystem)
            |-- glibc.py (pip.utils.glibc)
            |-- hashes.py (pip.utils.hashes)
            |-- logging.py (pip.utils.logging)
            |-- outdated.py (pip.utils.outdated)
            |-- packaging.py (pip.utils.packaging)
            |-- setuptools_build.py (pip.utils.setuptools_build)
            |-- ui.py (pip.utils.ui)
        |-- vcs (pip.vcs)
            |-- __init__.py (pip.vcs)
            |-- bazaar.py (pip.vcs.bazaar)
            |-- git.py (pip.vcs.git)
            |-- mercurial.py (pip.vcs.mercurial)
            |-- subversion.py (pip.vcs.subversion)
        |-- __init__.py (pip)
        |-- __main__.py (pip.__main__)
        |-- basecommand.py (pip.basecommand)
        |-- baseparser.py (pip.baseparser)
        |-- cmdoptions.py (pip.cmdoptions)
        |-- download.py (pip.download)
        |-- exceptions.py (pip.exceptions)
        |-- index.py (pip.index)
        |-- locations.py (pip.locations)
        |-- pep425tags.py (pip.pep425tags)
        |-- status_codes.py (pip.status_codes)
        |-- wheel.py (pip.wheel)


.. _install:

Install
------------------------------------------------------------------------------

``picage`` is released on PyPI, so all you need is:

.. code-block:: console

    $ pip install picage

To upgrade to latest version:

.. code-block:: console

    $ pip install --upgrade picage
