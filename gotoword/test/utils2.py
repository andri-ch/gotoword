# -*- coding: utf8 -*-


from standalone import models
# Read more about models:
# https://docs.djangoproject.com/en/1.7/topics/db/models/


class Context(models.StandaloneModel):
    """Keywords have different definitions depending on the context.
    Eg.:
    kivy = Context.objects.create(name="kivy GUI", description="Kivy is an " +
             "OSS library for GUI development suitable for multi-touch apps.")
    """
    name = models.CharField("context name", max_length=50, unique=True)
    description = models.CharField("short description of context",
                                   max_length=100)

    def __unicode__(self):
        return self.name


class Keyword(models.StandaloneModel):
    """
    name - is the keyword itself, like "button", etc; it should be unique
        in DB
    cmd - will be run to obtain info about the keyword, like reading a man
        page,
    info_public - note that exists publicly on the internet and people
        agreed on it
    info - usually an user edited field, this is where the user personalizes
        the definition or adds his own.
    Eg.:
        canvas = Keyword.objects.create(name="canvas")
    """
    name = models.CharField("keyword name", max_length=50, unique=True)
    contexts = models.ManyToManyField(Context, through='Data')
    # this is the source model, it has the ManyToManyField

    #col2 = models.ForeignKey("standalone.MyModel")

    def __unicode__(self):
        "useful when calling print() on a class instance."
        return self.name


class Data(models.StandaloneModel):
    """
    This is the intermediary model for a ManyToMany relationship that shows
    how Keyword is related to Context.
    To create ManyToMany relationships, you need to use this model.
    1. Create a Context and a Keyword:
    Context is the target model of the ManyToManyField from Keyword model;
    Keyword is the source model of the ManyToManyField.
    2. Create the relationship
    >>> r1 = Data(keyword=canvas, context=kivy)
    >>> r1.save()
    # it is possible to let the other kwargs empty when creating a new Data
    # object and add them later on
    >>> r1.info_public = "http://kivy.org/docs/api-kivy.graphics.html#" +
                         "kivy.graphics.Canvas"
    >>> r1.info = "Define a canvas section in which you can add Graphics " +
    ...           "instructions that define how the widget is rendered."
    >>> r1.save()

    info_public(keyword, context)
    info(keyword, context)
    cmd(keyword, context)
    """
    keyword = models.ForeignKey(Keyword)
    context = models.ForeignKey(Context)
    cmd = models.CharField("cmd to run to obtain info", max_length=100)
    info_public = models.TextField("info note publicly available")
    info = models.TextField("note with user's own data")

    def __unicode__(self):
        return self.keyword.name + self.context.name


def initialize(database):
    '''This should be run only once, to create the db, maybe when the script
    is installed. It can populate the db if needed, or the install script
    copy the default db.

    database - check the docs for load_keywords_store function.'''
    pass


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
    pass


def find_keyword(word, store=None):
    '''Searches the database for the word.
    store - any model class, like Keyword, Context, etc.
    word - any string
    Eg.:
        find_keyword(Keyword, "canvas")
    '''
    keyword = Keyword.objects.filter(name=word)
    return keyword


#    Workflow:
#    with cursor on the word that will become a keyword,
#    user calls vim function Helper, which opens an empty helper_buffer or
#    empties the one already open.
#    User edits the buffer with info he wants to store as keyword.info or keyword.cmd
#    User saves the contents of the buffer to database by calling HelperSave vim cmd or
#    HelperSaveInfo which are aliases to HelperSave(flag).
#    '''
#    #if not hasattr(word, "name"):
#    #    keyword = Keyword(name=word)

def create_keyword(word, context, buf, store=None):
    '''Creates a new keyword with name=word and adds contents from vim buffer
    as information for the keyword and updates the database.
    Returns the keyword.
    '''

    keyword = Keyword.objects.create(name=word)
    if not context:
        # use the default context
        context = Context.objects.get(name="default")
    # create the ManyToMany relationship
    r1 = Data(keyword=keyword, context=context)
    r1.save()
    #r1.info_public = "http://kivy.org/docs/api-kivy.graphics.html#kivy.graphics.Canvas"
    #r1.info = ("Define a canvas section in which you can add Graphics "
    #           "instructions that define how the widget is rendered.")
    #r1.save()
    buf_content = read_vim_buffer(buf, 0)
    update_info(keyword, buf_content, store)
    return keyword


# TODO: unit tests for all these functions
def update_keyword(keyword, buf, store=None):
    '''Reads contents from vim buffer except for the title line and updates
    the keyword's info (personal note), not info_public.
    '''
    buf_content = read_vim_buffer(buf, 1)
    update_info(keyword, buf_content, store)
    #store.find(Keyword, Keyword.name == keyword.name).set(info=buf_content)
    # write to DB file
    return keyword


def read_vim_buffer(buf, start_line):
    '''Reads vim buffer as a list of strings and joins them into one string.
    Returns the string.'''
    lines = buf[start_line:]
    buf_content = "\n".join(lines)
    return buf_content


def update_info(keyword, context, content):
    'Updates the keyword information and commits to database.'
    data = keyword.data_set.get(context=context)
    data.info = content
    data.save()
    # maybe content replaced with info, and info_public added


def introduction_line(word):
    '''Constructs a text message.
    It could use an argument to decide which message to return.'''

    msg_no_keyword = '''The keyword "%s" doesn't exist in the database. Would \
you like to add info about it?\nEdit text with \
usual vim commands, but save it to this plugin's database, for future use, \
with :HelperSave.\nIf you don't want to save it, quit with :q!\n\n \
All these lines can be deleted when adding info.''' % word

    return msg_no_keyword


def create_vim_list(values):
    """creates the Vim editor's equivalent of python's repr(a_list).

        >>> create_vim_list(['first line', 'second line'])
        '["first line", "second line"]'

    values - a list of strings
    We need double quotes not single quotes to create a Vim list.
    Returns a string that is a properly written Vim list of strings.
    This result can be fed to vim's eval function to create a list in vim.
    """

    values_with_quotes = ('"' + elem + '"' for elem in values)
    return '[%s]' % ', '.join(values_with_quotes)
    # as a one liner:
    #return '[%s]' % ', '.join("\"%s\"" % elem for elem in values)
