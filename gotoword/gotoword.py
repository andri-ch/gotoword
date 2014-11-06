### System libraries ###
import os
import os.path
import sys
import logging

### Third party libs ###
# for database:
from storm.locals import Store

### import vim python library ###
try:
    import vim
    # the vim module contains everything we need to interact with vim
    # editor from python, but only when python is used inside vim.
    # Eg. you can't import vim in ipython like a normal module
    # More info here:
    # http://vimdoc.sourceforge.net/htmldoc/if_pyth.html#Python
except ImportError:
    print("Script must be run inside vim editor!")
    print("Either quit or use some variables and functions")
    #sys.exit()

def set_up_logging(default_level):
    ### DEBUG -> is the lowest level ###

    msg_format = '[  %(levelname)s  ] %(className)s.%(funcName)s - %(message)s'
    logging.basicConfig(format=msg_format, level=default_level)
    logger = logging.getLogger('Main')

    ##  SET UP A HANDLER THAT LOGS TO FILE ###
    # Handlers send the log records (created by loggers) to the appropriate
    # destination: a console, a file, over the internet, by email, etc.
    filename = None
    # script that is run from vim editor has one log filename, while script
    # that is run from a python interpreter external to vim editor has
    # another filename
    try:
        import vim
        filename = "gotoword_vim.log"
    except ImportError:
        # TODO: do I need this branch? This script won't be executed outside
        # editor
        # this branch is executed when this script is run outside vim editor
        filename = "gotoword_ipython.log"
        ### SET UP A CONSOLE HANDLER ###
        console_handler = logging.StreamHandler()       # stream -> sys.stdout
        # set level per handler
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)
        # this handler outputs debug messages although level is info

    file_handler = logging.FileHandler(filename=filename, mode='w')
    logger.addHandler(file_handler)
    return logger

logger = set_up_logging(logging.DEBUG)


VIM_FOLDER = os.path.expanduser('~/.vim')
# os.path.expanduser turns '~' into an absolute path, because os.path.abspath can't!
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
# active buffer (vim.current.buffer) in which this code is executed
# So, to import our own libs, we have to add them to python path.
SOURCE_DIR = os.path.join(VIM_FOLDER, PLUGINS_FOLDER, PLUGIN_NAME, PYTHON_PACKAGE)
sys.path.insert(1, SOURCE_DIR)
# Eg. '/home/username/.vim/a_plugins_dir/gotoword/gotoword'
import utils               # should be replaced by import utils


# plugin's database that holds all the keywords and their info
DB_NAME = 'keywords.db'
DATABASE = utils.create_database('sqlite:' + os.path.join(VIM_FOLDER,
                                 PLUGINS_FOLDER, PLUGIN_NAME, DB_NAME))
# Eg: DATABASE = 'sqlite:/home/user/.vim/user_plugins/gotoword/keywords.db'
STORE = Store(DATABASE)
# store is a cursor to database wrapped by storm

logger.debug("Following constants are defined: \n"
             "\t\t VIM_FOLDER: %s \n"
             "\t\t PLUGINS_FOLDER: %s \n"
             "\t\t PLUGIN_NAME: %s \n"
             "\t\t PYTHON_PACKAGE: %s \n"
             "\t\t PLUGIN_PATH: %s \n"
             "\t\t SCRIPT: %s \n"
             "\t\t SOURCE_DIR: %s \n"
             "\t\t DATABASE: %s \n" %
             (VIM_FOLDER, PLUGINS_FOLDER, PLUGIN_NAME, PYTHON_PACKAGE,
             PLUGIN_PATH, SCRIPT, SOURCE_DIR, DATABASE),
             extra={'className': ""}
             )


# move to utils.py
def strip(s):
    """Used to stringify and then strip a class name accessed using obj.__class__
    so that it is suitable for pretty printing.
    This function will be used like this::

        >>> print("this is class %s " % strip(obj.__class__))
        'this is class module.Class'

    Without this function the output would look like this::

        'this is class <class 'module.Class'>

    This function is needed because::

        >>> obj.__class__
        module.Class
        >>> print(obj.__class__)
        <class 'module.Class'>
        >>> type(s)
        type

    so obj.__class__ is not 'str' but of type 'type' , so we need to call
    repr(s) to get the string notation and get rid of the characters we don't
    want.

    It is used by the logging system.
    """
    return repr(s).lstrip("<class '").rstrip("'>")


