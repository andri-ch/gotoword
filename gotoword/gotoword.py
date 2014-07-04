### System libraries ###
import os.path
import sys
import functools

# needed by VimServer class
import threading
import subprocess
import time

### Third party libs ###
from storm.locals import Store


VIM_FOLDER = os.path.expanduser('~/.vim')
# os.path.expanduser turns '~' into an absolute path, because os.path.abspath can't!
PLUGINS_FOLDER = 'andrei_plugins'
# PLUGINS_FOLDER can be any of "plugin", "autoload", etc.
# TODO: decide in which plugin folder is more appropriate to install this
# plugin
PLUGIN_NAME = 'gotoword'
PYTHON_PACKAGE = 'gotoword'

PLUGIN_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(PLUGIN_PATH, 'gotoword.vim')

### Own libraries ###
# NOTICE
# the python path when these lines are executed is the path of the currently
# active buffer (vim.current.buffer) in which this code is executed
# So, to import our own libs, we have to add them to python path.
sys.path.insert(1, os.path.join(VIM_FOLDER, PLUGINS_FOLDER, PLUGIN_NAME, PYTHON_PACKAGE))
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


def toggle_activate(f):
    """
    Activate/focus the helper buffer and then activate/focus again the last
    used buffer.
    """
    def wrapper_activate(obj, *args, **kwargs):
        # store old buffer
        user_buf_nr = obj.vim.get_active_buffer()
        # activate the buffer so we can set some buffer options
        obj.vim.command("buffer! %s" % obj.buffer_nr)
        f(obj, *args, **kwargs)
        # f(obj, ...) because we need to pass ALL args to wrapped function
        # make the old buffer active again
        obj.vim.command("buffer! %s" % user_buf_nr)
    return wrapper_activate


def toggle_readonly(f):
    """decorator used to set buffer options inside vim editor"""
    def wrapper_readonly(obj, *args, **kwargs):
        # if called repeatedly, remove readonly flag set by previous calls
        obj.vim.command("set noreadonly")
        res = f(*args, **kwargs)
        obj.vim.command("set readonly")
        # by setting buffer readonly, we want user to prevent from saving it
        # on harddisk with :w cmd, instead we want user to update the
        # database with HelperUpdate vim cmd or HelperSave
        return res
    return wrapper_readonly


def database_operations(f):
    """decorator used to open and close a database connection before each
    call to the wrapped function."""
    # pass decorated func's name, description to wrapper
    @functools.wraps
    def wrapper_operations(*args, **kwargs):
        # reopen database connection
        STORE._connection = STORE.get_database().connect()
        # call decorated function
        res = f(*args, **kwargs)
        # close database connection
        STORE.close()
        return res
    return wrapper_operations


class VimServer(object):
    """Represents a remote vim server."""
    def __init__(self, name, filename=''):
        # vim server needs to be started in a subprocess:
        # subprocess.call("vim -g -n --servername GOTOWORD", shell=True)
        # start vim subprocess in a new thread in order not to block this
        # script:
        self.name = name
        server = threading.Thread(
            name=name,
            target=subprocess.call,
            args=("vim -g -n --servername %s %s" % (name, filename),),
            kwargs={'shell': True}
        )
        server.start()
        print("I am a blocking thread? Why's that so?")
        # allow vim enough time to start as server, to avoid messages like:
        # E247: no registered server named "GOTOWORD": Send expression failed.
        # E247: no registered server named "GOTOWORD": Send failed.
        while True:
            # check server exists
            vim_server = subprocess.check_output("vim --serverlist", shell=True)
            if vim_server.strip().lower() != 'gotoword':
                print("Launched vim server and waiting for it to become available.\n"
                      "Stop this with CTRL + C if nothing happens in 3 or 4 seconds.")
                time.sleep(1)
            else:
                break
        # source the plugin script
        subprocess.call("""vim --servername {0} --remote-send ':source {1} <Enter>'""".format(
            name, SCRIPT), shell=True)
        time.sleep(2)

        # TODO: get rid of these lines
        # enable this obj for toggle_activate() and other decorators
        #self.vim = self
        # get all lines from buffer as a list
        #self._buffer = self.eval('getline(1, "$")').split()


    def command(self, cmd):
        """Like vim.command()"""
        # TODO: eval & command should adapt depending on editor or vim server.
        # We just send the command in an underlying shell to the vim server
        # Eg: vim --servername GOTOWORD --remote-send ':qa! <Enter>'
        subprocess.call(
            """vim --servername {0} --remote-send ':{1} <Enter>'""".format(
            self.name, cmd), shell=True)

    def eval(self, expr):
        """Like vim.eval()"""
        # Eg. vim --servername GOTOWORD --remote-expr 'bufwinnr(1)'
        res = subprocess.check_output(
            """vim --servername {0} --remote-expr '{1}'""".format(
            self.name, expr), shell=True).strip()
        return res

   # # TODO: are __setitem__ and __getitem__ neccessary?
   # def __setitem__(self, index, value):
   #     """
   #     Called when obj[i] = value or obj[i:j] = sequence.
   #     type(index) = int or slice obj.
   #     """
   #     if isinstance(index, int):
   #         op_succeded = self.eval('setline(%s, "%s")' % (index, value))
   #         if not op_succeded:
   #             raise RuntimeError
   #         # get all lines from buffer as a list
   #         # vim.eval('getline(1, "$")').split()
   #     elif isinstance(index, slice):
   #         start, stop, step = index.indices(len(self._buffer))
   #         self._buffer[start:stop] = value
   #         # it seems that _buffer[start:stop:step] is not accepted by the
   #         # underlying vim buffer
   #         op_succeded = self.eval('setline(1, "%s")' % (index, self._buffer))
   #     else:
   #         raise TypeError("index must be either an int or a slice object")

   # def __getitem__(self, index):
   #     """
   #     type(index) = int or slice obj. Called when var = obj[i:j]
   #     """
   #     raise NotImplemented
   #     #return self._buffer[index]


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
        self.vim = vim_wrapper
        self.keyword = None
        # the current keyword which was displayed in helper buffer

    def main(self):
        """This might be obsolete."""
        self.vim_wrapper = VimWrapper(app=self)
        # detect if run inside vim editor and if yes, setup help_buffer
        if not isinstance(self.vim_wrapper.vim, VimServer):
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
    def helper_all_words(self, help_buffer):
        """
        List all keywords from database into help_buffer.
        """
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
        self.vim_wrapper.open_window(help_buffer.name)
        help_buffer[:] = names


