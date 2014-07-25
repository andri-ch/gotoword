### System libraries ###
import os
import os.path
import sys
import logging

# needed by VimServer class
import subprocess
import time
import multiprocessing

### Third party libs ###
# for database:
from storm.locals import Store


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
import gotoword_state_machine

# plugin's database that holds all the keywords and their info
DB_NAME = 'keywords.db'
DATABASE = utils.create_database('sqlite:' +
                os.path.join(VIM_FOLDER, PLUGINS_FOLDER, PLUGIN_NAME, DB_NAME)
           )
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


def create_vim_list(values):
    """creates the Vim editor equivalent of python's repr(a_list).

        >>> create_vim_list(['first line', 'second line'])
        '["first line", "second line"]'

    We need double quotes not single quotes.
    This result can be fed to vim's eval function to create a list in vim.
    """
    values_with_quotes = ('"' + elem + '"' for elem in values)
    return '[%s]' % ', '.join(values_with_quotes)
    # as a one liner:
    #return '[%s]' % ', '.join("\"%s\"" % elem for elem in values)


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


class VimBuf(object):
    """
    Emulate a vim buffer whose index has the value received in the constructor.
    An instance of this class can read and write lines to the vim buffer it
    emulates.

    A vim buffer partially behaves like a list, so this class
    wraps a python list, but will take into account that buffer line indexing
    starts from 1, not from 0 like in a python list.

    Eg::

        buf = VimBuf(index)
        buf[1]
        # should output first line of vim buffer, not second line
        # like a python list would.

    """
    def __init__(self, index):
        # store the vim index (buffer number) of the vim buffer that
        # it emulates.
        self.index = index
        self._buffer = None     # will be a list

    def __str__(self):
        self._read_vim_buffer()
        return "\n".join(self._buffer)

    def __repr__(self):
        return "VimBuf(%s)" % self.index

    def _read_vim_buffer(self):
        """Read vim buffer contents so that what this buffer stores is the
        same with what's displayed in the actual vim buffer.
        """
        # get all lines from vim buffer as a list
        self._buffer = vim.eval('getbufline(%s, 1, "$")' % self.index).split("\n")
        # TODO: this is where you can make list values start from index = 1,
        # just like it is for vim buffers

    def __get__(self):
        """
        This method is part of the descriptor protocol along with __set__(),
        __delete__().
        Suppose:
            buf = VimBuf(...)
        Called when:
            var = buf
        """
        logger.debug("", extra={'className': strip(self.__class__)})
        # empty message "" is needed because a message is mandatory
        raise NotImplementedError
        #self._read_vim_buffer()
        #return self

    def __set__(self, value):
        logger.debug("called with value %s" % value,
                     extra={'className': strip(self.__class__)})
        raise NotImplementedError

    @toggle_activate            # activate it before changing a vim buffer
    @toggle_readonly            # remove any readonly buffer protection
    def __setitem__(self, index, value):
        """
        Called when obj[i] = value or obj[i:j] = sequence.
        type(index) = int or slice obj.
        It should write straight to vim buffer.
        It should behave like vim's setline().
        """
        # log when it enters function
        logger.debug("", extra={'className': strip(self.__class__)})
        # define flag for succesful operation
        exit_code = '1'            # 0 is True, 1 is False

        value = create_vim_list(value)
        # we do this because when type(index) == int we can assign one line
        # or multiple lines:
        # setline(1, ["one line"])  AND
        # setline(1, ["one line", "another line"])

        if isinstance(index, int):
            # TODO: catch IndexError when index is just one unit bigger than
            # last index and append to list to emulate vim behaviour.
            #self._buffer[index] = value
            exit_code = vim.eval('setline(%s, %s)' % (index + 1, value))
            # setline's 1st arg is incremented because buffer indexing starts
            # from 1
            #succeded = vim.eval('setline(2, "test - a vim string")')
            #succeded = vim.eval('setline(5, strftime("%c"))')
        elif isinstance(index, slice):
            # update self._buffer
            self._read_vim_buffer()
            start, stop, step = index.indices(len(self._buffer))
            #self._buffer[start:stop] = value
            # it seems that _buffer[start:stop:step] is not accepted by the
            # underlying vim buffer

            # if index is a slice we also expect that value is a list
            if not isinstance(value, list):
                raise TypeError("value must be a list of strings not a %s" %
                                type(value))
            exit_code = vim.eval('setline(%s, %s)' % (start + 1, value))
            # there are two ways to feed text to setline();
            # as above, by creating a list:
            # setline(index, ["line 1", "line 2"])
            # second way:
            #for index, value in zip(range(1, 3), ["first line", "second"]):
            #    vim.eval('setline(%s, "%s")' % (index, value))
        else:
            raise TypeError("index must be either an int or a slice object")

        if exit_code != '0':
            logger.debug("didn't manage to update buffer in vim server with "
                         "value %s" % value, extra={'className': strip(self.__class__)})

    def __getitem__(self, index):
        """
        type(index) = int or slice obj. Called when var = obj[i:j]
        """
        logger.debug("", extra={'className': strip(self.__class__)})
        self._read_vim_buffer()
        if isinstance(index, int):
            return self._buffer[index]
        elif isinstance(index, slice):
            start, stop, step = index.indices(len(self._buffer))
            return self._buffer[start:stop]
        else:
            raise TypeError("index must be either an int or a slice object not a %s" %
                            type(index))

    def append(self, value):
        """Adds lines after last line of vim buffer.
        It makes use of vim's setline() property:
        When {lnum} is just below the last line the {text} will be
        added as a new line.
        So this method makes index to be one unit greater than the highest
        current index.
        """
        self._read_vim_buffer()
        self[len(self._buffer) - 1] = value


