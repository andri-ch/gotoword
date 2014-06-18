### System libraries ###
import os.path
import sys

### Third party libs ###
from storm.locals import create_database, Store, Int, Unicode


VIM_FOLDER = os.path.expanduser('~/.vim')
# os.path.expanduser turns '~' into an absolute path, because os.path.abspath can't!
PLUGINS_FOLDER = 'andrei_plugins'
# PLUGINS_FOLDER can be any of "plugin", "autoload", etc.
PLUGIN_NAME = 'gotoword'
PYTHON_PACKAGE = 'gotoword'
# plugin's database that holds all the keywords and their info
DB_NAME = 'keywords.db'
DATABASE = os.path.join(VIM_FOLDER, PLUGINS_FOLDER, PLUGIN_NAME, DB_NAME)

### Own libraries ###
# NOTICE
# the python path when these lines are executed is the path of the currently
# active buffer (vim.current.buffer) in which this code is executed
# So, to import our own libs, we have to add them to python path.
sys.path.insert(1, os.path.join(VIM_FOLDER, PLUGINS_FOLDER, PLUGIN_NAME, PYTHON_PACKAGE))
# Eg. '/home/username/.vim/a_plugins_dir/gotoword/gotoword'
import utils               # should be replaced by import utils
import gotoword_state_machine

### import special vim python library  ###
try:
    import vim
    # the vim module contains everything we need to interface with vim from
    # python, but only when python is used in vim plugins.
    # can't import vim in ipython, maybe with some tricks or by using vimmock PyPI module
except ImportError:
    # just for testing purposes
    print("vim python module can't be used outside vim editor "
          "except if you install vimmock python module from PyPI.")
    try:
        import vimmock
        vimmock.patch_vim()
    except ImportError:
        print("you need to install vimmock if you want to import vim \n"
              "python module outside of the vim environment: \n"
              "sudo pip install vimmock")
        sys.exit()

    # now we can import a mockup of vim
    import vim
    # more patching because vimmock implements a minimal vim functionality
    mock_buf = vim.current.buffer
    # define attribute at runtime
    mock_buf.name = os.path.join(VIM_FOLDER, PLUGINS_FOLDER, PLUGIN_NAME, "helper_buffer")
    mock_win = vim.current.window
    mock_win.buffer = mock_buf
    # mimic vim commands like "exe 'set noro'"
    vim.command = lambda x: ""

    class mylist(list):
        """
        Mock up a list that always return the first element, the element
        we want, no matter the key.
        """
        def __init__(self, arg=None):
            if type(arg) is not list:
                raise TypeError
            super(list, self).__init__(arg)
            self.li = arg

        def __getitem__(self, key):
            "implements self[key] functionality."
            return self.li[0]

        def __iter__(self):
            "used by enumerate() or for loop, etc."
            return self.li.__iter__()

    vim.buffers = mylist([mock_buf])        # emulate a list of buffers
    vim.windows = [mock_win]


### MAIN ###

database = utils.create_database('sqlite:' + DATABASE)
# Eg: DATABASE = 'sqlite:/home/andrei/.vim/andrei_plugins/gotoword/keywords.db'
store = Store(database)
# store is a cursor to database wrapped by storm

help_window = None
# create a help_buffer that will hold info retrieved from database, etc. but
# prevent vim to create buffer in current working dir, by setting an explicit
# path; this way, python imports from our own library are easier
help_buffer_name = os.path.join(VIM_FOLDER, PLUGINS_FOLDER, PLUGIN_NAME, "helper_buffer")
# help_buffer is created on the fly, it doesn't exist on disk, but we
# specify a full path as its name
# TODO: rename helper_buffer to gotoword_buffer

# find and store the help window's index for further reference to it
# if the user needs help on other words, you just change the window buffer
# or, update the current buffer, so help_window might not be needed
for win in vim.windows:
    if win.buffer.name == help_buffer_name:
        # if already there is a window which displays the help buffer
        help_window = win
        #win.buffer.append("Help window: %s" % help_window)

