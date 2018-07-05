"""
A module that implements tooling to enable easy warnings about deprecations.
"""
from __future__ import absolute_import

import logging
import warnings

from pip._internal.utils.typing import MYPY_CHECK_RUNNING

if MYPY_CHECK_RUNNING:
    from typing import Any, Optional  # noqa: F401


class PipDeprecationWarning(Warning):
    pass


class PipPendingDeprecationWarning(PipDeprecationWarning):
    pass


_original_showwarning = None  # type: Any


# Warnings <-> Logging Integration
def _showwarning(message, category, filename, lineno, file=None, line=None):
    if file is not None:
        if _original_showwarning is not None:
            _original_showwarning(
                message, category, filename, lineno, file, line,
            )
    elif issubclass(category, PipDeprecationWarning):
        # We use a specially named logger which will handle all of the
        # deprecation messages for pip.
        logger = logging.getLogger("pip._internal.deprecations")

        # PipPendingDeprecationWarnings still have at least 2
        # versions to go until they are removed so they can just be
        # warnings.  Otherwise, they will be removed in the very next
        # version of pip. We want these to be more obvious so we use the
        # ERROR logging level.
        if issubclass(category, PipPendingDeprecationWarning):
            logger.warning(log_message)
        else:
            logger.error(log_message)
    else:
        _original_showwarning(
            message, category, filename, lineno, file, line,
        )


def install_warning_logger():
    # Enable our Deprecation Warnings
    warnings.simplefilter("default", PipDeprecationWarning, append=True)

    global _original_showwarning

    if _original_showwarning is None:
        _original_showwarning = warnings.showwarning
        warnings.showwarning = _showwarning


def deprecated(reason, replacement, issue=None, imminent=False):
    # type: (str, Optional[str], Optional[int], bool) -> None
    if imminent:
        category = PipDeprecationWarning
    else:
        category = PipPendingDeprecationWarning

    # Construct a nice message.
    # This is purposely eagerly formatted as we want it to appear as if someone
    # typed this entire message out.
    message = "DEPRECATION: " + reason
    if replacement is not None:
        message += " An alternative is to {}.".format(replacement)
    if issue is not None:
        url = "https://github.com/pypa/pip/issues/" + str(issue)
        message += " You can find discussion regarding this at {}.".format(url)

    warnings.warn(message, category=category, stacklevel=2)
