#!/usr/bin/python

# before running this file, you need to start vim editor as a server:
# $: vim --servername ANDREI ft_test_text

# allow relative imports from modules outside of system path, when this module is
# executed as script:
#if __name__ == '__main__' and __package__ is None:
#    from os import sys, path
#    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from os import sys, path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

import os
import unittest
import time
import multiprocessing
import threading
import pickle
from cStringIO import StringIO


from vimrunner import Server

# gotoword modules
import gotoword
import utils

# start vim server with GUI, it is better this way because it doesn't mess up
# the test terminal
# OR
# start vim server inside terminal

# the following tests are performed on a test database

SERVER = 'gotoword'
TEST_FILE = 'ft_test_text'
PLUGIN_PATH = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
#print(PLUGIN_PATH)
SCRIPT = 'gotoword.vim'

HELP_BUFFER = 'gotoword_buffer'
#HELP_BUFFER = '~/.vim/andrei_plugins/gotoword/helper_buffer'


class TestGotoword(unittest.TestCase):
    #TODO: def setUpClasss() to be run once per class
    def setUp(self):
        # start vim as a server
        self.vim = Server(name=SERVER)
        self.client = self.vim.start_gvim()
        # client = self.vim.start()
        # OR
        #self.client = self.vim.start()
        # $TERM -e sh -c ""
        # xterm -e sh -c "python a-file"

        #def f(q):
        #    client = self.vim.start_gvim()
        #    src = StringIO()
        #    pick = pickle.Pickler(src)
        #    pick.dump(client)
        #    q.put(client)

        #q = multiprocessing.Queue()
        #p = multiprocessing.Process(target=f, args=(q,))
        #p.start()
        #self.client = q.get()
        #p.join()

        # setup your plugin in the vim instance
        self.client.add_plugin(PLUGIN_PATH, SCRIPT)
        # edit test file
        self.client.edit(os.path.join(PLUGIN_PATH, 'gotoword', 'test',
                                      TEST_FILE))
        # prevent vim from opening windows for the same buffer
        #self.client.command("let oldswitchbuf=&switchbuf | set switchbuf+=useopen")
    # create a test DB and populate it with keywords and definitions

    def tearDown(self):
        # close vim server
        #self.vim.quit()
        pass

    def test_command_Helper(self):
        """
        tests if :Helper vim command opens the description of the word under cursor.
        """
        # test a vim buffer is opened for test file
        self.assertTrue(TEST_FILE in self.client.command('ls'))
        # List the user-defined commands that start with Helper
        out = self.client.command('command Helper')
        # out is something like:
        #     Name        Args Range Complete  Definition
        #     Helper      0                    call s:Help_buffer(expand("<cword>"))
        #     HelperAllWords 0                    call s:Helper_all_words()

        # so split at newlines and remove first line (Name Args...)
        out = out.split("\n")[1:]
        out = map(str.strip, out)
        # >>> type(out)
        # list

        # extract the command names by splitting each text line
        cmds = [elem[0] for elem in map(str.split, out)]
        # check all plugin commands exist
        self.assertTrue('Helper' in cmds)
        self.assertTrue('HelperSave' in cmds)
        self.assertTrue('HelperDelete' in cmds)
        self.assertTrue('HelperDeleteContext' in cmds)
        self.assertTrue('HelperAllWords' in cmds)
        self.assertTrue('HelperAllContexts' in cmds)
        self.assertTrue('HelperContextWords' in cmds)

        # call Vim function search("canvas", 'w') to search
        # top-bottom-top
        # for a keyword we know it exists and has a definition in database
        line_nr = self.client.search('canvas', flags='w')
        # if there is no match 0 is returned
        self.assertNotEqual('0', line_nr)

        # test Helper command is working
        self.client.command('Helper')
        time.sleep(1)
        # check the Helper cmd opens gotoword buffer
        buffers = self.client.command('ls!')
        # buffers is similar to:
        # '1 %a   "~/.vim/andrei_plugins/gotoword/gotoword/test/ft_test_text" line 31\n
        #  2u#a   "/home/andrei/.vim/andrei_plugins/gotoword/gotoword_buffer" line 1'
        self.assertTrue(HELP_BUFFER in buffers)
        # get buffer index and name:
        buffers = buffers.split("\n")
        buffers = map(str.strip, buffers)
        buf = [buf_info for buf_info in buffers if HELP_BUFFER in buf_info]
        # buf is a one element list, so
        buf = buf.pop()
        # >>> buf
        # '2u#a   "/home/andrei/.vim/andrei_plugins/gotoword/gotoword_buffer" line 1'
        buffer_index = buf[0]
        buffer_name = buf.split()[2]
        self.assertNotEqual(buffer_name, '')
        # check that the correct help text is displayed in gotoword buffer
        info = self.client.eval('getbufline(%s, 1, "$")' % buffer_index)
        # >>> info
        # 'Define a canvas section in which you can add Graphics instruct...'
        self.assertTrue('Define a canvas section' in info)

        # Check helper buffer is opened in its own window
        window_nr = self.client.eval('bufwinnr(%s)' % buffer_index)
        # if the buffer or no window exists for it, -1 is returned by bufwinnr()
        self.assertNotEqual(int(window_nr), -1)

        ## -------------------------
        # show that 'rgb' doesn't exist in database:
        # call :Helper, input some predefined documentation about the word
        ## -------------------------
        self.keyword_fixture('rgb', buffer_index, buffer_name)

        ## -------------------------
        #  call HelperSave with no context
        ## -------------------------
        # test when user calls :HelperSave with no arguments, we simulate an
        # empty argument with "" and we simulate user chose choice number 1:
        self.client.command('HelperSave "" 1')
        # because in Vim it is difficult to simulate user input when
        # unit testing, the above solution was chosen. The ideal test situation
        # would have been:
        #self.client.command('HelperSave')
        # and we would have simulated that user presses the corresponding
        # keys with self.client.feedkeys('1 \<Enter>')
        ##

        ## when prompt requires to answer, insert "1" -> insert context ->
        #p = multiprocessing.Process(target=self.client.feedkeys, args=("\<Enter>",))
        # TODO: I don't think Process is a solution:
        #p = multiprocessing.Process(target=self.client.type, args=("1\<CR>",))
        #p = multiprocessing.Process(target=self.client.type, args=("y",))
        #p.start()

