import sys
import os
from os.path import dirname, abspath


def djangopath(up=1, settings=None):
    """convenience function to easily set the application sys.path and
       DJANGO_SETTINGS_MODULE environment variable depending on the location
       of the script file in question.

    :param up: how many directories up from current __file__ where the
               djangopath function is called.
    :type up: integer
    :param settings: <djangoapp>.settings
    :type: settings: string

    usage::

        >>> import setSettings
        >>> djangopath(up=3, settings='myapp.settings')

    """
    # here's the magic
    path = abspath(sys._getframe(1).f_code.co_filename)
    for i in range(up):
        path = dirname(path)
    sys.path.insert(0, path)
    if settings:
        os.environ['DJANGO_SETTINGS_MODULE'] = settings
