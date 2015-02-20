# -*- coding: utf-8 -*-

### System libraries ###
import logging
import logging.handlers
#import os.path
#import threading
#import time
#import sys

try:
    import vim
    # the vim module contains everything we need to interact with Vim
    # editor from python, but only when python is used inside Vim.
    # Eg. you can't import vim in ipython like a normal module
    # More info here:
    # http://vimdoc.sourceforge.net/htmldoc/if_pyth.html#Python
except ImportError:
    print("Script must be run inside vim editor!")
    print("Either quit or use some variables and functions")
    #sys.exit()


def set_up_logging(default_level):
    ### DEBUG -> is the lowest level ###
    #logging.basicConfig(level=default_level)
    # .basicConfig adds a stream handler by default
    msg_format = ("%(asctime)s [  %(levelname)s  ] %(className)s.%(funcName)s "
                  "- %(message)s")
    #msg_format = ("%(asctime)s [  %(levelname)s  ] .%(funcName)s "
    #              "- %(message)s")
    formatter = logging.Formatter(msg_format)

    file_handler = logging.FileHandler(filename="gotoword.log",
                                       mode="w")
    file_handler.setFormatter(formatter)

    IP = 'localhost'
    PORT = logging.handlers.DEFAULT_TCP_LOGGING_PORT
    socket_handler = logging.handlers.SocketHandler(IP, PORT)
    # socket_handler is used to send logs to a socket server in the functional
    # tests file
    sock_msg_format = "%(message)s"
    socket_formatter = logging.Formatter(sock_msg_format)
    socket_handler.setFormatter(socket_formatter)

    # override Logger.makeRecord with a custom one to allow
    # logging facilities used by @log:
    logging.Logger.makeRecord = custom_makeRecord
    logger = logging.getLogger('app')
    logger.setLevel(default_level)
    logger.addHandler(file_handler)
    logger.addHandler(socket_handler)
    return logger


def custom_makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None):
        """
        A factory method which can be overridden in subclasses to create
        specialized LogRecords.

        For instance, 'funcName' is an attribute of LogRecord, created
        automatically and cannot be overwritten except if you use a
        LoggerAdapter instead of Logger.

        With this method, LogRecord attbutes can now be overwritten by keys
        in 'extra' dict.
        Eg:
        >>> logger.debug('test message', extra={'funcName': 'some_fct'})

        """
        rv = logging.LogRecord(name, level, fn, lno, msg, args, exc_info, func)
        if extra is not None:
            for key in extra:
                #if (key in ["message", "asctime"]) or (key in rv.__dict__):
                #    raise KeyError("Attempt to overwrite %r in LogRecord" % key)
                rv.__dict__[key] = extra[key]
        return rv


def log(fn):
    """Adapted the decorator for extracting the name of the function even if
    the function is decorated.
    """
    # uncomment if multiple decorators wrap fn:
    #decorators = get_decorators(fn)
    #fn = decorators[0]

    def wrapper(obj, *args, **kwargs):
        """
        Because fn is wrapped, the function name when logging, will be
        'wrapper':
        >>> fn.__repr__()
        '<unbound method CheckContextState.wrapper>'
        """
        logger.debug('About to run %s with args: %s and kwargs: %s' %
                     (fn.__name__, args[1:], kwargs),
                     extra={'className': strip(getattr(obj, '__class__', "")),
                            'funcName': fn.__name__}
                     )
        # getattr() is needed because not all functions decorated by log()
        # are bounded to a class instance.
        out = fn(obj, *args, **kwargs)
        logger.debug('Done running %s; return value: %s' %
                     (fn.__name__, out),
                     extra={'className': strip(getattr(obj, '__class__', "")),
                            'funcName': fn.__name__}
                     )
        return out
    return wrapper


def get_decorators(function):
    """Get decorators wrapping a function:
    http://schinckel.net/2012/01/20/get-decorators-wrapping-a-function/

    Recursive function that returns a list of functions, last element L[-1]
    is the original function.
    """
    # all python functions have an attr. 'func_closure' which is None or a
    # tuple;
    # If func_closure is None, it means we are not wrapping any other
    # functions -> it's the original function that's being wrapped.
    if not function.func_closure:
        return [function]
    decorators = []
    # Otherwise, we want to collect all of the recursive results for every
    # closure we have.
    for closure in function.func_closure:
        decorators.extend(get_decorators(closure.cell_contents))
    return [function] + decorators