#        t = threading.Thread(target=self.client.type, args=("y",))
#        t.start()
#        t = threading.Thread(target=type_loop)
#        t.start()
        #time.sleep(1)
        #p.terminate()
        ##
        #self.client.type("\<CR>")

        #self.client.type("1")
        #self.client.type("y")
        #self.client.feedkeys("\<Enter>")
        #self.client.feedkeys('1 \<Enter>')

        ## check definition and keyword are stored to database
        all_words = self.get_all_keywords(buffer_index)
        self.assertTrue('rgb' in all_words)
        time.sleep(1)

        ## -------------------------
        #  test HelperDelete
        ## -------------------------
        ## delete 'rgb' word saved previuosly
        # HelperDelete deletes the keyword on which Helper was called
        # which in this case is 'rgb'
        self.client.command('HelperDelete')
        # check 'rgb' is deleted
        all_words = self.get_all_keywords(buffer_index)
        self.assertTrue('rgb' not in all_words)

        ## -------------------------
        #  call HelperSave with no context and user chooses choice 2
        # which means we wants to provide no context, but save the keyword
        # anyway
        ## -------------------------
        self.keyword_fixture('rgb', buffer_index, buffer_name)
        self.client.command('HelperSave "" 2')
        ## check definition and keyword are stored to database
        all_words = self.get_all_keywords(buffer_index)
        self.assertTrue('rgb' in all_words)
        # ok, now delete it to revert database
        self.client.command('HelperDelete')

        ## -------------------------
        #  call HelperSave with no context and user chooses choice 3
        # which means user cancels :HelperSave, so nothing should happen
        ## -------------------------
        self.keyword_fixture('rgb', buffer_index, buffer_name)
        self.client.command('HelperSave "" 3')
        ## check definition and keyword are not stored to database
        all_words = self.get_all_keywords(buffer_index)
        self.assertFalse('rgb' in all_words)

        ## -------------------------
        #  call HelperSave with context that exists in database
        ## -------------------------
        # call :Helper on word 'rgb'
        self.keyword_fixture('rgb', buffer_index, buffer_name)

        ## we save again the word 'rgb', but we supply a context
        context = "kivy"
        self.client.command('HelperSave %s' % context)
        time.sleep(0.5)
        # Can be deleted?
        # we don't have a prompt for now
        #self.client.type("\<CR>")
        ctx_words = self.get_context_keywords(buffer_index, context)
        self.assertTrue('rgb' in ctx_words)

        # delete 'rgb'
        self.client.command('HelperDelete')

        ## -------------------------
        #  call HelperSave with context that doesn't exist in database
        ## -------------------------
        # call :Helper on word 'rgb'
        self.keyword_fixture('rgb', buffer_index, buffer_name)

        ## we save again the word 'rgb', but we supply a context that doesn't
        # exist yet in database
        context = "newcontext"
        self.client.command('HelperSave %s' % context)
        time.sleep(0.5)
        ctx_words = self.get_context_keywords(buffer_index, context)
        self.assertTrue('rgb' in ctx_words)

        # delete 'rgb'
        self.client.command('HelperDelete')
        # delete context
        self.client.command('HelperDeleteContext %s' % context)
        all_contexts = self.get_all_contexts(buffer_index)
        self.assertFalse(context in all_contexts)

        ## -------------------------
        ## test HelperAllContexts
        ## -------------------------
        all_contexts = self.get_all_contexts(buffer_index)
        # test at least one context exists
        # TODO: contexts should be retrieved from DB and test for equality
        # between the two
        self.assertTrue('python' in all_contexts)
        time.sleep(0.5)

        ## -------------------------
        ## test 'HelperContextWords'
        ## -------------------------
        # get keywords that are defined in the 'python' context using the
        # plugin we are testing
        context = "python"
        ctx_words = self.get_context_keywords(buffer_index, context)
        # get context from DB as a Storm object and count keywords straight
        # from DB table
        ctx = utils.Context.find_context(gotoword.STORE, unicode(context))
        # compare the two numbers
        self.assertEqual(ctx.keywords.count(), len(ctx_words.split("\n")) - 1)
        # len(lines) - 1 because we omit the title line

