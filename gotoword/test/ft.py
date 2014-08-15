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

from vimrunner import Server

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

        # call Vim function search("canvas", 'w') to search top-bottom
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
        buf = buf.pop()
        # >>> buf
        # '2u#a   "/home/andrei/.vim/andrei_plugins/gotoword/gotoword_buffer" line 1'
        buffer_index = buf[0]
        buffer_name = buf[1]
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

        # check :HelperAllWords works after :Helper or other command
        self.client.command('HelperAllWords')
        time.sleep(1)

        # check all words from database are displayed, and look for a subset
        words = self.client.eval('getbufline(%s, 1, 3)' % buffer_index)
        self.assertEqual(['canvas', 'color', 'test'], words.split("\n"))

#    def test_command_HelperAllWords(self):
#        self.client('HelperAllWords')
#
#        window_nr = sp.check_output("""vim --servername {0} --remote-expr 'bufwinnr({1})'""".format(
#            SERVER, buffer_nr), shell=True).strip()
#        # if the buffer or no window exists for it, -1 is returned by bufwinnr()
#        self.assertNotEqual(int(window_nr), -1)
#
#        # check if some buffer lines correspond
#        info = sp.check_output("""vim --servername {0} --remote-expr 'getbufline({1}, 1, 3)'""".format(
#            SERVER, buffer_nr), shell=True).strip()
#        self.assertEqual(['canvas', 'color', 'test'], info.split())
#
#    def test_command_HelperSave(self):
#        pass
#
#    def test_command_HelperDelete(self):
#        pass

    def tearDown(self):
        # close vim server
        self.vim.quit()


if __name__ == '__main__':
    unittest.main()
