#!/usr/bin/python

"""
This file contains functional tests for "gotoword" python app.
It uses pytest python module, not the default unittest, because in python 2.x
it is more difficult to run and organize functional tests.

From the command line, it should be run like this:
$: py.test -v ft.py
"""

# allow relative imports from modules outside of system path, when this module is
# executed as script:
#if __name__ == '__main__' and __package__ is None:
#    from os import sys, path
#    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from os import sys, path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

import os
#import unittest
import pytest
import time

from vimrunner import Server

# gotoword modules
import gotoword
import utils


SERVER = 'gotoword'
TEST_FILE = 'ft_test_text'
PLUGIN_PATH = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
#print(PLUGIN_PATH)
SCRIPT = 'gotoword.vim'

HELP_BUFFER = 'gotoword_buffer'
#HELP_BUFFER = '~/.vim/andrei_plugins/gotoword/helper_buffer'


@pytest.fixture(scope="class")
def server_setup(request):
    request.cls.vim = Server(name=SERVER)
    # request.cls will become self when a test class is instantiated, so
    # attributes will be added to self.
    request.cls.client = request.cls.vim.start_in_other_terminal()
    request.cls.client.add_plugin(PLUGIN_PATH, SCRIPT)
        # edit test file
    request.cls.client.edit(os.path.join(PLUGIN_PATH, 'gotoword', 'test',
                                         TEST_FILE))
    buffers = request.cls.client.command('ls!')
    # buffers is similar to:
    # '1 %a   "~/.vim/andrei_plugins/gotoword/gotoword/test/ft_test_text" line 31\n
    #  2u#a   "/home/andrei/.vim/andrei_plugins/gotoword/gotoword_buffer" line 1'
    if not HELP_BUFFER in buffers:
        raise RuntimeError("initialization failed, no help buffer exists.")

    # get buffer index and name:
    buffers = buffers.split("\n")
    buffers = map(str.strip, buffers)
    buf = [buf_info for buf_info in buffers if HELP_BUFFER in buf_info]
    # buf is a one element list, so
    buf = buf.pop()
    # >>> buf
    # '2u#a   "/home/andrei/.vim/andrei_plugins/gotoword/gotoword_buffer" line 1'

    # make buffer_index persistent across test cases -> make it a class
    # variable, not an instance variable, because new instances are created
    # for each test case:
    request.cls.buffer_index = buf[0]
    #TestGotoword.buffer_index = buf[0]
    request.cls.buffer_name = buf.split()[2]
    if request.cls.buffer_name is '':
            raise RuntimeError("buffer name is empty, so no buffer exists")


