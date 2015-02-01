#!/usr/bin/python

# allow relative imports from modules outside of system path, when this module is
# executed as script:
#if __name__ == '__main__' and __package__ is None:
#    from os import sys, path
#    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from os import sys, path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

import os
import os.path
import shutil
import inspect

import unittest

from storm.locals import *
import storm

### Own libraries ###
#import gotoword
from utils import Keyword, Context, create_keyword, update_keyword
from utils import load_keywords_store
import utils

#from gotoword import *
# TODO: get rid of this; you should do: import gotoword; that's it, like import
# django

# Beware, relative imports don't work when this file is called like:
# $ python test.py

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

DATABASE_PATH = os.path.expanduser("~/.vim/andrei_plugins/gotoword/gotoword/test")


class TestMain(unittest.TestCase):
    def setUp(self):
        self.database_name = 'test.db'
        # remove old test databases
        try:
            os.remove(self.database_name)
        except OSError:
            # file doesn't exist, that's what we want in the first place
            pass

        '''Create a test database.'''
        self.database = create_database("sqlite:" +
                                        os.path.join(DATABASE_PATH,
                                                     self.database_name))
        self.store = Store(self.database)
        # create table according to Keyword class:
        Keyword.create_table(self.store)
        # populate db
        for kword in [u'canvas', u'color', u'test']:
            word = Keyword(name=kword)
            word.info = unicode(keywords[kword])
            self.store.add(word)
            self.store.commit()
        # create some contexts
        Context.create_table(self.store)

    def test_database_is_populated(self):
        query = self.store.execute("SELECT * FROM keyword;")
        # query is a generator-like obj
        self.assertEqual(3, len(query.get_all()))

    def test_keyword_is_unique(self):
        w1 = Keyword(u'unique')
        w1.info = u'this name should be unique in the table.'
        self.store.add(w1)
        self.store.commit()
        w2 = Keyword(u'unique')
        w2.info = u'only when committing the SQL engine can tell that'\
                  'your keyword is not unique'
        self.store.add(w2)
        with self.assertRaises(storm.exceptions.IntegrityError):
            self.store.commit()

    def test_context_is_unique(self):
        c1 = Context(u'python')
        c2 = Context(u'python')
        self.store.add(c1)
        self.store.add(c2)
        with self.assertRaises(storm.exceptions.IntegrityError):
            self.store.commit()

    def test_create_keyword_add_info_from_buffer(self):
        # buf simulates contents retrieved from a vim buffer with buf[:]
        buf = u"""<Rule>:
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

        word = create_keyword(self.store, u'testword', buf)
        self.assertTrue(word.info)

    def test_update_keyword(self):
        kw = Keyword(name=u'test_update_keyword')
        self.store.add(kw)
        self.store.commit()
        buf = ["This is awesome."]     # vim buffer is a list of strings/lines
        kw = update_keyword(self.store, kw, buf)
        # prepare db for visual inspection
        #func_name = inspect.stack()[0][3]
        #self.copy_database_for_inspection(func_name + ".db")

        # expect .find() not to find any "\n"
        self.assertEqual(kw.info.find("\n"), -1)

    def test_find_keyword(self):
        pass

    def tearDown(self):
        self.store.close()
        # copy database resulted after running one test with name:
        #test_name = 'test_create_keyword_add_info_from_buffer'
        #test_name = 'test_update_keyword_info'

        # a TestCase instance will have ._testMethodName() which shows the
        # name of the test case (one/test unit)
        #if self.__dict__['_testMethodName'] == test_name:

        #    self.copy_database_for_inspection(test_name + '.db')
        # get rid of database after every test
        try:
            os.remove(self.database_name)
        except OSError:
            print("there's no such file: %s" % self.database_name)

    def copy_database_for_inspection(self, test_name):
        '''Dump a copy of the database for inspection with other tools.'''
        destination = os.path.join(os.path.dirname(self.database_name),
                                   test_name)
        shutil.copy(self.database_name, destination)


class TestKeyword(unittest.TestCase):
    pass


class TestContext(unittest.TestCase):
    pass


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

    # enable storm debugging, SQL queries are made available
    from storm.tracer import debug
    debug(True, stream=sys.stdout)
    # debug displays all storm queries when you call store.flush() or
    # store.commit()

    database_name = os.path.join(DATABASE_PATH, 'test_at_shell.db')
    # remove any previously created db:
    try:
        os.remove(database_name)
    except OSError as error:
        # Database doesn't exist, so silent the error, raise anything else
        if error.errno != 2:
            raise

    print("create db %s and create variable 'store'" % database_name)

    database = 'sqlite:' + database_name
    store = load_keywords_store(database)

    print("create table %s" % Keyword.__storm_table__)
    store.execute("CREATE TABLE IF NOT EXISTS keyword (id INTEGER PRIMARY KEY,"
                  "name VARCHAR not NULL, cmd VARCHAR, info VARCHAR)")

    words = [u'canvas', u'color', u'test']
    print("Populate db with words: %s" % " ".join(words))
    for kword in words:
        word = Keyword(name=kword)
        word.info = unicode(keywords[kword])
        store.add(word)
        store.commit()

    print("Retrieve keywords from DB and store them in variables.")
    canvas = store.find(Keyword, Keyword.name == u'canvas').one()
    color = store.find(Keyword, Keyword.name == u'color').one()
    test = store.find(Keyword, Keyword.name == u'test').one()
    # each word has one or more contexts, just like in real life
    print("Create table %s" % Context.__storm_table__)
    Context.create_table(store)
    # create table used for many-to-many relationships
    print("Create table %s" % utils.KeywordContext.__storm_table__)
    utils.KeywordContext.create_table(store)
    store.commit()

    kivy = Context(name=u'kivy')
    python = Context(name=u'python')
    store.add(kivy)
    store.add(python)
    #kivy = store.find(Context, Context.name == u'kivy').one()
    #python = store.find(Context, Context.name == u'python').one()

    # word belongs to 2 contexts:
    canvas.contexts.add(kivy)
    canvas.contexts.add(python)
    color.contexts.add(kivy)
    store.commit()

    print("list all contexts the keyword %s belongs to:" % canvas)
    contexts_generator = canvas.contexts.values(Context.name)
    for context in contexts_generator:
        print(context)

    print("list all keywords the context %s has: " % kivy)
    words_generator = kivy.keywords.values(Keyword.name)
    for word in words_generator:
        print(word)

    print("user at shell is required to call store.close() at the end.")
