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

from vimrunner import Server

# gotoword modules
from gotoword import STORE
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
    def setUp(self):
        # start vim as a server
        self.vim = Server(name=SERVER)
        self.client = self.vim.start_gvim()
        # client = self.vim.start()

        # setup your plugin in the vim instance
        self.client.add_plugin(PLUGIN_PATH, SCRIPT)
        # edit test file
        self.client.edit(os.path.join(PLUGIN_PATH, 'gotoword', 'test',
                                      TEST_FILE))
        # prevent vim from opening windows for the same buffer
        self.client.command("let oldswitchbuf=&switchbuf | set switchbuf+=useopen")
    # create a test DB and populate it with keywords and definitions

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
        self.assertTrue('HelperAllWords' in cmds)
        self.assertTrue('HelperAllContexts' in cmds)
        self.assertTrue('HelperContextWords' in cmds)

        # call Vim function search("canvas", 'w') to search
        # top-bottom-top
        # for a keyword we know is defined and has a definition in database
        line_nr = self.client.search('canvas', flags='w')
        # if there is no match 0 is returned
        self.assertNotEqual('0', line_nr)

        # test Helper command is working
        self.client.command('Helper')
        time.sleep(1)
        # check the Helper cmd opens gotoword buffer
        buffers = self.client.command('ls!')
        # r is similar to:
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
        # 'Define a canvas section in which you can add Graphics instructions that define how the widget is rendered.'
        self.assertTrue('Define a canvas section' in info)

        # Check helper buffer is opened in its own window
        window_nr = self.client.eval('bufwinnr(%s)' % buffer_index)
        # if the buffer or no window exists for it, -1 is returned by bufwinnr()
        self.assertNotEqual(int(window_nr), -1)

        # -------------------------
        # show that 'rgb' doesn't exist in database
        # -------------------------
        # locate it in current document
        line_nr = self.client.search('rgb', flags='w')
        self.assertNotEqual('0', line_nr)

        # display help text in Help buffer about "rgb"
        self.client.command('Helper')

        # check if definition informs user that word doesn't exist in database
        info = self.client.eval('getbufline(%s, 1)' % buffer_index)
        self.assertTrue('"rgb" doesn\'t exist' in info)

        # -------------------------
        # test HelperSave
        # -------------------------
        # note that cursor is positioned on 'rgb' word located previously;
        # gotoword buffer is readonly to prevent user from accidentally save
        # it with :w or to edit it with i
        self.client.command("set noreadonly")
        # focus/activate Helper buffer by moving to the top window:
        self.client.feedkeys('\<C-w>k')
        self.client.command('buffer! %s' % buffer_index)
        time.sleep(2)
        # delete default text:
        self.client.normal('gg')
        self.client.normal('dG')
        # add a definition for keyword
        self.client.insert("Functional tests: This is definition for "
                           "keyword 'rgb'.")
        # exist Insert mode:
        self.client.normal('<ESC>')
        self.client.command("let oldswitchbuf=&switchbuf | set switchbuf+=useopen")
        ##
        ## call HelperSave with no context
        ##
        self.client.command('HelperSave "" 1')
        time.sleep(1)
        ## when prompt requires to answer, insert "1" -> insert context ->
        #p = multiprocessing.Process(target=self.client.feedkeys, args=("\<Enter>",))
        # TODO: I don't think Process is a solution:
        #p = multiprocessing.Process(target=self.client.type, args=("\<Enter>",))
        #p.start()
        #time.sleep(1)
        #p.terminate()
        self.client.type("\<CR>")
        #self.client.feedkeys("\<Enter>")
        #self.client.eval("feedkeys('%s')" % "1")
        #self.client.command('exe "normal 2 \<CR>"')

        #self.client.feedkeys('1 \<Enter>')
        #self.client.normal('1 \<Enter>')
        ## check definition and keyword are stored in database
        all_words = self.get_all_keywords(buffer_index)
        self.assertTrue('rgb' in all_words)
        time.sleep(1)

        ## -------------------------
        ## test HelperDelete
        ## -------------------------
        ## delete 'rgb' word saved previuosly
        # HelperDelete deletes the keyword on which Helper was called
        # which in this case is 'rgb'
        self.client.command('HelperDelete')
        # check 'rbg' is deleted
        all_words = self.get_all_keywords(buffer_index)
        self.assertTrue('rgb' not in all_words)

        ##
        ## call HelperSave with context
        ##
        #self.client.command('HelperSave kivy 1')
        #time.sleep(1)

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
        context = "python"
        # get keywords that belong to context with :HelperContextWords cmd
        ctx_words = self.get_cmd_output('HelperContextWords %s' % context,
                                        buffer_index)
        # Eg. inside Vim editor:
        # :HelperContextWords python
        # get context from DB as a Storm object and count keywords from table
        ctx = utils.Context.find_context(STORE, unicode(context))
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

    def get_cmd_output(self, cmd, buffer_index):
        """Eg:
            get_cmd_output('2', 'HelperAllWords')
        """
        self.client.command('%s' % cmd)
        return self.client.eval('getbufline(%s, 1, "$")' % buffer_index)

#    def tearDown(self):
#        # close vim server
#        self.vim.quit()




if __name__ == '__main__':
    unittest.main()