if not help_window:
    try:
    # open the andrei_help buffer in a new window
    #vim.command("exe 'silent new' escape('%s', '\ ')" % help_buffer_name)
    #vim.command("exe 'silent new' escape('%s', '\ ')" % help_buffer_name)
        # opens file in same win
        vim.command("exe 'split %s'" % help_buffer_name)
        #vim.command("exe 'set readonly'")                   # or 'set ro'
        # by setting buffer readonly, we want user to prevent from saving it
        # on harddisk with :w cmd, instead we want user to update the
        # database with HelperUpdate vim cmd or HelperSave
    except vim.error:
        print("can't create %s buffer, it already exists." % help_buffer_name)

"""
map buffer names to vim.buffers indices for easier access from python
(indices differ when compared to vim buffers' indices, but the name is the
same, so we need to access buffers by name)
"""
py_buffers = {}
for index, b in enumerate(vim.buffers):
    py_buffers[b.name] = index + 1
    # vim indexing starts from 1, but index starts from 0
    # >>> print(py_buffers)
    #{'/home/andrei/.vim/andrei_plugins/andrei_helper': 1, '/home/andrei/bash_exp/-MiniBufExplorer-': 2, '/home/andrei/bash_exp/sugarsync.kv': 0}
help_buffer = vim.buffers[py_buffers[help_buffer_name]]


def update_help_buffer(word):
    # reopen database connection
    store._connection = store.get_database().connect()
    # make it unicode, for python2.x, this is what is stored in the db
    word = unicode(word)
    # make it case-insensitive
    word = word.lower()
    # look for keyword in DB
    keyword = utils.find_keyword(store, word)

    if keyword:
        # load content in buffer, previous content is deleted
        help_buffer[:] = keyword.info.splitlines()
        vim.command("exe 'set readonly'")                   # or 'set ro'
    else:
        # keyword doesn't exist, prepare buffer to be filled with user content
        vim.command("exe 'set noreadonly'")                 # or 'set noro'
        # write to buffer the small help text
        help_buffer[:] = utils.introduction_line(word).splitlines()
        vim.command("exe 'set readonly'")                   # or 'set ro'
        # .splitlines() is used because vim buffer accepts at most one "\n"
        # per vim line

    ### DEBUG ###
    #help_buffer.append("%s" % help_buffer)
    ###

    # close database connection
    store.close()
    return keyword


