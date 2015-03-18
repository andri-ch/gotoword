# -*- coding: utf-8 -*-

### System libraries ###
import logging
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

# gotoword libraries:
from settings import (PKG_PATH, VIM_PLUGIN_PATH, DJANGO_PATH, SCRIPT,
                      HELP_BUFFER, DATABASE)
import utils
from gotoword_logging import logger_as_decorator_factory
from gotoword_logging import strip


logger = logging.getLogger('vim.gotoword')
log = logger_as_decorator_factory(logger)

"""Set TESTING - flag to indicate that a log server in functional tests file
might be up, so this script is under test and should accept test input using
Vim's input functions."""
TESTING = True if logging.getLogger('vim').handlers[1].sock else False
# socket is created just before the first log message in the entire app
# (including gotoword.vim) is
# created, so TESTING will be False if called before the logger starts sending
# messages
#logger.debug("TESTING: %s" % TESTING, extra={'className': ""})

logger.debug("Following constants are defined: \n"
             "\t\t PKG_PATH: %s \n"
             "\t\t VIM_PLUGIN_PATH: %s \n"
             "\t\t DJANGO_PATH: %s \n"
             "\t\t SCRIPT: %s \n"
             "\t\t HELP_BUFFER: %s \n"
             "\t\t DATABASE: %s \n"
             "\t\t TESTING: %s \n" %
             (PKG_PATH, VIM_PLUGIN_PATH, DJANGO_PATH, SCRIPT, HELP_BUFFER,
             DATABASE, TESTING),
             extra={'className': ""}
             )


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
        """
        TODO: write a proper doc string... explaining the attributes
        """
        self.vim_wrapper = vim_wrapper
        self.word = None
        # the current keyword which will be displayed in helper buffer
        self.keyword = None
        self.keyword_context = None
        # we are sure that 'default' context exists in DB
        self.default_context = utils.find_model_object('default',
                                                       utils.Context)
        # 'links' will store words that will be highlighted and will be
        # considered links that will lead to other notes (like tags)
        #self.links = []
        """
        a list of strings (test answers) used when script is under test; the
        values are added in another script (functional tests file) by sending
        the strings to Vim editor -> check docstring from
        App.get_test_answer.
        """
        self.test_answers = {}
        logger.debug("app init", extra={'className': strip(self.__class__)})

    #@log
    def main(self):
        """This is the main entry point of this script."""
        self.vim_wrapper = VimWrapper(app=self)
        self.vim_wrapper.setup_help_buffer(self.help_buffer_name)
        self.template = Template(self.vim_wrapper, App.help_buffer_name)
        links_observer = LinksObserver(self.template)
        self.template.attach(links_observer)

    @log
    def helper_save(self, context, test_answer):
        """
        If called for a word that doesn't exist into database - for the first
        time - saves it to DB.
        If called for an existing word, it will update it.
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
        '''
        >>> names
        [u'canvas', u'color', u'line']
        '''
        self.template.template(names)
        #self.vim_wrapper.open_window(self.help_buffer_name, vim)
        #logger.debug("names: %s" % names,
        #             extra={'className': strip(self.__class__)})
        #self.vim_wrapper.help_buffer[:] = names
        return names

    @log
    def helper_all_contexts(self):
        """
        List all contexts from database into help_buffer.
        """
        # TODO: this is the same as helper_all_words, create one that is
        # used by both

        # select only the context names
        names = [ctx.name for ctx in utils.Context.objects.all()]
        #names.sort()

        self.template.template(names)
        #logger.debug("names: %s" % names,
        #             extra={'className': strip(self.__class__)})
        return names
        # TODO: can dump logger.debug and just use return names because they
        # get logged by @log anyway

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

        header = [
            "The following keywords have a meaning (definition) in '%s' "
            "context:" % context_obj.name]
        self.template.template(words, header=header)
        return words

    @log
    def helper_word_contexts(self):
        """
        Displays a list of contexts a keyword has definitions in, along with
        one line of each definition.
        """

        #name = "helper_word_contexts"
        summary = []
        # reset global value of links because it is specific to each view
        #self.links = []
        links = []
        if self.keyword:                     # what is the 'else' branch?
            header = ["The keyword '%s' has information belonging to the "
                      "following contexts:" % self.keyword.name]
            #template = self._template_with_header
            contexts = self.keyword.contexts.all()
            for ctx in contexts:
                relation = self.keyword.data_set.get(context=ctx)
                # choose user note if possible, else public note available for
                # all users by default:
                definition = (relation.info if relation.info else
                              relation.info_public)
                one_line_definition = definition.split("\n", 1)[0]
                summary.extend([ctx.name, one_line_definition, "\n"])
                #self.links.append(ctx.name)
                links.append(ctx.name)

            self.template.template(summary, header, links,
                                   syntax_group="GotowordLinks")
            #self._highlight_links(self.links)
            # TODO: disable highlighting when the view is changed
            #vim.command('au BufWinEnter <buffer=%s>  py app._clear_highlight_links("GotowordLinks")' % self.vim_wrapper.buffer_nr)
            #vim.command('au BufWinEnter <buffer=%s>  echo "hold")' % self.vim_wrapper.buffer_nr)
            # next time buffer is reloaded (with :sbuffer, etc.), this autocmd
            # will be used

            # create a mapping only for Helper buffer, buffer must be active when
            # the mapping is created because <buffer> requires it
            #command = 'noremap <buffer> <silent> <2-LeftMouse> :call g:Gotoword_make_links()<cr>'
            # during development, <silent> can be omitted so we can see what
            # function is called when executing this mapping:
            #command = 'noremap <buffer> <silent> <2-LeftMouse> :call g:Gotoword_make_links()<cr>'
            #command = 'noremap <buffer> <silent> <2-LeftMouse> :py app._make_links()<cr>'
            #self.vim_wrapper.toggle_activate(command)
            # TODO: disable links when template is changed
            #command = 'unmap <buffer> <2-LeftMouse>'
            #self.vim_wrapper.toggle_activate(command)

            return [ctx.name for ctx in contexts]
            #self._display_word_contexts(self.keyword, summary)

#    def _highlight_links(self, links):
#        """Highlight the words which are considered links. In Vim, to define
#        the syntax item one would write something like this:
#        syntax match GotowordLinks /Ok\%4l\c\|Cancel\%4l\c/
#        Of course, GotowordLinks needs to be defined already.
#        """
#        for link in links:
#            vim.command('syntax match GotowordLinks /%s\c/' % link)
#
#    def _clear_highlight_links(self, group):
#        """Disables syntax highlighting for a group for the current buffer. Eg:
#        suppose "GotowordLinks is a syntax group,
#        >>> self._clear_highlight_links("GotowordLinks")
#        """
#        command = 'syntax clear %s' % group
#        self.vim_wrapper.toggle_activate(command)
#
#    def _make_links(self):
#        """Calls Helper if word under cursor (<cword>) exists in links."""
#        word = vim.eval('expand("<cword>")')
#        # because of this word expansion, links should be only one word...
#        # TODO: make links to be made of multiple words
#        if word in self.links:
#            vim.command('Helper')
#
#    def _template(self, text):
#        """
#        Opens the help window and displays text in it.
#        text - a list of strings
#
#        Returns nothing.
#        """
#        self.vim_wrapper.open_window(self.help_buffer_name, vim)
#        self.vim_wrapper.help_buffer[:] = text
#
#    def _template_with_header(self, header, text):
#        """
#        Opens the help window and displays a title/header line and the rest
#        of the text.
#        header - a list with one string; can be just a string if one uses
#        help_buffer[0] = header, but help_buffer[0:0] = [header] is used in
#        accordance with help_buffer[1:3] = ['first line', 'second line']
#
#        Returns nothing.
#        """
#        self.vim_wrapper.open_window(self.help_buffer_name, vim)
#        self.vim_wrapper.help_buffer[0:0] = header
#        self.vim_wrapper.help_buffer[1:] = text
#
    def get_test_answer(self, obj):
        """Retrieves first value from App.test_answers list.
        Usage:
        In functional tests file:
        >>> vim_client.command('py app.test_answers.append("test answer")'

        In the app script:
        >>> user_input = App.get_test_answer()
        >>> print(user_input)
        'test_answer'
        """
        try:
            # FIFO queue:
            answer = self.test_answers.pop(0)
            return answer
        except IndexError:
            logger.debug("no more test answers left",
                         extra={'className': strip(obj.__class__)})