class VimBuffers(object):
    """Implements the vim list of buffers."""
    def __init__(self):
        self._buffer = None

    def __str__(self):
        # TODO: it should print the vim buffer list:  index, name
        pass

    def __getitem__(self, index):
        """
        type(index) = int. Called when var = obj[i]
        Exists because it is used by vim.buffers[i] to get a vim buffer if vim
        is the python module supplied by vim or if it is the vim server this
        script has created.
        """
        return VimBuf(index)

    def __setitem__(self, index, value):
        pass
        # TODO: implement it


class VimServer(object):
    """Represents a remote vim server. It tries to implement the same
    interface as the python vim module provided by the python interpreter
    used by vim editor.
    Eg::

        vim = VimServer(server1, filename="path_to_file")
        # the following is possible:
        vim.buffers
        etc.
    """
    def __init__(self, name, filename=''):
        self.name = name
        self.buffers = VimBuffers()
        logger.debug("", extra={'className': strip(self.__class__)})
        # vim server needs to be started in a subprocess:
        # subprocess.call("vim -g -n --servername GOTOWORD", shell=True)
        # start vim subprocess in a new thread in order not to block this
        # script:
        self.server = multiprocessing.Process(
            name=name,
            target=subprocess.call,
            args=(['vim', '-g', '-n', '--servername', name, filename],),
        )
        # if filename is empty, Vim will open a new document

    def start(self, timeout=5):
        """Starts the vim server in a new process. Waits for server to become
        active timeout seconds.
        """
        self.server.start()
        # allow vim enough time to start as server, to avoid messages like:
        # E247: no registered server named "GOTOWORD": Send expression failed.
        # E247: no registered server named "GOTOWORD": Send failed.
        while timeout:
            if self.is_running('gotoword'):
                break
            else:
                time.sleep(1)
                timeout -= 1
        else:
            print("Could not connect to vim server before timeout expired")
            sys.exit()

        # set flag that indicates that python app is running outside of vim
        # editor so next, when we're sourcing the script, the app won't be
        # initialized inside vim editor:
        #subprocess.call("""vim --servername {0} --remote-send ':let g:gotoword_remote_start = 1 <Enter>'""".format(
        #    name), shell=True)

    def is_running(self, name=''):
        """Checks if there's a running Vim instance with the server's name.

        Returns a Boolean.
        """
        server_list = subprocess.check_output(["vim", "--serverlist"]
                                              ).split("\n")
        logger.debug("vim server(s): %s" % server_list,
                     extra={'className': strip(self.__class__)})
        return name.lower() in map(str.lower, server_list)

    def source(self, script):
        """Source a script in Vim server.

        script - a filename with an absolute path
        """
        #subprocess.call("""vim --servername {0} --remote-send ':source {1} <Enter>'""".format(
        #    self.name, script, shell=True))
        subprocess.call(['vim', '--servername', self.name, '--remote-send', ':source %s <Enter>' % script])
        time.sleep(2)

    def terminate(self):
        """Sends SIGTERM to process.
        Calls multiprocessing.Process.terminate()."""
        self.server.terminate()

    def command(self, cmd):
        """Send commands to a Vim server.
        Used for Vim cmds and everything except for calling functions.
        A wrapper around --remote-send.
        """
        # We just send the command to the vim server
        # Eg: vim --servername GOTOWORD --remote-send ':qa! <Enter>'
        #subprocess.call(
        #    """vim --servername {0} --remote-send ':{1} <Enter>'""".format(
        #    self.name, cmd), shell=True)
        subprocess.call(
            ['vim', '--servername', self.name, '--remote-send',
             ':%s <Enter>' % cmd]
        )

    def eval(self, expr):
        """Like vim.eval(), mainly used to call Vim functions.
        A wrapper around --remote-expr.
        """
        # Eg. vim --servername GOTOWORD --remote-expr 'bufwinnr(1)'
        #res = subprocess.check_output(
        #    """vim --servername {0} --remote-expr '{1}'""".format(
        #    self.name, expr), shell=True).strip()
        res = subprocess.check_output(
            ['vim', '--servername', self.name, '--remote-expr', expr]).strip()
        return res


