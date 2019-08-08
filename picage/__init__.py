# -*- coding: utf-8 -*-

from ._version import __version__

__short_description__ = "Object style interface for package/module."
__license__ = "MIT"
__author__ = "Sanhe Hu"
__author_email__ = "husanhe@gmail.com"
__maintainer__ = "Sanhe Hu"
__maintainer_email__ = "husanhe@gmail.com"
__github_username__ = "MacHu-GWU"

try:
    from .helpers import SP_DIR, get_sp_dir, is_valid_package_module_name
    from .model import Module, Package
except Exception as e: # pragma: no cover
    pass
