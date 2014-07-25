#!/usr/bin/python


from storm.locals import *
#try:                        # this ca be eliminated as vim will be available in the namespace that imports this file
#    import vim
#except ImportError:
#    print("vim python module can't be used outside vim editor "
#          "except if you install vimmock python module from PyPI.")


__all__ = ['Keyword', 'Context', 'KeywordContext', 'get_server', 'initialize',
           'load_keywords_store', 'find_keyword', 'create_keyword',
           'update_keyword_info', 'introduction_line']


def __dir__():
    '''This method will be called by dir() and must return the list of
    attributes. This defines the interface of this module.'''
    return __all__


class Keyword(Storm):
    '''This is the model of a keyword.
    Each instance of this class represents a row in the table 'keyword'
    which should exist or be created.
    It must inherit object base class or, for advanced use, Storm.
    All involved classes should inherit Storm too, if you want to define
    references at class definition time, using a stringified version of
    class.property.

    __storm_table__  - table in an SQL database(sqlite, etc.)
    id - is db specific, for indexing
    name - is the keyword itself, like "button", etc; it should be unique in DB
    cmd - will be run to obtain info about the keyword, like reading a man page,
    info - usually an user edited field, this is where the user personalizes
    the definition.

    to learn faster, enable debugging:

        >>> import sys
        >>> from storm.tracer import debug
        >>> debug(True, stream=sys.stdout)
        to disable, do
        >>> debug(False)

        >>> from storm.locals import *
        create or open an existing db
        >>> database = create_database("sqlite:keyword.db")
        On linux, use 'sqlitebrowser' utility to graphically browse the db.
        >>> store = Store(database)
        create the table which will hold instances of Keyword class
        >>> store.execute("CREATE TABLE keyword "
                          "(id INTEGER PRIMARY KEY, name VARCHAR not NULL, cmd VARCHAR, info VARCHAR)")
        define a keyword to add to the table
        >>> keyword1 = Keyword(name=u'canvas')
        >>> keyword1.info = u"Define a canvas section in which you can add Graphics instructions that define how the widget is rendered."
        >>> store.add(keyword1)
        find a keyword with a known name:
        >>> keyword = store.find(Keyword, Keyword.name == u'canvas').one()
        save all stuff
        >>> store.commit()
    '''
    __storm_table__ = "keyword"
    id = Int(primary=True)
    name = Unicode()
    cmd = Unicode()
    info = Unicode()
    # many-to-many relationship, from keyword's point of view
    contexts = ReferenceSet("Keyword.id",
                            "KeywordContext.keyword_id",
                            "KeywordContext.context_id",
                            "Context.id")
    # keywords can have no contexts whatsoever

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    @classmethod
    def create_table(cls, store):
        '''Create the database table according to class properties.'''
        # subclasses that will use this method, will call it with their
        # own __storm_table__
        store.execute("CREATE TABLE IF NOT EXISTS %s (id INTEGER "
                      "PRIMARY KEY, name VARCHAR UNIQUE NOT NULL,"
                      "cmd VARCHAR, info VARCHAR)" % cls.__storm_table__)
        store.commit()

    #def get_all_keywords():
    #    # TODO: get all from table keywords and represent them nicely
    #    pass


class Context(Storm):
    '''Keywords have different definitions depending on the context.
    To create the corresponding DB table, for sqlite:
    >>> store.execute("CREATE TABLE context (id INTEGER PRIMARY KEY, name VARCHAR)")
    '''
    __storm_table__ = "context"
    id = Int(primary=True)
    name = Unicode()
    #description = Unicode()

    # implement many-to-many reference: context has multiple keywords
    # and keywords have multiple contexts. Get all keywords in context:
    keywords = ReferenceSet("Context.id",
                            "KeywordContext.context_id",
                            "KeywordContext.keyword_id",
                            "Keyword.id")

    def __init__(self, name):
        self.name = name

    @classmethod
    def create_table(cls, store):
        '''Context.create_table or Context(u'a_context').create_table'''
        #store.execute("CREATE TABLE IF NOT EXISTS %s (id INTEGER PRIMARY KEY, "
        #              "name VARCHAR UNIQUE NOT NULL, description VARCHAR)" %
        #              cls.__storm_table__)
        store.execute("CREATE TABLE IF NOT EXISTS %s (id INTEGER PRIMARY KEY, "
                      "name VARCHAR UNIQUE NOT NULL)" %
                      cls.__storm_table__)
        store.commit()

    @classmethod
    def find_context(cls, store, name):
        # TODO: you might need to make same abstract class for Keyword & for
        # Content (they might be polimorphic), same methods are used.
        res = store.find(cls, cls.name == name).one()
        return res

    #@classmethod
    #def new_context(cls, store, name,

    # TODO: def get_all():