logger = set_up_logging(logging.DEBUG)
#logger = set_up_logging(logging.INFO)
logger.debug("SCRIPT STARTED", extra={'className': ""}),
#logger.debug("logger parameters: \n"
#             "\t\thandlers: %s \n"
#             "\t\tSocketHandler socket %s \n" %
#             (logger.handlers, type(logger.handlers[1].sock)),
#             extra={'className': ""}
#             )
#logger.info("emit_counter: %s" % logger.handlers[1].emit_counter, extra={'className': ""})
"""Flag to indicate that a log server in functional tests file might be up,
so this script is under test and should accept test input using Vim's input
functions."""
TESTING = True if logger.handlers[1].sock else False

from settings import (PKG_PATH, VIM_PLUGIN_PATH, DJANGO_PATH, SCRIPT,
                      HELP_BUFFER, DATABASE)
import utils
# TODO: Can sys.path.insert() be avoided if we have a proper __init__.py file in the
# package?

logger.debug("Following constants are defined: \n"
             "\t\t PKG_PATH: %s \n"
             "\t\t VIM_PLUGIN_PATH: %s \n"
             "\t\t DJANGO_PATH: %s \n"
             "\t\t SCRIPT: %s \n"
             "\t\t HELP_BUFFER: %s \n"
             "\t\t DATABASE: %s \n" %
             (PKG_PATH, VIM_PLUGIN_PATH, DJANGO_PATH, SCRIPT, HELP_BUFFER,
             DATABASE),
             extra={'className': ""}
             )


# move to utils.py
def strip(s):
    """Used to stringify and then strip a class name accessed using
    obj.__class__ so that it is suitable for pretty printing.
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


class App(object):
    """
    This is the main plugin app. Run App.main() method to launch it.
    """
    # create a help_buffer that will hold info retrieved from database, etc.
    # but prevent vim to create buffer in current working dir, by setting an
    # explicit path;
    help_buffer_name = HELP_BUFFER
    # help_buffer is created on the fly, in memory, it doesn't exist on disk,
    # but we specify a full path as its name

    def __init__(self, vim_wrapper=None):
        self.vim_wrapper = vim_wrapper
        self.word = None
        # the current keyword which will be displayed in helper buffer
        self.keyword = None
        self.keyword_context = None
        # we are sure that 'default' context exists in DB
        self.default_context = utils.find_model_object('default',
                                                       utils.Context)
        # a list of strings (test answers) used when script is under test
        self.test_answers = []
        logger.debug("app init", extra={'className': strip(self.__class__)})

    #@log
    def main(self):
        """This is the main entry point of this script."""
        self.vim_wrapper = VimWrapper(app=self)
        # detect if run inside vim editor and if yes, setup help_buffer
        #if not isinstance(self.vim_wrapper.vim, VimServer):
        #    self.vim_wrapper.setup_help_buffer(self.help_buffer_name)
        self.vim_wrapper.setup_help_buffer(self.help_buffer_name)

    @log
    def helper_save(self, context, test_answer):
        """
        this function, if called twice on same keyword(first edit, then an update)
        should know that it doesn't need to create another keyword, just to update
        TODO: write a proper doc string

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

    @log
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
            keyword.delete()