class Template(object):
    """Displays/writes text to help buffer in Vim."""
    def __init__(self, vim_wrapper, buf_name):
        self.observers = []
        self.vim_wrapper = vim_wrapper
        self.help_buffer_name = buf_name
        self.header = None
        # header will be a list of strings that will be written to help buffer
        # to form the header lines
        self.links = None
        # links will be a list of words that will behave like hyperlinks
        # TODO: add def for links from App.__init__
        self.syntax_group = None
        # words belonging to syntax_group that will be highlighted as links

    def attach(self, observer):
        self.observers.append(observer)

    def _update_observers(self):
        for observer in self.observers:
            observer()

    #def template(self, *args, **kwargs):
    def template(self, text, header=None, links=None, syntax_group=None):
        """Main method for this class. It chooses the template based on the
        arguments it gets.
        Eg:
        >>> t = Template(wrapper, buf_name)
        >>> t.template(text, header, links)
        """
        self.header = header
        self.links = links
        self.syntax_group = syntax_group
        if header:
            self._template_with_header(text, header, links)
        else:
            self._template(text, links)

    def _template(self, text, links):
        """
        Opens the help window and displays text in it.
        text - a list of strings

        Returns nothing.
        """
        self.vim_wrapper.open_window(self.help_buffer_name, vim)
        self.vim_wrapper.help_buffer[:] = text
        self._update_observers()

    def _template_with_header(self, text, header, links):
        """
        Opens the help window and displays a title/header line and the rest
        of the text.
        header - a list with one string; can be just a string if one uses
        help_buffer[0] = header, but help_buffer[0:0] = [header] is used in
        accordance with help_buffer[1:3] = ['first line', 'second line']

        Returns nothing.
        """
        self.vim_wrapper.open_window(self.help_buffer_name, vim)
        self.vim_wrapper.help_buffer[0:0] = header
        self.vim_wrapper.help_buffer[1:] = text
        self._update_observers()

    def _make_links(self):
        """Calls Helper if word under cursor (<cword>) exists in links."""
        word = vim.eval('expand("<cword>")')
        # because of this word expansion, links should be only one word...
        # TODO: make links to be made of multiple words
        if word in self.links:
            vim.command('Helper')

    def _disable_links(self):
        "Clear mapping for double LMB click in the helper buffer."
        command = 'unmap <buffer> <2-LeftMouse>'
        self.vim_wrapper.toggle_activate(command)


