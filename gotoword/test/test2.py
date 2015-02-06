#!/home/andrei/.vim/andrei_plugins/gotoword/virtualenv/bin/python
# -*- coding: utf8 -*-

from os import sys, path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
import os
import os.path
import shutil
import inspect

import unittest

### Own libraries ###
#import gotoword
#from utils import create_keyword, update_keyword
#from utils import load_keywords_store
database_name = 'test.db'
from settings import setup
setup(db=database_name)

import django
#from standalone.conf import settings
from django.core.management import call_command


# parse command line to get the database and whether we want to
# create the database.
#from optparse import OptionParser
#
#
#parser = OptionParser("usage: %prog -d DATABASE [-s]|[-r]")
#parser.add_option('-d', '--database', dest='database', help="DATABASE file name", metavar="DATABASE")
#parser.add_option('-s', '--syncdb', dest='syncdb', action="store_true", help="should the database be created?")
#parser.add_option('-r', '--repl', dest='repl', action="store_true", help="start a REPL with access to your models")

#options, args = parser.parse_args()

#if not options.database:
#    parser.error("You must specify the database name")
#
#database_name = 'test.db'
## fetch the settings and cache them for later use
#settings = settings(
#    DATABASES={
#        'default': {
#            'ENGINE': 'django.db.backends.sqlite3',
#            #'NAME': 'db.sqlite3',
#            #'NAME': options.database,
#            'NAME': database_name,
#        },
#    },
#    MIDDLEWARE_CLASSES=(
#        'django.middleware.common.CommonMiddleware',
#    ),
#)

##### Andrei stuff
# for standalone scripts:
# according to http://django.readthedocs.org/en/latest/releases/1.7.html#standalone-scripts
# you need to use this after settings.configure() which is done by settings()
# above
#import django
#django.setup()
#####

from utils2 import Keyword, Context, Data

#DATABASE_PATH = path.dirname(path.abspath(__file__)


keywords = {'canvas': "Define a canvas section in which you can add Graphics instructions that define how the widget is rendered.",
            'color': '''Color is a canvas context instruction. Instruction to set the color state for any vertices being drawn after it. All the values passed are between 0 and 1, not 0 and 255.In kv lang:

<Rule>:
    canvas:
        # red color
        Color:
            rgb: 1, 0, 0
        # blue color
        Color:
            rgb: 0, 1, 0
        # blue color with 50% alpha
        Color:
            rgba: 0, 1, 0, .5

        # using hsv mode
        Color:
            hsv: 0, 1, 1

        # using hsv mode + alpha
        Color:
            hsv: 0, 1, 1
            a: .5''',
            'test': "This is awesome"
            }

contexts = {'kivy GUI': ("Kivy is an OSS library for GUI "
                         "development suitable for multi-touch apps."),
            'python': "programming langugage",
            'django': "web framework",
            }


class TestMain(unittest.TestCase):
    database_name = database_name

    @classmethod
    def setUpClass(cls):
        # remove old test databases
        try:
            os.remove(database_name)
        except OSError:
            # file doesn't exist, that's what we want in the first place
            pass
        '''Create a test database.'''
        call_command('syncdb')

    def setUp(self):
        # populate db
        for kword in keywords:
            Keyword.objects.create(name=kword)
            # .create() automatically saves to DB

        # create some contexts
        for c in contexts:
            Context.objects.create(name=c, description=contexts[c])

    def tearDown(self):
        # copy database resulted after running one test with name:
        #test_name = 'test_create_keyword_add_info_from_buffer'
        #test_name = 'test_update_keyword_info'
        #test_name = 'test_context_is_unique'
        #test_name = 'test_keyword_is_unique'

        ## a TestCase instance will have ._testMethodName() which shows the
        ## name of the test case (one/test unit)
        #if self.__dict__['_testMethodName'] == test_name:
        #    self.copy_database_for_inspection(test_name + '.db')

        Keyword.objects.all().delete()
        Context.objects.all().delete()
        Data.objects.all().delete()
        pass
        #self.store.close()

        # get rid of database after every test
        #try:
        #    os.remove(self.database_name)
        #except OSError:
        #    print("there's no such file: %s" % self.database_name)

    def test_database_is_populated(self):
        l = Keyword.objects.all()
        # query is a generator-like obj
        self.assertEqual(len(keywords.keys()), len(l))

    #@unittest.skip("")
    def test_keyword_is_unique(self):
        Keyword.objects.create(name='unique')
        '''only when committing the SQL engine can tell that
        your keyword is not unique'''
        with self.assertRaises(django.db.IntegrityError):
            Keyword.objects.create(name='unique')

    @unittest.skip("")
    def test_context_is_unique(self):
        Context.objects.create(name='python')
        with self.assertRaises(django.db.IntegrityError):
            Context.objects.create(name='python')
        # although the right exception is raised, unittest takes this as a
        # failed test

    def test_create_keyword_add_info_from_buffer(self):
        # buf simulates contents retrieved from a vim buffer with buf[:]
        buf = """<Rule>:
        canvas:
        # red color
        Color:
            rgb: 1, 0, 0
        # blue color
        Color:
            rgb: 0, 1, 0
        # blue color with 50% alpha
        Color:
            rgba: 0, 1, 0, .5

        # using hsv mode
        Color:
            hsv: 0, 1, 1

        # using hsv mode + alpha
        Color:""".splitlines()

        testword = Keyword.objects.create(name='testword')
        kivy = Context.objects.get(name='kivy GUI')
        testword_kivy = Data(keyword=testword, context=kivy)
        testword_kivy.info = "my note about testword in kivy context"
        testword_kivy.save()
        #word = create_keyword(self.store, u'testword', buf)
        # create_keyword(Keyword, 'testword', buf)
        data = testword.data_set.get(context=kivy)
        # or data = Data.objects.get(keyword=testword, context=kivy)
        self.assertTrue(data.info)

    def test_update_keyword(self):
        kw = Keyword.objects.create(name='test_update_keyword')
        kivy = Context.objects.get(name='kivy GUI')
        kw_kivy = Data(keyword=kw, context=kivy)
        kw_kivy.info = "my note about testword in kivy context"
        kw_kivy.save()

        buf = ["This is awesome. Info is updated."]     # vim buffer is a list of strings/lines
        #kw = update_keyword(self.store, kw, buf)
        kw.info = "\n".join(buf)

        # prepare db for visual inspection
        #func_name = inspect.stack()[0][3]
        #self.copy_database_for_inspection(func_name + ".db")

        # expect .find() not to find any "\n"
        self.assertEqual(kw.info.find("is"), 2)

    def test_find_keyword(self):
        kw = Keyword.objects.filter(name="canvas")
        self.assertEqual(u'canvas', kw.values()[0]['name'])

    def copy_database_for_inspection(self, test_name):
        '''Dump a copy of the database for inspection with other tools.'''
        destination = os.path.join(os.path.dirname(self.database_name),
                                   test_name)
        shutil.copy(self.database_name, destination)