#            STORE.remove(keyword)
#            STORE.commit()
            print("Keyword %s and its definition was removed from database" %
                  kw_name)
        else:
            print("Can't delete a word and its definition if it's not in the database.")

    @log
    def helper_delete_context(self, context):
        "Deletes context from database."
        context = utils.Context.objects.get(name=context)
        if context:
            ctx_name = context.name
            context.delete()
            #STORE.remove(context)
            #STORE.commit()
            print("Context %s was removed from database" % ctx_name)
        else:
            print("Can't delete a context if it's not in the database.")

    @log
    def helper_all_words(self):
        """
        List all keywords from database into help_buffer.
        """
        # select only the keyword names
        names = [kwd.name for kwd in utils.Keyword.objects.all()]
        #result = STORE.execute("SELECT name FROM keyword;")
        # dump from generator into a list
        #l = result.get_all()
        '''
        >>> result
        [u'line', u'canvas', u'color']
        '''
        names.sort()
        '''
        >>> names
        [u'canvas', u'color', u'line']
        '''
        self.vim_wrapper.open_window(self.help_buffer_name, vim)
        logger.debug("names: %s" % names,
                     extra={'className': strip(self.__class__)})
        self.vim_wrapper.help_buffer[:] = names

    @log
    def helper_all_contexts(self):
        """
        List all contexts from database into help_buffer.
        """
        # TODO: this is the same as helper_all_words, create one that is
        # used by both

        # select only the context names
        names = [ctx.name for ctx in utils.Context.objects.all()]
        names.sort()

        self.vim_wrapper.open_window(self.help_buffer_name, vim)
        logger.debug("names: %s" % names,
                     extra={'className': strip(self.__class__)})
        self.vim_wrapper.help_buffer[:] = names

    @log
    def helper_context_words(self, context):
        """
        Displays all keywords that have a definition belonging to this
        context.
        context - a string
        Returns a list of words.
        """

        # locate context into DB and retrieve it as a Context object
        context_obj = utils.Context.objects.get(name=context)
        words = [kwd.name for kwd in context_obj.keyword_set.all()]
        words.sort()

        # TODO: the following can be split into a template, the above is the
        # view
        # add a title on the first line
        self.vim_wrapper.help_buffer[0:0] = [
            "The following keywords have a meaning (definition) in '%s' "
            "context:" % context_obj.name]
        # write data to buffer
        self.vim_wrapper.help_buffer[1:] = words
        return words

    @log
    def helper_word_contexts(self):
        """
        It is used for testing, it should not be available to the user.
        Returns a list of contexts.
        """
        contexts = None
        if self.keyword:
            contexts = [ctx.name for ctx in self.keyword.contexts.all()]
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
            # this branch is not useful since django orm so it should be
            # deleted
            self.vim_wrapper.help_buffer[:] = [
                "The keyword '%s' has information that doesn't belong to any "
                "context" % kw.name]

    def get_test_answer(self, obj):
        try:
            answer = self.test_answers.pop(0)
            return answer
        except IndexError:
            logger.debug("no more test answers left",
                         extra={'className': strip(obj.__class__)})


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

    #@log
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
        user_buf_nr = self.get_active_buffer()

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
        logger.debug("help_buffer is: %s with index: %s" %
                     (self.help_buffer, self.buffer_nr),
                     extra={'className': strip(self.__class__)})

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
    #@log
    def open_window(buffer_name, editor=None):
        """
        Opens a window inside vim editor with an existing buffer whose name is
        buffer name.
        editor - the editor is the global var. vim, but it is given as arg. so
                 that you can import this fct. in other modules, as well, such
                 as the testing module.
        """
        # save current global value of 'switchbuf' in order to restore it later
        # and add 'useopen' value to it
        editor.command("let oldswitchbuf=&switchbuf | set switchbuf+=useopen")

        # open help buffer
        # 'sbuffer' replaces 'split' because we want to use same buffer window if
        # it exists because sbuffer checks the switchbuf option
        editor.command("sbuffer %s" % buffer_name)

        # restore switchbuf to its default value in order not to affect other plugin
        # functionality:
        editor.command("let &switchbuf=oldswitchbuf | unlet oldswitchbuf")

        # prevent vim from focusing the helper window created on top, by
        # focusing the last one used (the window used by user before calling this
        # plugin).
        # CTRL-W p   Go to previous (last accessed) window.
        editor.command('call feedkeys("\<C-w>p")')

    @log
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
        self.open_window(self.parent.help_buffer_name, vim)

        # look for keyword in DB
        keyword = utils.find_model_object(self.parent.word, utils.Keyword)

        if keyword:
            # get contexts this keyword belongs to (specific to ORM); it
            # should be moved to utils
            contexts = keyword.contexts.all()
            ctx_names = [ctx.name for ctx in contexts]
            ctx_names.sort()
            # TODO: keyword.current_context should be set by user if keyword
            # has more contexts
            keyword.current_context = contexts[0]
            logger.debug("word: %s keyword: %s contexts: %s" %
                         (word, keyword, ctx_names),
                         extra={'className': strip(self.__class__)})
            # add a title line at the top;
            # TODO: is the title line removed when kw is updated?
            # maybe it's best to write the content than insert at index 0 the
            # title line, after a md5sum is made, and when reading data, check
            # that title line hasn't changed by checking the md5sum again...
            self.help_buffer[0:0] = ['keyword: %s   contexts: %s' %
                                     (keyword.name, "; ".join(ctx_names))]
            # load content in buffer, previous content is deleted
            ## for now, only content from first context is displayed:
            content_main_ctx = keyword.data_set.get(context=keyword.current_context)
            self.help_buffer[1:] = content_main_ctx.info.splitlines()
        else:
            # keyword doesn't exist, prepare buffer to be filled with user content
            logger.debug("word: %s keyword: %s" %
                         (word, keyword),
                         extra={'className': strip(self.__class__)})

            # write to buffer the small help text
            self.help_buffer[:] = utils.introduction_line(word).splitlines()
            # .splitlines() is used because vim buffer accepts at most one "\n"
            # per vim line
            #keyword = utils.Keyword(name=word)     # conflicts with HelperSave
            keyword = None
        return keyword

    @staticmethod
    def get_active_buffer():
        """
        get the current (active) vim buffer.
        """
        return vim.eval("winbufnr(0)")