class KeywordContext(Storm):
    '''Helps in creating a many-to-many relationship.
    To create it in DB use:

        >>> store.execute("CREATE TABLE keyword_context(context_id INTEGER,"
                          "keyword_id INTEGER, PRIMARY KEY (context_id, keyword_id))")

    Notice the syntax for a composed primary key
    '''
    __storm_table__ = "keyword_context"
    # create a composed key
    __storm_primary__ = "context_id", "keyword_id"
    context_id = Int()
    keyword_id = Int()

    @classmethod
    def create_table(cls, store):
        store.execute("CREATE TABLE IF NOT EXISTS %s(context_id INTEGER,"
                      "keyword_id INTEGER, PRIMARY KEY (context_id, "
                      "keyword_id))" % cls.__storm_table__)
        store.commit()


def get_server():
    """Return a server daemon connection or start one """
    # might not be needed anymore
    pass


def initialize(database):
    '''This should be run only once, to create the db, maybe when the script
    is installed. It can populate the db if needed, or the install script
    copy the default db.

    database - check the docs for load_keywords_store function.'''

    store = load_keywords_store(database)
    # create table according to Keyword class:
    store.execute("CREATE TABLE keyword (id INTEGER PRIMARY KEY,"
                  "name VARCHAR not NULL, cmd VARCHAR, info VARCHAR)")
    return store


def load_keywords_store(database):
    '''Creates a connection to the database and loads all keywords.
    Probably, it should first identify the context, and load the keywords
    from that context, not all keywords in db.
    This function should be ran when the plugin is loaded.

    database - a string of the form SCHEME:PATH where:
    scheme - sqlite, postgresql, mysql, etc.
    path - it can be an absolute path.
    eg. '/home/user1/data.db' or 'data.db' for file in current dir.
    '''
    database = create_database(database)
    store = Store(database)
    return store


def find_keyword(store, word):
    '''Searches the database for the word.'''
    # find all matches
    #keywords = store.find(Keyword, Keyword.name == word)

    # return first match
    keyword = store.find(Keyword, Keyword.name == word).one()
    return keyword


def create_keyword(store, word, buf):
    '''Creates a new keyword with name=word and updates the database.
    Workflow:
    with cursor on the word that will become a keyword,
    user calls vim function Helper-create, which opens an empty helper_buffer or
    empties the one already open.
    User edits the buffer with info he wants to store as keyword.info or keyword.cmd
    User saves the contents of the buffer to database by calling HelperSaveCmd or
    HelperSaveInfo which are aliases to HelperSave(flag).
    '''
    keyword = Keyword(name=word)
    keyword = store.add(keyword)
    update_keyword_info(store, keyword, buf)
    return keyword


def update_keyword_info(store, keyword, buf):
    '''Commits to database the contents from helper buffer. Maybe it
    should detect if changes from original exist.
    buf  -> a vim buffer'''
    lines = buf[:]
    buf_content = "\n".join(lines)
    # storm stores content to db as unicode
    buf_content = unicode(buf_content)
    keyword.info = buf_content
    #store.find(Keyword, Keyword.name == keyword.name).set(info=buf_content)
    # write to DB file
    store.commit()
    return keyword


def introduction_line(word):
    '''Constructs a text message.
    It could use an argument to decide which message to return.'''

    msg_no_keyword = '''The keyword "%s" doesn't exist in the database. Would \
you like to add info about it?\nEdit text with \
usual vim commands, but save it to this plugin's database, for future use, \
with :HelperSave.\nIf you don't want to save it, quit with :q!\n\n \
All these lines can be deleted when adding info.''' % word

    return msg_no_keyword