class TestKeyword(unittest.TestCase):
    pass


class TestContext(unittest.TestCase):
    pass



#if options.syncdb:
#    # run a simple command - here syncdb - from the management suite
#    call_command('syncdb')
#elif options.repl:
#    # start the shell, access to your models through import standalone.models
#    call_command('shell')


# run all tests:
if __name__ == '__main__':          # when running as a script
    # test all functions
    import doctest
    doctest.testmod()

    print("Running tests...")
    ### load and run tests from other files ###
    #loader = unittest.defaultTestLoader
    #suite = loader.loadTestsFromName('utils.TestConfigValidate')
    #print(suite.countTestCases())
    #runner = unittest.TextTestRunner(verbosity=1)
    #runner.run(suite)

    ### run tests from this file ###
    unittest.main(verbosity=2)
    print("Done!")
else:                                # when it is being imported
    # Realtime initialization, useful in a shell when this file is imported
    # in ipython, for example;
    # type, call 'run -n' to import file like a normal python
    # module, to prevent the filename to change to '__main__':
    # >>> run -n <path_to_this_file>

    #database_name = os.path.join(DATABASE_PATH, 'test_at_shell.db')
    # remove any previously created db:
    try:
        os.remove(database_name)
    except OSError as error:
        # Database doesn't exist, so silent the error, raise anything else
        if error.errno != 2:
            raise

    print("create db %s" % database_name)
    call_command('syncdb')

    kivy = Context.objects.create(
        name="kivy GUI", description="Kivy is an OSS library for GUI " +
        "development suitable for multi-touch apps.")
    canvas = Keyword.objects.create(name="canvas")

    # create the ManyToMany relationship
    r1 = Data(keyword=canvas, context=kivy)
    r1.save()
    # it is possible to let the other kwargs empty when creating a new Data
    # object and add them later on
    r1.info_public = "http://kivy.org/docs/api-kivy.graphics.html#kivy.graphics.Canvas"
    r1.info = ("Define a canvas section in which you can add Graphics "
               "instructions that define how the widget is rendered.")
    r1.save()

    python = Context(name="python", description="programming langugage")
    python.save()
    django_ctx = Context.objects.create(name="django", description="web framework")

    color = Keyword.objects.create(name="color")
    # add definition of color in kivy context:
    color_kivy = Data(keyword=color, context=kivy)
    color_kivy.info_public = keywords['color']
    color_kivy.save()

    # get all keywords that have a definition in kivy context:
    words = kivy.keyword_set.all()
    # get all contexts in which canvas has a definition:
    canvas_contexts = canvas.contexts.all()

    # add definition of canvas in python context:
    canvas_python = Data(keyword=canvas, context=python)
    canvas_python.info = ("canvas doesn't mean anything in python, but it's "
                          "good as a test definition")
    canvas_python.save()

    test = Keyword.objects.create(name="test")

    # add the default (primary) context
#    default_context = Context.objects.create(
#        name="default", description="Context used for keywords that have " +
#        "only one definition, no matter the context. By default, unless " +
#        "specified, all keywords will have the first definition assigned " +
#        "to this context.")
    default_context = Context.objects.create(
        name="default", description="Context used by default for the main " +
        "definition of a word.")
    test_default_context = Data(keyword=test, context=default_context)
    test_default_context.info = "test info"
    test_default_context.save()

    # delete test keyword and its Data relationship
    test.delete()

    # select only the keyword names
    all_keywords = [kwd.name for kwd in Keyword.objects.all()]

    # Display all keywords that have a definition belonging to "kivy" context:
    context_kwds = [kwd.name for kwd in kivy.keyword_set.all()]

