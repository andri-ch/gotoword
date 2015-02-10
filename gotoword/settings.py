# -*- coding: utf8 -*-

import os.path
#import sys
#print(sys.path)
#try:
#    from standalone.conf import settings
#except ImportError:
#    pass
from standalone.conf import settings
#try:
#    import standalone.conf
#except ImportError:
#    sys.exit()
# use call_command to migrate/syncdb right after this app(plugin) is installed
#from django.core.management import call_command

# Get rid of so many variables
VIM_FOLDER = os.path.expanduser('~/.vim')
PLUGINS_FOLDER = 'andrei_plugins'
# PLUGINS_FOLDER can be any of "plugin", "autoload", etc.

# TODO: decide in which plugin folder is more appropriate to install this
# plugin and you might get rid of all these constants or put them in a dict

PLUGIN_NAME = 'gotoword'
PYTHON_PACKAGE = 'gotoword'

PLUGIN_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(PLUGIN_PATH, 'gotoword.vim')

### Own libraries ###
# NOTICE
# the python path when these lines are executed is the path of the currently
# active buffer (vim.current.buffer)
# So, to import our own libs, we have to add them to python path.
SOURCE_DIR = os.path.join(VIM_FOLDER, PLUGINS_FOLDER, PLUGIN_NAME,
                          PYTHON_PACKAGE)
#sys.path.insert(1, SOURCE_DIR)
# Eg. '/home/username/.vim/a_plugins_dir/gotoword/gotoword'
#sys.path.insert(2, os.path.join(PLUGIN_PATH, 'virtualenv', 'lib', 'python2.7'))
#sys.path.insert(3, os.path.join(PLUGIN_PATH, 'virtualenv', 'lib', 'python2.7',
                #'site-packages'))
#import imp
#fp, pathname, description = imp.find_module('conf', [os.path.join(PLUGIN_PATH,
#    'virtualenv', 'lib', 'python2.7', 'site-packages')])
#fp, pathname, description = imp.find_module('conf',
#        ['/home/andrei/.vim/andrei_plugins/gotoword/virtualenv/lib/python2.7/site-packages'])
#try:
#    conf = imp.load_module('conf', fp, pathname, description)
#finally:
#    # Since we may exit via an exception, close fp explicitly.
#    if fp:
#        fp.close()


#def custom_importer(name, pathname):
#    # Fast path: see if the module has already been imported.
#    try:
#        return sys.modules[name]
#    except KeyError:
#        pass
#
#    # If any of the following calls raises an exception,
#    # there's a problem we can't handle -- let the caller handle it.
#
#    fp, pathname, description = imp.find_module(name)
#
#    try:
#        return imp.load_module(name, fp, pathname, description)
#    finally:
#        # Since we may exit via an exception, close fp explicitly.
#        if fp:
#            fp.close()

#standalone = custom_importer('standalone', '/home/andrei/.vim/andrei_plugins/gotoword/virtualenv/lib/python2.7/site-packages')
#conf = custom_importer('conf', standalone.__path__)
#
#logger.debug("sys.path: %s" % sys.path, extra={'className': ""})
# plugin's database that holds all the keywords and their info:
DATABASE = os.path.join(PLUGIN_PATH, 'keywords.db')


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

    ##### Andrei stuff
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