@pytest.mark.usefixtures("server_setup")
@pytest.mark.incremental
class TestGotoword():
    def setUp(self):
        pass

    def tearDown(self):
        # close vim server
        #self.vim.quit()
        pass

    @pytest.mark.testit
    def test_test_file_is_opened(self):
        "Test a vim buffer is opened with the test file."
        #self.assertTrue(TEST_FILE in self.client.command('ls'))
        assert (TEST_FILE in self.client.command('ls'))

    @pytest.mark.testit
    def test_all_Helper_commands_exist(self):
        """
        tests if :Helper vim command opens the description of the word under cursor.
        """
        # List the user-defined commands that start with Helper
        out = self.client.command('command Helper')
        # out is something like:
        #  Name           Args Range Complete  Definition
        #  Helper          0                   call s:Help_buffer(expand("<cword>"))
        #  HelperAllWords  0                   call s:Helper_all_words()

        # so split at newlines and remove header line (Name Args Range ...)
        out = out.split("\n")[1:]
        out = map(str.strip, out)
        # >>> type(out)
        # list

        # extract the command names by splitting each text line
        cmds = [elem[0] for elem in map(str.split, out)]
        # check all plugin commands exist
        assert ('Helper' in cmds)
        assert ('HelperSave' in cmds)
        assert ('HelperDelete' in cmds)
        assert ('HelperDeleteContext' in cmds)
        assert ('HelperAllWords' in cmds)
        assert ('HelperAllContexts' in cmds)
        assert ('HelperContextWords' in cmds)
        assert ('HelperWordContexts' in cmds)

    @pytest.mark.testit
    def test_command_Helper_on_existing_keyword(self):
        # call Vim function search("canvas", 'w') to search
        # top-bottom-top
        # for a keyword we know it exists and has a definition in database
        line_nr = self.client.search('canvas', flags='w')
        # if there is no match 0 is returned
        assert '0' != line_nr

        # test Helper command is working
        self.client.command('Helper')
        time.sleep(1)
        # check that the correct help text is displayed in gotoword buffer
        #info = self.client.eval('getbufline(%s, 1, "$")' % self.buffer_index)
        info = self.client.eval('getbufline(%s, 1, "$")' % TestGotoword.buffer_index)
        # >>> info
        # 'Define a canvas section in which you can add Graphics instruct...'
        assert ('Define a canvas section' in info)

        # Check helper buffer is opened in its own window
        window_nr = self.client.eval('bufwinnr(%s)' % TestGotoword.buffer_index)
        # if the buffer or no window exists for it, -1 is returned by bufwinnr()
        assert (int(window_nr) != -1)

    #@pytest.mark.testit
    def test_HSave_new_kword_no_context_but_new_one_given_when_prompted(self):
        ## -------------------------
        # show that 'rgb' doesn't exist in database:
        # call :Helper, input some predefined documentation about the word
        ## -------------------------
        self.keyword_fixture('new kw no context but given', 'rgb',
                             self.buffer_index, self.buffer_name)

        ## -------------------------
        #  call HelperSave with no context
        ## -------------------------
        # test when user calls :HelperSave with no arguments, we simulate an
        # empty argument with "" and we simulate user chose choice number 1:
        self.client.command('HelperSave "" 0')
        # because in Vim it is difficult to simulate user input when
        # unit testing, the above solution was chosen. The ideal test situation
        # would have been:
        #self.client.command('HelperSave')
        # and we would have simulated that user presses the corresponding
        # keys with self.client.feedkeys('1 \<Enter>')
        ##
        #self.client.feedkeys('2 \<Enter>')

        time.sleep(0.2)
        ## check definition and keyword are stored to database
        all_words = self.get_all_keywords(self.buffer_index)
        time.sleep(0.2)
        assert ('rgb' in all_words)
        # check that 'rgb' has a context it belongs to
        word_contexts = self.get_keyword_contexts(self.buffer_index)
        time.sleep(0.2)
        assert ('0' in word_contexts)
        # revert
        self.client.command('HelperDelete')
        time.sleep(0.2)

    def test_HS_new_kw_no_context_but_existing_one_given_when_prompted(self):
        pass
        # TODO: make HelperSave take a test answer other than 0, make it take
        # multiple test answers, for each stage (maybe a list or a dict)
        # it should be an immutable container, to mimic that stages are not
        # mutable

    #@pytest.mark.testit
    def test_HelperDelete_on_current_keyword(self):
        ## -------------------------
        #  test HelperDelete
        ## -------------------------
        ## delete 'rgb' word saved previuosly
        # HelperDelete deletes the keyword on which Helper was called
        # which in this case is 'rgb'
        self.client.command('HelperDelete')
        # check 'rgb' is deleted
        all_words = self.get_all_keywords(self.buffer_index)
        assert ('rgb' not in all_words)

    #@pytest.mark.testit
    def test_HelperSave_new_keyword_no_context_not_given_when_prompted(self):
        ## -------------------------
        #  call HelperSave with no context and user chooses choice 1
        # which means he wants to provide no context, but save the keyword
        # anyway
        ## -------------------------
        self.keyword_fixture('new kw no context but not given', 'rgb',
                             self.buffer_index, self.buffer_name)
        self.client.command('HelperSave "" 1')
        ## check definition and keyword are stored to database
        all_words = self.get_all_keywords(self.buffer_index)
        assert ('rgb' in all_words)
        # check 'rgb' is saved with no context
        word_contexts = self.get_keyword_contexts(self.buffer_index)
        assert ("doesn't belong" in word_contexts)
        # ok, now delete it to revert database
        self.client.command('HelperDelete')

    def test_HelperSave_new_keyword_no_context_but_we_cancel_saving(self):
        ## -------------------------
        #  call HelperSave with no context and user chooses choice 3
        # which means user cancels :HelperSave, so nothing should happen
        ## -------------------------
        self.keyword_fixture('new kw no context but cancel', 'rgb',
                             self.buffer_index, self.buffer_name)
        self.client.command('HelperSave "" 2')
        ## check definition and keyword are not stored to database
        all_words = self.get_all_keywords(self.buffer_index)
        assert ('rgb' not in all_words)

    #@pytest.mark.testit
    def test_HelperSave_new_keyword_and_existing_context_given(self):
        ## -------------------------
        #  call HelperSave with context that exists in database
        ## -------------------------
        # call :Helper on word 'rgb'
        self.keyword_fixture('new kw and old context given', 'rgb',
                             self.buffer_index, self.buffer_name)

        ## we save the word 'rgb', but we supply a context
        context = "kivy"
        self.client.command('HelperSave %s' % context)
        time.sleep(0.5)
        # Can be deleted?
        # we don't have a prompt for now
        #self.client.type("\<CR>")
        ctx_words = self.get_context_keywords(self.buffer_index, context)
        assert ('rgb' in ctx_words)

        # delete 'rgb'
        self.client.command('HelperDelete')

    def test_HelperSave_new_keyword_and_new_context_given(self):
        ## -------------------------
        #  call HelperSave with context that doesn't exist in database
        ## -------------------------
        # call :Helper on word 'rgb'
        self.keyword_fixture('new kw and context given', 'rgb',
                             self.buffer_index, self.buffer_name)

        ## we save again the word 'rgb', but we supply a context that doesn't
        # exist yet in database
        context = "newcontext"
        self.client.command('HelperSave %s' % context)
        time.sleep(0.5)
        ctx_words = self.get_context_keywords(self.buffer_index, context)
        assert ('rgb' in ctx_words)

        # delete 'rgb'
        self.client.command('HelperDelete')
        # delete context
        self.client.command('HelperDeleteContext %s' % context)
        all_contexts = self.get_all_contexts(self.buffer_index)
        assert (context not in all_contexts)

    @pytest.mark.testit
    def test_HelperSave_update_info_for_keyword_to_same_context(self):
        '''test that info belonging to a context is updated (so keyword
        exists).'''
        kword = 'rgb'
        self.keyword_fixture('update_info_for_keyword_with_existing_context',
                             kword, self.buffer_index, self.buffer_name)
        self.client.write_buffer("line('$') + 1",
                                 "test update - add after last line")
        time.sleep(0.3)
        self.client.command('HelperSave "" 0')
        time.sleep(0.1)

        # check info is updated, so first locate it in current document
        line_nr = self.client.search(kword, flags='w')
        assert 0 != line_nr

        self.client.command('Helper')
        time.sleep(0.1)
        # focus helper buffer, because read_buffer() acts on current buffer

        info = self.client.read_buffer("'$'", buf=self.buffer_index)
        time.sleep(0.2)       # might be obsolete
        # debug in Vim
        #self.client.command('py app.info = "%s"' % info)
        assert ("test update - add after last line" == info)
        # delete 'rgb'
        self.client.command('HelperDelete')

    def test_HelperAllContexts(self):
        ## -------------------------
        ## test HelperAllContexts
        ## -------------------------
        all_contexts = self.get_all_contexts(self.buffer_index)
        # test at least one context exists
        # TODO: contexts should be retrieved from DB and test for equality
        # between the two
        assert ('python' in all_contexts)
        time.sleep(0.5)

    def test_HelperContextWords(self):
        ## -------------------------
        ## test 'HelperContextWords'
        ## -------------------------
        # get keywords that are defined in the 'python' context using the
        # plugin we are testing
        context = "python"
        ctx_words = self.get_context_keywords(self.buffer_index, context)
        # get context from DB as a Storm object and count keywords straight
        # from DB table
        ctx = utils.Context.find_context(gotoword.STORE, unicode(context))
        # compare the two numbers
        assert (ctx.keywords.count() == len(ctx_words.split("\n")) - 1)
        # len(lines) - 1 because we omit the title line

    ### other utilitary functions ###
    #################################
    def get_cmd_output(self, cmd, buffer_index):
        """Eg:
            get_cmd_output('2', 'HelperAllWords')
        Returns a string that contains the text from vim buffer and it can be
        split at newlines to obtain a list of vim lines.
        """
        self.client.command('%s' % cmd)
        return self.client.eval('getbufline(%s, 1, "$")' % buffer_index)

    def get_all_keywords(self, buffer_index):
        "Displays the output of HelperAllWords vim command."
        return self.get_cmd_output('HelperAllWords', buffer_index)

    def get_all_contexts(self, buffer_index):
        "Displays the output of HelperAllContexts vim command."
        return self.get_cmd_output('HelperAllContexts', buffer_index)

    def get_context_keywords(self, buffer_index, context):
        """Gets keywords that belong to context with :HelperContextWords cmd.
        Eg. inside Vim editor:
        :HelperContextWords python
        Returns the keywords as a string.
        """
        return self.get_cmd_output('HelperContextWords %s' % context,
                                   buffer_index)

    def get_keyword_contexts(self, buffer_index):
        """Displays the output of HelperWordContexts vim command."""
        return self.get_cmd_output('HelperWordContexts', buffer_index)

    def keyword_fixture(self, fixture_name, kword, buffer_index, buffer_name):
        """
        This function is useful to call :Helper on random words in the test
        document.

        It simulates the user flow inside Vim editor regarding a word that
        doesn't exist yet in the plugin database:
            - how he locates a word he wants more info about
            - how he calls :Helper  cmd on that word
            - the Helper buffer opens but it contains the default lines for
              words that don't exist yet in the database
            - he deletes the default text and writes his own notes about the
              word
        Arguments:
            buffer_index    the index of Helper_buffer inside Vim editor
            buffer_name     the Helper_buffer inside Vim editor
        Returns nothing.
        Eg:
            keyword_fixture('define canvas', 'canvas', '2', '~/my_file.txt')
        """

        # locate it in current document
        line_nr = self.client.search(kword, flags='w')
        assert 0 != line_nr
        #self.assertNotEqual('0', line_nr)

        # display help text in Help buffer about "rgb"
        self.client.command('Helper')

        # check if definition informs user that word doesn't exist in database
        info = self.client.eval('getbufline(%s, 1)' % buffer_index)
        assert ('"%s" doesn\'t exist' % kword in info)

        # note that cursor is positioned on kword word located previously in
        # test document;
        # gotoword buffer is readonly to prevent user from accidentally save
        # it with :w or to edit it with i, but we want to add text to it:
        self.client.command("set noreadonly")

        ### focus Helper_buffer window
        # all functions and classes from gotoword expect to have 'vim' python
        # module binding to Vim editor as a global variable, but we substitute
        # it with a partially compatible Vim server client
        gotoword.vim = self.client
        # focus window:
        gotoword.VimWrapper.open_window(buffer_name)
        ###

        # pause a bit to allow visual inspection, if needed
        time.sleep(1)
        # delete default text:
        self.client.normal('gg')
        self.client.normal('dG')
        # add a definition for keyword
        self.client.insert("Test name '%s': This is definition for "
                           "keyword '%s'." % (fixture_name, kword))
        # exist Insert mode:
        self.client.normal('<ESC>')


#if __name__ == '__main__':
#    unittest.main()