#    def test_command_HelperSave(self):
#        pass
#
#    def test_command_HelperDelete(self):
#        pass

    ### other utilitary functions
    def get_all_keywords(self, buffer_index):
        "Displays the output of HelperAllWords vim command."
        return self.get_cmd_output('HelperAllWords', buffer_index)

    def get_all_contexts(self, buffer_index):
        "Same as get_all_keywords"
        return self.get_cmd_output('HelperAllContexts', buffer_index)

    def get_context_keywords(self, buffer_index, context):
        """Gets keywords that belong to context with :HelperContextWords cmd.
        Eg. inside Vim editor:
        :HelperContextWords python
        Returns the keywords as a string.
        """
        return self.get_cmd_output('HelperContextWords %s' % context,
                                   buffer_index)

    def get_cmd_output(self, cmd, buffer_index):
        """Eg:
            get_cmd_output('2', 'HelperAllWords')
        """
        self.client.command('%s' % cmd)
        return self.client.eval('getbufline(%s, 1, "$")' % buffer_index)

    def keyword_fixture(self, kword, buffer_index, buffer_name):
        """
        Simulates the user activity inside Vim editor regarding a word that
        doesn't exist yet in the plugin database:
            - how he locates a word he wants more info about
            - how he calls :Helper  cmd on that word
            - the Helper buffer opens but it contains the default lines for
              words that don't exist yet in the database
            - he deletes the default text and writes his own notes about the
              word
        This function is useful to call :Helper on random words in the test
        document.
        Arguments:
            buffer_index    the index of Helper_buffer inside Vim editor
            buffer_name     the Helper_buffer inside Vim editor
        Returns nothing.
        Eg:
            keyword_fixture('canvas', '2', '~/documents/my_file.txt')
        """

        # locate it in current document
        line_nr = self.client.search(kword, flags='w')
        self.assertNotEqual('0', line_nr)

        # display help text in Help buffer about "rgb"
        self.client.command('Helper')

        # check if definition informs user that word doesn't exist in database
        info = self.client.eval('getbufline(%s, 1)' % buffer_index)
        self.assertTrue('"%s" doesn\'t exist' % kword in info)

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
        self.client.insert("Functional tests: This is definition for "
                           "keyword '%s'." % kword)
        # exist Insert mode:
        self.client.normal('<ESC>')


if __name__ == '__main__':
    unittest.main()