def get_active_buffer():
    """
    get the current (active) vim buffer.
    """
    return vim.eval("winbufnr(0)")


def toggle_activate(f):
    """
    Activate/focus the helper buffer and then activate/focus again the last
    used buffer.
    """
    def wrapper_activate(obj, *args, **kwargs):
        # store old buffer
        user_buf_nr = get_active_buffer()
        # activate the buffer whose index is obj.index so we can set some
        # buffer options
        vim.command("buffer! %s" % obj.index)
        f(obj, *args, **kwargs)
        # f(obj, ...) because we need to pass ALL args to wrapped function;
        # make the old buffer active again
        vim.command("buffer! %s" % user_buf_nr)
    return wrapper_activate


def toggle_readonly(f):
    """decorator used to set buffer options inside vim editor"""
    def wrapper_readonly(obj, *args, **kwargs):
        # if called repeatedly, remove readonly flag set by previous calls
        vim.command("set noreadonly")
        # the format of the log message below takes into account that this is a
        # wrapper only for __setitem__() methods that are found in a mapping
        # object; I probably should reformat this message
        logger.debug("obj: %s, index: %s , value: %s " % (obj, args[0], args[1]),
                     extra={'className': ''}
                     )
        res = f(obj, *args, **kwargs)
        vim.command("set readonly")
        # by setting buffer readonly, we want user to prevent from saving it
        # on harddisk with :w cmd, instead we want user to update the
        # database with HelperSave or HelperUpdate vim cmd
        return res
    return wrapper_readonly


def database_operations(f):
    """decorator used to open and close a database connection before each
    call to the wrapped function."""
    # pass decorated func's name, description to wrapper
    #@functools.wraps
    def wrapper_operations(*args, **kwargs):
        # reopen database connection
        STORE._connection = STORE.get_database().connect()
        # call decorated function
        res = f(*args, **kwargs)
        # close database connection
        STORE.close()
        return res
    return wrapper_operations


    # TODO:
    # toggle_activate, toggle_readonly should be part of vim client server
    # get_active_buffer, setup_help_buffer, open_window should be part of
    # vim client.