### import vim python library ###
try:
    import vim
    # the vim module contains everything we need to interact with vim
    # editor from python, but only when python is used inside vim.
    # Eg. you can't import vim in ipython like a normal module
    # More info here:
    # http://vimdoc.sourceforge.net/htmldoc/if_pyth.html#Python
except ImportError:
    # script is not called from vim editor so start a vim server;
    # just for testing/development purposes
    test_file = os.path.expanduser(
        "~/.vim/andrei_plugins/gotoword/gotoword/test/ft_test_text"
    )
    vim = VimServer("GOTOWORD", test_file)
    # this should belong to a testing module for vim and should be part of
    # setup in a unittest class

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
    # TODO: rename help_buffer to gotoword_buffer

    #help_buffer = setup_help_buffer(help_buffer_name)

    def __init__(self, vim_wrapper=None):
        self.vim_wrapper = vim_wrapper
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
    def helper_save(self, context):
        """
        this function, if called twice on same keyword(first edit, then an update)
        should know that it doesn't need to create another keyword, just to update
        """
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

    @database_operations
    def helper_delete(self, keyword):
        """
        this function deletes from DB the keyword whose content in help_buffer
        is displayed;
        in the future, it could delete from DB the word under cursor.
        """

        # TODO: prompt a question for user to confirm if he wants keyword with name x
        # to be deleted.
        # Edge case: user calls Help_buffer on word, but word doesn't exist so he
        # starts filling the definition, but he changes his mind and wants to delete
        # the keyword - calls :HelperDelete, because he thinks kw in the db, but it
        # isn't, so db will throw a python storm error. Provide a backup for this...

        if keyword:
            kw_name = keyword.name
            # TODO: kw_name exists only for the print msg, but can be replaced by
            # keyword.name which is still in the namespace, right?
            STORE.remove(keyword)
            STORE.commit()
            print("Keyword %s and its definition removed from database" % kw_name)
        else:
            print("Can't delete a word and its definition if it's not in the database.")

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


class VimWrapper(object):
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

    def open_window(self, buffer_name):
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
        word = word.lower()
        logger.debug("before opening window", extra={'className': strip(self.__class__)})
        self.open_window(self.parent.help_buffer_name)

        # look for keyword in DB
        #keyword = utils.find_keyword(self.vim_wrapper.parent.store, word)
        keyword = utils.find_keyword(STORE, word)

        if keyword:
            # load content in buffer, previous content is deleted
            self.help_buffer[:] = keyword.info.splitlines()
        else:
            # keyword doesn't exist, prepare buffer to be filled with user content

            # write to buffer the small help text
            self.help_buffer[:] = utils.introduction_line(word).splitlines()
            # .splitlines() is used because vim buffer accepts at most one "\n"
            # per vim line
        self.parent.keyword = keyword
        return keyword

    def close(self):
        """Sends the quit cmd to the vim server."""
        # should call vim server's terminate() method.
        pass


#### MAIN ###

##App.main()