def helper_save(context):
    """
    this function, if called twice on same keyword(first edit, then an update)
    should know that it doesn't need to create another keyword, just to update
    """
    # reopen database connection
    store._connection = store.get_database().connect()

    # initialize state machine to handle case 00

    #m = gotoword_state_machine.StateMachine()
    #m.add_state("Start", start_transitions)
    #m.add_state("read_context_state", read_context_transitions)
    #m.add_state("end_state", end_state, end_state=1)
    gotoword_state_machine.m.set_start("Start")
    #m.run('start')

    ### debug ###
    if not context:
        print("context is empty")
        gotoword_state_machine.m.run('start')
    else:
        print("context is %s" % context)

    #if context:
    #    # context was specified by the user, so look it up in DB
    #    ctx = Context.find_context(context)
    #    # if context not in DB, ctx will be None, create a new context
    #    if !ctx:
    #        context = Context(name=context)
    #else:
    #    pass

    ### ALL COMBINATIONS ###
    # from the user's point of view - what he types when he executes :HelperSave [context]
    # [context] is optional

    # keyword doesn't exist, context doesn't exist                                             0 0
        # Do you want to specify a context?
            # abort [a]
            # yes -> create keyword with context   1
            # no -> create keyword with no context 0


    # keyword doesn't exist, context exists                                                    0 1
        # context exists in db, do you want to create keyword with context?    1
            # yes -> create keyword with context [default yes]       1
            # no, user might have made a context spelling mistake    0
        # context doesn't exist in db, do you want to assign keyword def. to a context?  0
                                # yes, create keyword & context [yes]     1
                                # no, user might have made a context spelling mistake  0


    # keyword exists, context doesn't                                                          1 0
        # with no context defined. Would the user want to create another context?
            # yes, then prompt for user to specify context       1
                         # update definition & context?  0
                         # keep the old def, but new context, definition pair? (a dict)  1
            # no, then update the existing definition, keep with no context.  0
        # with one context. Would the user want to create another context?
            # no [update keyword]
            # yes [Keep old definition and create a new definition with context]
                # context == prevctx?
                    # yes, update keyword, keep context
                    # no, Does user want to create a new def. with context?
                        # yes
                        # no, update def. & update context
        # with more contexts(more defs.)  # TODO display context and 3 lines from definition for each definition
        # keyword exists with more contexts(more definitions) ->
        # user chose which context to load, so the context should
        # be known & stored before this function is called. Would the user want to create another context?
            # yes, then prompt for user to specify context
                         # update definition & context?
                         # keep the old def, but new context, definition pair? (a dict)
            # no, then update the existing definition, keep with same context.


    # keyword exists, context exists                                                           1 1
        # if more contexts, load one of them
        # context exists in db:
            # context == prevctx?
                # yes, then update keyword
                # no:
                    # abort? [a]
                    # keyword has no context. Update kewyword and assign a context?
                        # yes
                        # no, keep old definition and create a new def with this context
                    # keyword has a context. Do you want to update just the keyword context?
                        # yes, update keyword and context
                        # no, keep old definition and create a new def with context
        # context doesn't exist in db:
            # abort [a]
            # keyword has no context. Update kewyword and assign a context?
                # yes
                # no, keep old definition and create a new def with this context
            # keyword has a context. Do you want to update just the keyword context?
                # yes, update keyword and context
                # no, keep old definition and create a new def with context


                #if keyword:
                #    # if keyword already defined in database, update it
                #    keyword = update_keyword_info(store, keyword, help_buffer)
                #else:
                #    # create a new keyword
                #    keyword = create_keyword(store, word, help_buffer)

    ## TODO: context.name? this will be an error if no context is defined whatsoever
    #print("Keyword and its definition were saved in %s context." % context.name)

    store.close()


def helper_delete(keyword):
    """
    this function deletes from DB the keyword whose content in help_buffer
    is displayed;
    in the future, it could delete from DB the word under cursor.
    """
    # reopen database connection
    store._connection = store.get_database().connect()

    # TODO: prompt a question for user to confirm if he wants keyword with name x
    # to be deleted.
    # Edge case: user calls Help_buffer on word, but word doesn't exist so he
    # starts filling the definition, but he changes his mind and wants to delete
    # the keyword - calls :HelperDelete, because he thinks kw in the db, but it
    # isn't, so db will throw a python storm error. Provide a backup for this...

    if keyword:
        kw_name = keyword.name
        store.remove(keyword)
        store.commit()
        print("Keyword %s and its definition removed from database" % kw_name)
    else:
        print("Can't delete a word and its definition if it's not in the database.")

    store.close()


def helper_all_words():
    """
    List all keywords from database into help_buffer.
    """

    # reopen database connection
    store._connection = store.get_database().connect()
    # select only the keyword names
    result = store.execute("SELECT name FROM keyword;")
    # dump from generator into a list
    l = result.get_all()
    '''
    Example:
    >>> l
    [(u'line',), (u'color',), (u'canvas',)]
    '''
    # the above is a list of two tuples, we create a list of strings
    names = [t[0] for t in l]
    '''
    >>> names
    [u'line', u'color', u'canvas']
    '''
    names.sort()
    '''
    >>> names
    [u'canvas', u'color', u'line']
    '''
    vim.command("exe 'set noro'")                     # set noreadonly
    #help_buffer[:] = "\t".join(names)
    help_buffer[:] = names
    vim.command("exe 'set ro'")                       # set noreadonly

    store.close()
