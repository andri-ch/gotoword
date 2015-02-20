# -*- coding: utf8 -*-

import sys
import os.path
import glob

# NOTICE
# the python path when these lines are executed is the path of the currently
# active buffer (vim.current.buffer)
# So, to import our own libs, we have to add them to python path.
CONF = {
    'PLUGIN_NAME': 'gotoword',
    # get the path to this python package
    'PKG_PATH': os.path.abspath(os.path.dirname(__file__))
}
'''
>>> print(pkg_path)
'/home/andrei/.vim/plugins/gotoword/gotoword'
'''
# get the root dir of this plugin:
VIM_PLUGIN_PATH = os.path.dirname(PKG_PATH)
SCRIPT = os.path.join(VIM_PLUGIN_PATH, 'gotoword.vim')
HELP_BUFFER = os.path.join(VIM_PLUGIN_PATH, 'gotoword_buffer')

# get a glob specific to the python version installed in the virtualenv
virtualenv_packages = os.path.join(VIM_PLUGIN_PATH,
                                   'virtualenv/lib/python*/site-packages/')

DJANGO_PATH = glob.glob(virtualenv_packages)[0]

#sys.path.insert(1, VIM_PLUGIN_PATH)
sys.path.insert(2, DJANGO_PATH)

# load django-standalone (can find it on PyPI)
from standalone.conf import settings
# use call_command to migrate/syncdb right after this app(plugin) is installed
#from django.core.management import call_command

#logger.debug("sys.path: %s" % sys.path, extra={'className': ""})
# plugin's database that holds all the keywords and their info:
DATABASE = os.path.join(VIM_PLUGIN_PATH, 'keywords.db')


def setup(db='test.db', engine='django.db.backends.sqlite3'):
    """Calls django's settings() which must be called only once per project."""
    # fetch the settings and cache them for later use
    init_settings = settings(
        DATABASES={
            'default': {
                'ENGINE': engine,
                'NAME': db,
            },
        },
        MIDDLEWARE_CLASSES=(
            'django.middleware.common.CommonMiddleware',
        ),
    )

    #####
    # for standalone scripts:
    # according to http://django.readthedocs.org/en/latest/releases/1.7.html#standalone-scripts
    # you need to use this after settings.configure() which is done by settings()
    # above
    import django
    django.setup()

    return init_settings
    #####

# MAIN
#setup(DATABASE)
