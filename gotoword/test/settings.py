# -*- coding: utf8 -*-


from standalone.conf import settings
# use call_command to migrate/syncdb right after this app(plugin) is installed
#from django.core.management import call_command


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