class LinksObserver(object):
    """Enables/disables words in buffer to act like links.
    Eg:
    >>> t = Template(args, kwargs)
    >>> o = LinksObserver(t)
    """
    def __init__(self, template):
        self.template = template
        #self.current_template = template.name
        #self.new_template = None
        self.syntax_group = None
        self.links = None

    def __call__(self):
        "it's called when template has changed from methods of self.template"
        #if self.current_template != self.template.name:
        #    # template has changed
        #    self.current_template = self.template.name
        # undo actions from previous template, like setting links, etc.
        if self.syntax_group:
            # otherwise we get:
            # vim.error: Vim(syntax):E28: No such highlight group name: None
            self._clear_highlight_links(self.syntax_group)
        # get the syntax group of the new template
        self.syntax_group = self.template.syntax_group
        # disable links from previous template
        if self.links:
            # if links exist, a mapping exists (for links)
            # otherwise we get:
            # vim.error: Vim(unmap):E31: No such mapping
            self.template._disable_links()
        # get links of the new template
        self.links = self.template.links
        # set links for the new template
        if not self.template.links:
            return
        self._highlight_links(self.template.syntax_group, self.template.links)
        # map, only for the helper buffer, double LMB click to call _make_links
        # that makes words "click-able"
        command = ('noremap <buffer> <2-LeftMouse> :python '
                   'app.template._make_links()<CR>')
        # one can see existing key maps with
        # :verbose map <2-LeftMouse>
        #command = ('noremap <buffer> <silent> <2-LeftMouse> :python '
        #           'app.template._make_links()<CR>')
        self.template.vim_wrapper.toggle_activate(command)

    def _highlight_links(self, group, links):
        """Highlight the words which are considered links. In Vim, to define
        the syntax item one would write something like this:
        syntax match GotowordLinks /Ok\%4l\c\|Cancel\%4l\c/
        Of course, GotowordLinks needs to be defined already.
        """
        # TODO: does helper buffer need to be the current buffer?
        for link in links:
            vim.command('syntax match %s /%s\c/' % (group, link))

    def _clear_highlight_links(self, group):
        """Disables syntax highlighting for a group for the current buffer. Eg:
        suppose "GotowordLinks" is a syntax group,
        >>> self._clear_highlight_links("GotowordLinks")
        """
        command = 'syntax clear %s' % group
        self.template.vim_wrapper.toggle_activate(command)


