#!/usr/bin/python

# before running this file, you need to start vim editor as a server:
# $: vim --servername ANDREI ft_test_text

# allow relative imports from modules outside of system path, when this module is
# executed as script:
#if __name__ == '__main__' and __package__ is None:
#    from os import sys, path
#    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from os import sys, path
sys.path.append(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))))

#import os
import subprocess as sp
import unittest

import thread
import time

# modules from this plugin
from gotoword import gotoword

app = gotoword.App()
app.main()
# start vim server with GUI, it is better this way because it doesn't mess up
# the test terminal
#thread.start_new_thread(sp.call, ("""vim -g -n --servername gotoword ft_test_text""",), {'shell': True})

# start vim server inside terminal
#thread.start_new_thread(sp.call, ("""vim -n --servername gotoword ft_test_text""",), {'shell': True})
#time.sleep(1)

SERVER = 'gotoword'
TEST_FILE = 'ft_test_text'
PLUGIN_PATH = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
#print(PLUGIN_PATH)
SCRIPT = path.join(PLUGIN_PATH, 'gotoword.vim')

HELP_BUFFER = '~/.vim/andrei_plugins/gotoword/helper_buffer'

# didn't use these global vars all the time because sometimes it is more
# elegant to read the untouched bash commands.


class TestGotoword(unittest.TestCase):
#    def setUp(self):
#        # check if vim server already exists, launch it otherwise
#        #vim_server = sp.check_output("vim --serverlist", shell=True)
#        #if vim_server.strip().lower() != 'gotoword':
#        # start vim server with GUI, it is better this way because it doesn't mess up
#        # the test terminal
#        thread.start_new_thread(sp.call, ("""vim -g -n --servername gotoword ft_test_text""",), {'shell': True})
#        time.sleep(1)
#
#        # check that test file is opened (because tests are based on its
#        # contents) and show the buffer name of the current (active) buffer
#        #filename = sp.check_output("""vim --servername {0} --remote-expr 'bufname("%")'""".format(SERVER), shell=True)
#        #filename = filename.strip()
#        #self.assertEqual(TEST_FILE, filename)
#
#        # source the plugin script
#        sp.call("""vim --servername {0} --remote-send ':source {1} <Enter>'""".format(SERVER, SCRIPT), shell=True)
#        time.sleep(2)

    def test_command_Helper(self):
        """
        tests if :Helper vim command opens the description of the word under cursor.
        """
        # check helper_buffer exists and retrieve its index from the buffer list
        buffer_nr = sp.check_output("""vim --servername {0} --remote-expr 'bufnr("{1}")'""".format(
            SERVER, HELP_BUFFER), shell=True).strip()
        self.assertGreater(int(buffer_nr), 1)
        # helper buffer index is greater than 1 because the file opened for
        # editing usually has index 1

        # -------------------------
        # show definition of 'canvas'; check helper buffer is shown in window
        # -------------------------

        # search for the word in document; position the cursor at the start of the word if
        # it's found
        line_nr = sp.check_output("""vim --servername {0} --remote-expr 'search("{1}")'""".format(
            SERVER, 'canvas'), shell=True).strip()
        self.assertGreater(int(line_nr), 0)
        # line number is 0 if nothing is found by search(); if pattern is
        # found, move the cursor there and return the line number

        # :Helper
        sp.call("""vim --servername {0} --remote-send ':Helper <Enter>'""".format(
            SERVER), shell=True)

        # Check helper buffer is open in its own window
        window_nr = sp.check_output("""vim --servername {0} --remote-expr 'bufwinnr({1})'""".format(
            SERVER, buffer_nr), shell=True).strip()
        # if the buffer or no window exists for it, -1 is returned by bufwinnr()
        self.assertNotEqual(int(window_nr), -1)

        # check if definition corresponds to its word
        info = sp.check_output("""vim --servername {0} --remote-expr 'getbufline({1}, 1)'""".format(
            SERVER, buffer_nr), shell=True).strip()
        self.assertEqual('Define a canvas', info[:15])

        # -------------------------
        # show that 'rgb' doesn't exist in database
        # -------------------------
        # locate it in current document
        line_nr = sp.check_output("""vim --servername {0} --remote-expr 'search("{1}")'""".format(
            SERVER, 'rgb'), shell=True).strip()
        self.assertGreater(int(line_nr), 0)

        # :Helper
        sp.call("""vim --servername {0} --remote-send ':Helper <Enter>'""".format(
            SERVER), shell=True)

        window_nr = sp.check_output("""vim --servername {0} --remote-expr 'bufwinnr({1})'""".format(
            SERVER, buffer_nr), shell=True).strip()
        # if the buffer or no window exists for it, -1 is returned by bufwinnr()
        self.assertNotEqual(int(window_nr), -1)

        # check if definition corresponds to its word
        info = sp.check_output("""vim --servername {0} --remote-expr 'getbufline({1}, 1)'""".format(
            SERVER, buffer_nr), shell=True).strip()
        self.assertEqual('"rgb" doesn\'t exist', info[12:31])

        # :HelperAllWords
        sp.call("""vim --servername {0} --remote-send ':HelperAllWords <Enter>'""".format(
            SERVER), shell=True)

        window_nr = sp.check_output("""vim --servername {0} --remote-expr 'bufwinnr({1})'""".format(
            SERVER, buffer_nr), shell=True).strip()
        # if the buffer or no window exists for it, -1 is returned by bufwinnr()
        self.assertNotEqual(int(window_nr), -1)

        # check if definition corresponds to its word
        info = sp.check_output("""vim --servername {0} --remote-expr 'getbufline({1}, 1, 3)'""".format(
            SERVER, buffer_nr), shell=True).strip()
        self.assertEqual(['canvas', 'color', 'test'], info.split())

        time.sleep(5)

    def test_command_HelperAllWords(self):
        buffer_nr = sp.check_output("""vim --servername {0} --remote-expr 'bufnr("{1}")'""".format(
            SERVER, HELP_BUFFER), shell=True).strip()
        self.assertGreater(int(buffer_nr), 1)

        # :HelperAllWords
        sp.call("""vim --servername {0} --remote-send ':HelperAllWords <Enter>'""".format(
            SERVER), shell=True)

        window_nr = sp.check_output("""vim --servername {0} --remote-expr 'bufwinnr({1})'""".format(
            SERVER, buffer_nr), shell=True).strip()
        # if the buffer or no window exists for it, -1 is returned by bufwinnr()
        self.assertNotEqual(int(window_nr), -1)

        # check if some buffer lines correspond
        info = sp.check_output("""vim --servername {0} --remote-expr 'getbufline({1}, 1, 3)'""".format(
            SERVER, buffer_nr), shell=True).strip()
        self.assertEqual(['canvas', 'color', 'test'], info.split())
#
#    def test_command_HelperSave(self):
#        pass
#
#    def test_command_HelperDelete(self):
#        pass

    def tearDown(self):
        # close vim server
        sp.call("""vim --servername gotoword --remote-send ':qa! <Enter>'""", shell=True)


if __name__ == '__main__':
    unittest.main()