class VimWrapper(object):
    """
    It is an alternative to the vim python module, by implementing it as an
    interface to a vim server, all commands and expressions are sent to it.
    """
    def __init__(self, app=None):
        self.parent = app
        self.help_buffer = None
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
            vim = VimServer("GOTOWORD")
        self.vim = vim

    def get_active_buffer(self):
        """
        get the current (active) vim buffer.
        """
        return self.vim.eval("winbufnr(0)")

    def setup_help_buffer(self, buffer_name=''):
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
        user_buf_nr = self.get_active_buffer()

        # create a buffer without opening it in a window
        self.vim.command("badd %s" % buffer_name)
        # create a buffer by opening it in a window
        #vim.command("split %s" % help_buffer_name)

        self.help_buffer = HelperBuffer(buffer_name, self)

        # activate the buffer so we can set some buffer options
        self.vim.command("buffer! %s" % self.help_buffer.buffer_nr)
        # make it a scratch buffer
        self.vim.command("setlocal buftype=nofile")
        self.vim.command("setlocal bufhidden=hide")
        self.vim.command("setlocal noswapfile")
        # prevent buffer from being added to the buffer list; can be seen with :ls!
        self.vim.command("setlocal nobuflisted")
        # Note: above options can be expressed in only one "setlocal ..." line

        # activate the user (initial) buffer
        self.vim.command("buffer! %s" % user_buf_nr)

    def open_window(self, buffer_name):
        """
        Opens a window inside vim editor with an existing buffer whose name is
        the value of buffer name.
        """
        # save current global value of 'switchbuf' in order to restore it later
        # and add 'useopen' value to it
        self.vim.command("let oldswitchbuf=&switchbuf | set switchbuf+=useopen")

        # open help buffer
        # 'sbuffer' replaces 'split' because we want to use same buffer window if
        # it exists because sbuffer checks the switchbuf option
        self.vim.command("sbuffer %s" % buffer_name)

        # restore switchbuf to its default value in order not to affect other plugin
        # functionality:
        self.vim.command("let &switchbuf=oldswitchbuf | unlet oldswitchbuf")

        # prevent vim from focusing the helper window created on top, by
        # focusing the last one used (the window used by user before calling this
        # plugin).
        # CTRL-W p   Go to previous (last accessed) window.
        self.vim.command('call feedkeys("\<C-w>p")')

    def close(self):
        """Sends the quit cmd to the vim server."""
        pass


class HelperBuffer(object):
    """
    Wraps a vim buffer which partially mimics the behaviour of a list.
    """
    def __init__(self, buffer_name, vim_wrapper=None):
        self.vim_wrapper = vim_wrapper
        # vim_wrapper.vim is the exposed interface of the vim editor.
        self.vim = vim_wrapper.vim
        self.name = buffer_name
        # we need the buffer number assigned by vim so we can get a reference
        # to it that we can later use by indexing vim buffers list.
        buffer_nr = self.vim.eval('bufnr("%s")' % self.name)
        # vim.eval returns a string that contains a vim list index
        self.buffer_nr = int(buffer_nr)
        # define the internal buffer which is the vim buffer:
        self._buffer = self.vim.buffers[self.buffer_nr]

    @database_operations
    def update(self, word):
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

        self.vim_wrapper.open_window(self.name)

        # look for keyword in DB
        keyword = utils.find_keyword(self.vim_wrapper.parent.store, word)

        if keyword:
            # load content in buffer, previous content is deleted
            self._buffer[:] = keyword.info.splitlines()
        else:
            # keyword doesn't exist, prepare buffer to be filled with user content

            # write to buffer the small help text
            self._buffer[:] = utils.introduction_line(word).splitlines()
            # .splitlines() is used because vim buffer accepts at most one "\n"
            # per vim line
        self.vim_wrapper.parent.keyword = keyword
        return keyword

# TODO: I think _set_buffer & _get_buffer can be safely deleted; nothing uses
# them
    def _set_buffer(self, value):
        """ Called when HelperBuffer_obj = value """
        self._buffer = value

    def _get_buffer(self):
        """
        Called when buffer is read: x = HelperBuffer_obj
        """
        return self._buffer

    @toggle_activate            # activate it before changing a vim buffer
    @toggle_readonly            # remove any readonly buffer protection
    def __setitem__(self, index, value):
        """
        Called when obj[i] = value or obj[i:j] = sequence.
        type(index) = int or slice obj.
        """
        if isinstance(index, int):
            self._buffer[index] = value
        elif isinstance(index, slice):
            start, stop, step = index.indices(len(self._buffer))
            self._buffer[start:stop] = value
            # it seems that _buffer[start:stop:step] is not accepted by the
            # underlying vim buffer
        else:
            raise TypeError("index must be either an int or a slice object")

    def __getitem__(self, index):
        """
        type(index) = int or slice obj. Called when var = obj[i:j]
        """
        return self._buffer[index]


############
### MAIN ###

#App.main()