class App(object):
    """
    This is the main plugin app. Run App.main() method to launch it.
    """
    # create a help_buffer that will hold info retrieved from database, etc. but
    # prevent vim to create buffer in current working dir, by setting an explicit
    # path;
    help_buffer_name = os.path.join(VIM_FOLDER, PLUGINS_FOLDER, PLUGIN_NAME,
                                    PLUGIN_NAME + '_buffer')
    # help_buffer is created on the fly, in memory, it doesn't exist on disk, but we
    # specify a full path as its name

    def __init__(self, vim_wrapper=None):
        self.vim_wrapper = vim_wrapper
        self.word = None
        self.keyword = None
        # the current keyword which will be displayed in helper buffer
        logger.debug("gotoword started from vim pid: %s and parent's: %s" %
                    (os.getpid(), os.getppid()), extra={'className': strip(self.__class__)})

    def main(self):
        """This is the main entry point of this script."""
        logger.debug("", extra={'className': strip(self.__class__)})
        self.vim_wrapper = VimWrapper(app=self)
        # detect if run inside vim editor and if yes, setup help_buffer
        #if not isinstance(self.vim_wrapper.vim, VimServer):
        #    self.vim_wrapper.setup_help_buffer(self.help_buffer_name)
        self.vim_wrapper.setup_help_buffer(self.help_buffer_name)

    @database_operations
    def helper_save(self, context, test_answer):
        """
        this function, if called twice on same keyword(first edit, then an update)
        should know that it doesn't need to create another keyword, just to update
        """
        # bind to app for easier handling
        self.context = context
        self.test_answer = test_answer
        # state strategy pattern:
        self.state = EntryState()
        self.saving = True
        while self.saving:
            self.state = self.state.evaluate(self, self.keyword, self.context, self.test_answer)
            if self.state is None:
                self.saving = False


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

    @database_operations
    def helper_delete(self, keyword, context=None):
        """
        this function deletes from DB the keyword whose content in help_buffer
        is displayed;
        in the future, it could delete from DB the word under cursor.
        context - it deletes only the definition of keyword for a specific
                  context (#TODO)
        """

        # TODO: prompt a question for user to confirm if he wants keyword with name x
        # to be deleted.
        # Edge case: user calls Help_buffer on word, but word doesn't exist so he
        # starts filling the definition, but he changes his mind and wants to delete
        # the keyword - calls :HelperDelete, because he thinks kw is in the db, but it
        # isn't, so db will throw a python storm error. Provide a backup for this...

        if keyword:
            kw_name = keyword.name
            # TODO: kw_name exists only for the print msg, but can be replaced by
            # keyword.name which is still in the namespace, right?
            STORE.remove(keyword)
            STORE.commit()
            print("Keyword %s and its definition was removed from database" %
                  kw_name)
        else:
            print("Can't delete a word and its definition if it's not in the database.")

    @database_operations
    def helper_delete_context(self, context):
        "Deletes context from database."
        context = utils.Context.find_context(STORE, context)
        if context:
            ctx_name = context.name
            STORE.remove(context)
            STORE.commit()
            print("Context %s was removed from database" % ctx_name)
        else:
            print("Can't delete a context if it's not in the database.")

    @database_operations
    def helper_all_words(self):
        """
        List all keywords from database into help_buffer.
        """
        logger.debug("", extra={'className': strip(self.__class__)})
        # select only the keyword names
        result = STORE.execute("SELECT name FROM keyword;")
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
        self.vim_wrapper.open_window(self.help_buffer_name)
        logger.debug("names: %s" % names, extra={'className': strip(self.__class__)})
        self.vim_wrapper.help_buffer[:] = names

    @database_operations
    def helper_all_contexts(self):
        """
        List all contexts from database into help_buffer.
        """
        logger.debug("", extra={'className': strip(self.__class__)})
        # select only the keyword names
        result = STORE.execute("SELECT name FROM context;")
        # dump from generator into a list
        l = result.get_all()
        '''
        Example:
        >>> l
        [(u'python',), (u'django',), (u'java',)]
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
        self.vim_wrapper.open_window(self.help_buffer_name)
        logger.debug("names: %s" % names, extra={'className': strip(self.__class__)})
        self.vim_wrapper.help_buffer[:] = names

    @database_operations
    def helper_context_words(self, context):
        """
        Displays all keywords that have a definition belonging to this
        context.
        context - a string
        Returns a list of words.
        """
        # locate context into database and retrieve it as a Storm ORM object
        storm_context = utils.Context.find_context(STORE, context)
        words_generator = storm_context.keywords.values(utils.Keyword.name)
        words = [w for w in words_generator]
        words.sort()
        # TODO: the following can be split into a template, the above is the
        # view
        # add a title on the first line
        self.vim_wrapper.help_buffer[0:0] = [
            "The following keywords have a meaning (definition) in '%s' "
            "context:" % storm_context.name]
        self.vim_wrapper.help_buffer[1:] = words
        return words

    @database_operations
    def helper_word_contexts(self):
        """
        It is used for testing, it should not be available to the user.
        Returns a list of contexts.
        """
        contexts = None
        if self.keyword:
            contexts_generat = self.keyword.contexts.values(utils.Context.name)
            contexts = [c for c in contexts_generat]
            contexts.sort()
            self._display_word_contexts(self.keyword, contexts)

    def _display_word_contexts(self, kw, contexts):
        # add a title on the first line
        if contexts:
            self.vim_wrapper.help_buffer[0:0] = [
                "The keyword '%s' has information belonging to the following "
                "contexts:" % kw.name]
            self.vim_wrapper.help_buffer[1:] = contexts
        else:
            self.vim_wrapper.help_buffer[:] = [
                "The keyword '%s' has information that doesn't belong to any "
                "context" % kw.name]


class VimWrapper(object):
    # TODO: maybe VimWrapper is not the best name, might create confusion
    #
    """
    It is an alternative to the vim python module, by implementing it as an
    interface to a vim server, all commands and expressions are sent to it.
    """
    def __init__(self, app=None):
        self.parent = app
        self.help_buffer = None

    def setup_help_buffer(self, buffer_name):
        """
        It does an init job for a vim buffer by setting buffer options.
        It should be run only once.
        Opens a buffer customized for this plugin, a "scratch" or temporary kind
        of buffer. To read more about it, inside vim do:
        :help special-buffers

        returns a reference to the vim buffer.
        """
        # store current active buffer so that we can get back to it after we setup
        # our help_buffer
        user_buf_nr = get_active_buffer()

        # create a buffer without opening it in a window
        vim.command("badd %s" % buffer_name)
        # create a buffer by opening it in a window
        #vim.command("split %s" % help_buffer_name)

        # we need the buffer number assigned by vim so we can get a reference
        # to it that we can later use by indexing vim buffers list.
        buffer_nr = vim.eval('bufnr("%s")' % buffer_name)
        # vim.eval returns a string that contains a vim list index
        self.buffer_nr = int(buffer_nr)
        #self.help_buffer = HelperBuffer(buffer_name, self)
        self.help_buffer = vim.buffers[self.buffer_nr]
        logger.debug("help_buffer: %s" % self.help_buffer, extra={'className': strip(self.__class__)})

        # activate the buffer so we can set some buffer options
        vim.command("buffer! %s" % self.buffer_nr)
        # make it a scratch buffer
        vim.command("setlocal buftype=nofile")
        vim.command("setlocal bufhidden=hide")
        vim.command("setlocal noswapfile")
        # prevent buffer from being added to the buffer list; can be seen with :ls!
        vim.command("setlocal nobuflisted")
        # Note: above options can be expressed in only one "setlocal ..." line

        # activate the user (initial) buffer
        vim.command("buffer! %s" % user_buf_nr)

    @staticmethod
    def open_window(buffer_name):
        """
        Opens a window inside vim editor with an existing buffer whose name is
        the value of buffer name.
        """
        # save current global value of 'switchbuf' in order to restore it later
        # and add 'useopen' value to it
        vim.command("let oldswitchbuf=&switchbuf | set switchbuf+=useopen")

        # open help buffer
        # 'sbuffer' replaces 'split' because we want to use same buffer window if
        # it exists because sbuffer checks the switchbuf option
        vim.command("sbuffer %s" % buffer_name)

        # restore switchbuf to its default value in order not to affect other plugin
        # functionality:
        vim.command("let &switchbuf=oldswitchbuf | unlet oldswitchbuf")

        # prevent vim from focusing the helper window created on top, by
        # focusing the last one used (the window used by user before calling this
        # plugin).
        # CTRL-W p   Go to previous (last accessed) window.
        vim.command('call feedkeys("\<C-w>p")')

    @database_operations
    def update_buffer(self, word):
        """
        Updates an existing buffer with information about a
        keyword or displays an invitation for the user to fill in info about
        words that don't exist in the database.

        Tasks:
            open help buffer in its own window
            look for keyword in database
            display info in the help_buffer
        """
        # convert fct. arg to unicode, for python2.x, this is what is stored in the db
        word = unicode(word)
        # make it case-insensitive
        self.parent.word = word.lower()
        logger.debug("before opening window", extra={'className': strip(self.__class__)})
        self.open_window(self.parent.help_buffer_name)

        # look for keyword in DB
        #keyword = utils.find_keyword(self.vim_wrapper.parent.store, word)
        keyword = utils.find_keyword(STORE, self.parent.word)

        if keyword:
            # get contexts this keyword belongs to (specific to ORM); it
            # should be moved to utils
            contexts_generator = keyword.contexts.values(utils.Context.name)
            contexts = [c for c in contexts_generator]
            # add a title line at the top;
            # TODO: is the title line removed when kw is updated?
            self.help_buffer[0:0] = ['keyword: %s   contexts: %s' %
                                     (keyword.name, " ".join(contexts))]
            # load content in buffer, previous content is deleted
            self.help_buffer[1:] = keyword.info.splitlines()
        else:
            # keyword doesn't exist, prepare buffer to be filled with user content

            # write to buffer the small help text
            self.help_buffer[:] = utils.introduction_line(word).splitlines()
            # .splitlines() is used because vim buffer accepts at most one "\n"
            # per vim line
            #keyword = utils.Keyword(name=word)     # conflicts with HelperSave
            keyword = None
        return keyword

    def close(self):
        """Sends the quit cmd to the vim server."""
        # should call vim server's terminate() method.
        pass


class EntryState(object):
    """Makes an initial evaluation of keyword & context and decides which is
    the next state.
    """
    def __init__(self):
        pass

    @database_operations
    def evaluate(self, app, kw, context, test_answer):
        # kw is None if no keyword exists in database
        if (not kw) and (not context):
            # check out
            # http://www.diveintopython.net/power_of_introspection/and_or.html
            # for The peculiar nature of 'and' and 'or'
            # case when kw doesn't exist in DB and context was not given by
            # user
            # debug flags:
            app.kw = kw
            app.new_context0 = context
            app.bol = (not kw) and (not context)
            return ReadContextState()
        elif (not kw) and context:
            # debug flags:
            app.kw2 = kw
            app.new_context1 = context
            app.bol2 = context and (not kw)
            app.new_context = True
            # case when kw doesn't exist in DB and context was given by user;
            # context was supplied by user to save keyword in that context;
            # check if it exists in the database (if it is not a new one)
            ctx = utils.Context.find_context(STORE, context)
            # if context not in DB, ctx will be None, create a new context
            if not ctx:
                # TODO: prompt user that context doesn't exist and must be
                # created; if yes:
                # save it to DB
                app.new_context2 = True
                ctx = utils.Context(name=context)
                STORE.add(ctx)
                STORE.commit()
            # transform app.context which is just a string into a Storm object
            # from DB
            app.context = ctx
            # continue with creating and saving a keyword
            return NewKeywordState()
        elif kw and (not context):
            app.kwnotcontext = True
            # kw exists in db, context was not given by user -> update kw info
            # to same context, if context exists, or to no context at all
            return UpdateKeywordState()
            #return None
        else:
            # so both kw and context are defined: info will be assigned to
            # other context -> update kw
            app.kwandcontext = True
            #return None
            return UpdateKeywordState()


class ReadContextState(object):
    """Prompts user to supply context."""
    def evaluate(self, app, kw, context, test_answer):
        # we keep this code in case we want to drop inputlist() for reading
        # user input
        # input(), inputlist(), getchar() are all Vim blocking methods, cannot
        # be tested well...

        #print("Do you want to specify a context that this definition of the word "
        #      "applies in?")
        #message = "[Y]es define it    [N]o do not define it    [A]bort"
        ### following vim cmds are needed because:
        ###   http://vim.wikia.com/wiki/User_input_from_a_script
        #vim.command('call inputsave()')
        ## put vim cursor here:
        #vim.command("let user_input = input('" + message + ": ')")
        #vim.command('call inputrestore()')
        #vim.command('echo ""')     # make prompt pass to next line, for pretty printing
        #answer = vim.eval('user_input')

        # TODO: put it in a while loop, like any prompt should be
        # eg: while not answer in ('0', '1', '2')
        answer = vim.eval("""inputlist(["Do you want to specify a context that this definition of the word applies in?", \
                "0. Yes, I will provide a context [0 and press <Enter>]", \
                "1. No, I won't provide a context [1 and press <Enter>]", \
                "2. Abort [2 and press <Enter>]" ])
                """)
        # TODO: provide another option for 'Yes, I will provide an existing
        # context'

        # inputlist() is blocking the prompt, waiting for a key from user
        # inputlist() returns '0' if no option is chosen or if first option is
        # chosen

        #print("Do you want to specify a context that this definition of the word "
        #      "applies in?")
        #vim.command('echo ""')     # make prompt pass to next line, for pretty printing
        #message = "[Y]es define it    [N]o do not define it    [A]bort"
        #print(message)
        #vim.command('echo ""')     # make prompt pass to next line, for pretty printing
        ##answer = vim.eval('getchar(0)')
        ## the following snippet is taken from here:
        ## http://stackoverflow.com/questions/4189239/vim-script-input-function-that-doesnt-require-user-to-hit-enter
        ## snippet is needed because 8 bit characters are converted to numbers
        ## by getchar()
        #vim.command('exe "let c = getchar()"')
        #vim.command("exe \"if c =~ '^\d\+$' | let c = nr2char(c) | endif\"")
        ## allow multiple commands on same line with |
        ##vim.command('exe "let c = nr2char(c) | endif"')
        ##vim.command('exe "endif"')
        #answer = vim.eval('c')

        #answer = vim.eval('confirm("Do you want to define a context that this definition of the word applies in?", "&Yes\n&No\n&Cancel")')
        answer = answer.strip().lower()
        # use test_answer if it is supplied (when testing)
        answer = test_answer if test_answer else answer
        # attach this local variable to our app
        app.answer = answer
        #if answer.startswith('1'):
        #if answer.startswith(' 1'):
        #if answer == '1' or answer.startswith('y'):
        if answer == '0' or answer.startswith('y'):
            # read context ....
            # debug:
            vim.command('echo "\n"')
            vim.command('echomsg "You entered: [\"%s\"]"' % app.answer)
            return CheckContextState()
            #return NewKeywordState()
        elif answer.startswith('1') or answer.startswith('n'):
            app.nocontextno = True        # debug
            return NewKeywordState()
        #elif answer.startswith('0') or answer.startswith('a'):
        elif answer.startswith('2') or answer.startswith('a'):
            # Abort
            vim.command('echo ""')     # make prompt pass to next line ???!, for pretty printing
            vim.command('echomsg "You entered: [\"%s\"]"' % answer)
            vim.command('echo "You entered: [\"%s\"]"' % test_answer)
            vim.command('echo ""')     # make prompt pass to next line, for pretty printing
            vim.command('echo "None is returned"')
            return None
        else:
            vim.command('echomsg "Invalid option! Type a number from 0 to 2"')
            return None


class NewKeywordState(object):
    "Creates a keyword and stores it to database."
    @database_operations
    def evaluate(self, app, kw, context, test_answer):
        # global app
        app.keyword = utils.create_keyword(STORE, app.word,
                                           app.vim_wrapper.help_buffer)
        # add keyword definition to context
        app.keyword.contexts.add(context)
        STORE.commit()
        vim.command('echomsg "keyword %s saved into context %s"' %
                    (app.keyword.name, context))
        return None


class CheckContextState(object):
    # TODO rename to CreateContextState and create a CheckContextState that
    # points you to CreateContextState if context name is new, else just
    # assigns it to keyword
    """Creates a context and stores it to database. It returns a
    NewKeywordState, because we use this class only when user wants to define
    a keyword and a context, so first we define a context then we define a
    keyword and we add it to the context.
    """
    @database_operations   # maybe I should remove these for the evaluate fcts
    def evaluate(self, app, kw, context, test_answer):
        # capture from stdin the context name
        message = "Enter a one word context name: \n"
        answer = get_user_input(message, test_answer)
        # debug
        vim.command('echo "\n"')
        vim.command('echomsg "You entered: \'%s\'"' % answer)
        # validate it
        context = STORE.find(utils.Context, utils.Context.name == answer).one()
        if context:
            # user typed an existing context
            # TODO: don't raise, output a friendlier message and return to
            # previous state/the proper state
            #raise RuntimeError("Context '%s' already exists!" % context)
            app.context = context
            return NewKeywordState()
        else:
            # user typed a context name that doesn't exist in DB, so create a
            # new one
            app.context = answer
            return CreateContextState()


class CreateContextState(object):
    """TODO: add description."""
    @database_operations   # maybe I should remove these for the evaluate fcts
    def evaluate(self, app, kw, context, test_answer):
        context = utils.Context(name=context)
        # make it a storm object
        context = STORE.add(context)

        # capture from stdin the short description of the context
        message = "Enter a short description of the context you just defined: \n"
        answer = get_user_input(message, test_answer)
        # debug
        vim.command('echo "\n"')
        vim.command('echomsg "You entered: \'%s\'"' % answer)
        # add it to the storm object, to the appropriate field
        # TODO: add a 'description' field to utils.Context
        #context.description = answer
        STORE.commit()
        app.context = context
        #return None
        return NewKeywordState()


class UpdateKeywordState(object):
    "Updates the information field of a keyword."
    def evaluate(self, app, kw, context, test_answer):
        # retrieve context
        pass


def get_user_input(message, test_answer):
    "Returns the user input from vim, displaying a message at the prompt."
    if test_answer:
        answer = unicode(test_answer)
    else:
        vim.command('call inputsave()')
        vim.command("let user_input = input('%s')" % message)
        vim.command('call inputrestore()')
        answer = vim.eval('user_input')
        # sanitize it (strip, lowercase, unicode it, etc.)
        answer = unicode(answer.strip().lower())
    return answer

#### MAIN ###

##App.main()