class VimWrapper(object):
    # TODO: maybe VimWrapper is not the best name, might create confusion
    #
    """
    It is an alternative to the vim python module, by implementing it as an
    interface to a vim server, all commands and expressions are sent to it.
    """
    def __init__(self, app=None):
        self.app = app
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
        # but for clarity they were split

        # activate the user (initial) buffer
        vim.command("buffer! %s" % user_buf_nr)

    @staticmethod
    #@log
    def open_window(buffer_name, editor=None):
        """
        Opens a window inside vim editor with an existing buffer whose name is
        buffer_name.
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
        self.app.word = word.lower()
        #self.open_window(self.app.help_buffer_name, vim)

        # look for keyword in DB
        keyword = utils.find_model_object(self.app.word, utils.Keyword)

        if keyword:
            # get contexts this keyword belongs to (specific to ORM); it
            # should be moved to utils
            contexts = keyword.contexts.all()
            ctx_names = [ctx.name for ctx in contexts]
            #ctx_names.sort()
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
            #self.help_buffer[0:0] = ['keyword: %s   contexts: %s' %
            #                         (keyword.name, "; ".join(ctx_names))]
            header = ['keyword: %s   contexts: %s' %
                      (keyword.name, "; ".join(ctx_names))]
            # TODO: make it use a template
            # load content in buffer, previous content is deleted
            ## for now, only content from first context is displayed:
            content_main_ctx = keyword.data_set.get(context=keyword.current_context)
            #self.help_buffer[1:] = content_main_ctx.info.splitlines()
            content = content_main_ctx.info.splitlines()
            self.app.template.template(content, header=header)
        else:
            # keyword doesn't exist, prepare buffer to be filled with user content
            logger.debug("word: %s keyword: %s" %
                         (word, keyword),
                         extra={'className': strip(self.__class__)})

            # write to buffer the small help text
            #self.help_buffer[:] = utils.introduction_line(word).splitlines()
            content = utils.introduction_line(word).splitlines()
            self.app.template.template(content)
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

    def toggle_activate(self, cmd):
        """
        Activate/focus the helper buffer, run a cmd, and then activate/focus
        again the last used buffer.
        """
        # store old buffer
        user_buf_nr = self.get_active_buffer()
        # activate the buffer so we can do other operations on it
        vim.command("buffer! %s" % self.buffer_nr)
        # run our operations
        vim.command(cmd)
        # make the old buffer active again
        vim.command("buffer! %s" % user_buf_nr)


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
            answer = app.test_answers['user_input']
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
            vim.command('echo "\n"')
            vim.command('echomsg "You entered: [\"%s\"]"' % app.answer)
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
            answer = app.test_answers['context']
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
            answer = app.test_answers['context_description']
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