class EntryState(object):
    """Makes an initial evaluation of keyword & context and decides which is
    the next state.
    """
    def __init__(self):
        pass

    @log
    def evaluate(self, app, kw, context, test_answer):
        # kw is None if no keyword exists in database
        if (not kw) and (not context):
            logger.debug("not kw and not context", extra={'className': strip(self.__class__)})
            # check out
            # http://www.diveintopython.net/power_of_introspection/and_or.html
            # for The peculiar nature of 'and' and 'or'
            # case when kw doesn't exist in DB and context was not given by
            # user
            # debug flags:
            app.kw = kw
            return ReadContextState()
        elif (not kw) and context:
            logger.debug("not kw and context", extra={'className': strip(self.__class__)})
            # debug flags:
            app.new_context = True
            # case when kw doesn't exist in DB and context was given by user;
            # context was supplied by user to save keyword in that context;
            # check if it exists in the database (if it is not a new one)
            ctx = utils.find_model_object(context, utils.Context)
            # if context not in DB, ctx will be None, create a new context
            if not ctx:
                return CreateContextState()
            app.context = ctx
            # continue with creating and saving a keyword
            return NewKeywordState()
        elif kw and (not context):
            app.kwnotcontext = True
            # kw exists in db, context was not given by user -> update kw info
            # to same context, if context exists, or to no context at all
            logger.debug("kw and not context", extra={'className': strip(self.__class__)})
            # TODO: app.default_context -> actually, it should be keysword's
            # existing context,
            app.keyword_context = kw.current_context
            return UpdateKeywordState()
            #return None
        else:
            # so both kw and context are defined: info will be assigned to
            # other context -> update kw
            app.kwandcontext = True
            #return None
            logger.debug("kw and context", extra={'className': strip(self.__class__)})
            return UpdateKeywordState()


