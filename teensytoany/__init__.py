"""Top-level package for Python TeensyToAny."""

__author__ = 'Ramona Optics'
__email__ = 'info@ramonaoptics.com'
from .teensytoany import TeensyToAny

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

__all__ = ['TeensyToAny', ]