class ReadContextState(object):
    """Prompts user to supply context."""
    @log
    def evaluate(self, app, kw, context, test_answer):
         #input(), inputlist(), getchar() are all Vim blocking methods, cannot
         #be tested well...

        # TODO: put it in a while loop, like any prompt should be
        # eg: while not answer in ('0', '1', '2')

        vim.command("""let user_input = inputlist(["Do you want to specify a context that this definition of the word applies in?", \
                "1. Yes, I will provide a context [1 and press <Enter>]", \
                "2. No, I won't provide a context - use the default one [2 and press <Enter>]", \
                "3. Abort [3 and press <Enter>]" ])
                """)
        # inputlist() is blocking the prompt, waiting for a key from user
        # inputlist() returns '0' if no option is chosen or 1 if first option is
        # chosen

        if TESTING:
            answer = app.get_test_answer(self)
        else:
            answer = vim.eval('user_input')
            answer = answer.strip().lower()
        # use test_answer if it is supplied (when testing)
        #answer = test_answer if test_answer else answer

        # attach this local variable to our app
        app.answer = answer
        logger.debug("answer: %s" % answer,
                     extra={'className': strip(self.__class__)})
        #if answer.startswith('1'):
        #if answer.startswith(' 1'):
        #if answer == '1' or answer.startswith('y'):
        if answer == '1' or answer.startswith('y'):
            # read context ....
            # debug:
            vim.command('echo "\n"')
            vim.command('echomsg "You entered: [\"%s\"]"' % app.answer)
            return CheckContextState()
            #return NewKeywordState()
        elif answer.startswith('2') or answer.startswith('n'):
            app.nocontextno = True        # debug
            return NewKeywordState()
        #elif answer.startswith('0') or answer.startswith('a'):
        elif answer.startswith('3') or answer.startswith('a'):
            # Abort
            # make prompt pass to next line ???!, for pretty printing
            vim.command('echo ""')
            vim.command('echomsg "You entered: [\"%s\"] \n"' % answer)
            #vim.command('echo "You entered test answer: [\"%s\"]"' % test_answer)
            # make prompt pass to next line, for pretty printing
            vim.command('echo ""')
            #vim.command('echo "None is returned"')
            return None
        else:
            # user made a mistake, repeat whole process
            vim.command('echomsg "Invalid option! Type a number from 1 to 3"')
            return self


class NewKeywordState(object):
    "Creates a keyword and stores it to database."
    @log
    def evaluate(self, app, kw, context, test_answer):
        if not context:
            # use the default context
            context = utils.Context.objects.get(name="default")
        app.keyword = utils.create_keyword(app.word, context,
                                           app.vim_wrapper.help_buffer)
        app.keyword.current_context = context
        logger.debug('echomsg "keyword %s saved into context %s"' %
                     (app.keyword.name, context.name),
                     extra={'className': strip(self.__class__)})
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
    @log
    def evaluate(self, app, kw, context, test_answer):
        # capture from stdin the context name
        message = "Enter a one word context name: "
        if TESTING:
            answer = app.get_test_answer(self)
        else:
            answer = get_user_input(message, test_answer)

        # validate it
        context = utils.find_model_object(answer, utils.Context)
        # debug
        logger.debug("kw: %s, context: %s, test_answer: %s, answer: %s" %
                     (app.keyword, context, test_answer, answer),
                     extra={'className': strip(self.__class__)})
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
    @log
    def evaluate(self, app, kw, context, test_answer):
        # capture from stdin the short description of the context
        message = "Enter a short description of the context you just defined: \n"
        if TESTING:
            answer = app.get_test_answer(self)
        else:
            answer = get_user_input(message, test_answer)

        context = utils.Context.objects.create(name=context,
                                               description=answer)
        # debug
        logger.debug("kw: %s, context: %s, test_answer: %s, answer: %s" %
                     (app.keyword, context, test_answer, answer),
                     extra={'className': strip(self.__class__)})
        app.context = context
        #return None
        if kw:
            # user added info for keyword for a new context
            return UpdateKeywordState()
        else:
            return NewKeywordState()


class UpdateKeywordState(object):
    """Updates the information field of a keyword. No states follow after
    this one."""
    @log
    def evaluate(self, app, kw, context, test_answer):
        if context:
            # user wants to add info in another context than the default one
            # check that given context exists
            ctx = utils.find_model_object(context, utils.Context)
            # if context not in DB, ctx will be None, create a new context
            if not ctx:
                return CreateContextState()
            current_context = ctx
        current_context = kw.current_context
        utils.update_keyword(kw, current_context,
                             app.vim_wrapper.help_buffer)
        vim.command('echomsg "Info field of keyword \"%s\" updated"' % kw.name)
        return None


def get_user_input(message, test_answer):
    "Returns the user input from vim, displaying a message at the prompt."
    #if test_answer:
    #    answer = unicode(test_answer)
    #else:
    vim.command('call inputsave()')
    vim.command("let user_input = input('%s')" % message)
    vim.command('call inputrestore()')
    answer = vim.eval('user_input')
    # sanitize it (strip, lowercase, unicode it, etc.)
    answer = unicode(answer.strip().lower())
    return answer


#### MAIN ###

##App.main()
