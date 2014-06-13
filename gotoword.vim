" Vim global plugin for displaying info about the word under cursor
" Last Change:	2014 Ian 18
" Maintainer:	Andrei Chiver  <andreichiver@gmail.com>
" License:	This file is placed in the public domain.

"if exists("g:loaded_gotoword")
"  finish
"endif
"let g:loaded_gotoword = 1


" plugin that opens a help file in a separate buffer for the  word under 
" cursor and displays information about it.
" All this information is retrieved from a database.
" Usually the word belongs to a context, and same word can belong to different
" contexts, so it can have a definition for each context it belongs to.
"
"WHAT IS IT USEFUL FOR?
" TODO: write some more use cases
" Mainly, you can use it as a quick reminder.
" For example, when you're inside a document, you don't remember the 
" meaning/all the details about a word/all implications for that work, but you 
" did write something about it a while ago, so you can open up the note.
"
"
"
"
"
" RUN THE PLUGIN
" test if plugin is loaded at vim startup by typing/calling the Helper command
" :Helper 
" If you get a message that no Helper command is defined, type:
" :source path_to_the_plugin
" To check if script sourced, call Helper cmd again

" DETAILED DESCRIPTION
"
" When I open a document, I want vim to highlight words that this plugin has
" into its database.
" Highlighting should be a toggle on/off property, when too much of it, it is
" annoying. 
" So when I want to read info about a key word, I put my cursor on the word and
" type :Helper
" Contexts:
"   - should be chainable: filename extension -> *.kv, *.py, should provide
"   first context, then the keyword, etc.
"
" At startup, the plugin should detect the contexts in the file and  load the 
" keywords from database that exist in those contexts and look for
" them in the active document(index the document?)
" So, vim editor could search the buffer for each of the words belonging to 
" a context and highlight those matches or to say somewhere that keywords 
" exist in the buffer. Then, the user can further open the help_buffer to 
" see those words or enable highlighting of those words. 
" Check out the script: 
" Mark : a little script to highlight several words in different colors 
" simultaneously:
" http://www.vim.org/scripts/script.php?script_id=1238
"
"TODO: create a function to list all keywords in db in the help_buffer
"TODO: figure out how to change Keyword class in order to introduce contexts
" figure how if context is a table with different context columns, if it's a
" one to many or many to one relation, etc.



if !has('python')
    echo "Error: Required vim compiled with +python"
    echo "To check the python configuration, type in a terminal the following: "
    echo "vim --version | grep --color '+python'"
    finish                             " like python's sys.exit()
endif

" production mode
" function s:Initialize_gotoword(word)              
" fct name always starts with uppercase
" development mode
function! s:Initialize_gotoword()             
" this function is run only once, it creates a helper_buffer, so helper_buffer 
" should not be deleted(wiped) with :bwipe

python << EOF

### System libraries ###
import os.path
import sys
import vim
# the vim module contains everything we need to interface with vim from
# python, but only when python is used in vim plugins. 
# can't import vim in ipython, maybe with some tricks

VIM_FOLDER = os.path.expanduser('~/.vim')
# os.path.expanduser turns '~' into an absolute path, because os.path.abspath can't!
PLUGINS_FOLDER = 'andrei_plugins'
# PLUGINS_FOLDER can be any of "plugin", "autoload", etc. 
PLUGIN_NAME = 'gotoword'
PYTHON_PACKAGE = 'gotoword'
# plugin's database that holds all the keywords and their info
DB_NAME = 'keywords.db'
DATABASE = os.path.join(VIM_FOLDER, PLUGINS_FOLDER, PLUGIN_NAME, DB_NAME)

### Third party libs ###
from storm.locals import create_database, Store, Int, Unicode

### Own libraries ###
# NOTICE
# the python path when these lines are executed is the path of the currently 
# active buffer (vim.current.buffer) in which this code is executed, NOT the 
# path of this vim script.
# So, to import our own libs, we have to add them to python path.
sys.path.insert(1, os.path.join(VIM_FOLDER, PLUGINS_FOLDER, PLUGIN_NAME, PYTHON_PACKAGE))
# Eg. '/home/username/.vim/a_plugins_dir/gotoword/gotoword'
from gotoword import *
import gotoword_state_machine


### MAIN ### 

database = create_database('sqlite:' + DATABASE)
# Eg: DATABASE = 'sqlite:/home/andrei/.vim/andrei_plugins/gotoword/keywords.db'
store = Store(database)

help_window = None
# create a help_buffer that will hold info retrieved from database, etc.
#help_buffer = os.path.join(os.getcwd(), "andrei_helper")
# prevent vim to create buffer in current working dir, by setting an explicit 
# path; this way, python imports from our own library are easier
help_buffer_name = os.path.join(VIM_FOLDER, PLUGINS_FOLDER, PLUGIN_NAME, "helper_buffer")
# help_buffer is created on the fly, it doesn't exist on disk, but we 
# specify a full path as its name

# find and store the help window's index for further reference to it
# if the user needs help on other words, you just change the window buffer
# or, update the current buffer, so help_window might not be needed
for win in vim.windows:
    if win.buffer.name == help_buffer_name:
        # if already there is a window which displays the help buffer
        help_window = win
        #win.buffer.append("Help window: %s" % help_window)   

if not help_window:
    try:
    # open the andrei_help buffer in a new window
    #vim.command("exe 'silent new' escape('%s', '\ ')" % help_buffer_name)
    #vim.command("exe 'silent new' escape('%s', '\ ')" % help_buffer_name)
        # opens file in same win
        vim.command("exe 'split %s'" % help_buffer_name) 
        #vim.command("exe 'set readonly'")                   # or 'set ro'
        # by setting buffer readonly, we want user to prevent from saving it 
        # on harddisk with :w cmd, instead we want user to update the 
        # database with HelperUpdate vim cmd or HelperSave
    except vim.error:
        print("can't create %s buffer, it already exists." % help_buffer_name)

"""
map buffer names to vim.buffers indices for easier access from python 
(indices differ when compared to vim buffers' indices, but the name is the 
same, so we need to access buffers by name)
"""
py_buffers = {}
for index, b in enumerate(vim.buffers):
    py_buffers[b.name] = index + 1
    # vim indexing starts from 1, but index starts from 0
    # >>> print(py_buffers)
    #{'/home/andrei/.vim/andrei_plugins/andrei_helper': 1, '/home/andrei/bash_exp/-MiniBufExplorer-': 2, '/home/andrei/bash_exp/sugarsync.kv': 0}

help_buffer = vim.buffers[py_buffers[help_buffer_name]]
# help_buffer should
EOF

let g:gotoword_initialized = 1
endfunction



if !exists(":Helper")
  " development mode
  command -nargs=0 Helper call Help_buffer(expand("<cword>"))
  " production mode
  "command -nargs=0 Helper call s:Help_buffer(expand("<cword>"))
endif
" We define the command :Helper to call the function Help_buffer. 
" The -nargs argument states how many arguments the command will take.
" :call Help_buffer(expand("<cword>"))   " call fct with word under the cursor 


" production mode
"function s:Help_buffer(word)              " fct name always starts with uppercase
" development mode
function! Help_buffer(word)              " fct name always starts with uppercase

call s:Initialize_gotoword() 

python << EOF

# get function argument
word = vim.eval("a:word")            # get argument by name
# word = vim.eval("a:1")             # get argument by position (first one)

# make it unicode, for python2.x, this is what is stored in the db
word = unicode(word)
# make it case-insensitive
word = word.lower()
# look for keyword in DB
keyword = find_keyword(store, word)

if keyword:
    # load content in buffer, previous content is deleted
    help_buffer[:] = keyword.info.splitlines()
    vim.command("exe 'set readonly'")                   # or 'set ro'
else:
    # keyword doesn't exist, prepare buffer to be filled with user content
    vim.command("exe 'set noro'")                       # set noreadonly
    # write to buffer the small help text
    help_buffer[:] = introduction_line(word).splitlines()
    vim.command("exe 'set readonly'")                   # or 'set ro'
    # .splitlines() is used because vim buffer accepts at most one "\n" 
    # per vim line

### DEBUG ###
#help_buffer.append("%s" % help_buffer)
###

# close database connection
store.close()
EOF

let g:loaded_Help_buffer = 1
endfunction



if !exists(":HelperSave")
  " developer mode
  "command -nargs=0 HelperSave call Helper_save()
  command -nargs=? HelperSave call Helper_save(<f-args>)   
  " ? means zero or one argument
  " production mode
  "command -nargs=? HelperSave call s:Help_save()
endif

" This command saves to DB the helper buffer, which should already exist
" Eg. :HelperSave            - keyword is in db, so context is known
"     :HelperSave kivy       - create new keyword, kivy is the context

" production mode
"function s:Helper_save()              " fct name always starts with uppercase
" development mode
function! Helper_save(...)             " fct has a variable number of args
    " To redefine a function that already exists, use the ! 
    " This way, we reload for each subsequent function call
    if !exists("g:loaded_Help_buffer")
      echo "There is nothing to save. HelperSave needs to be called after Helper command."
      finish
    endif

python << EOF

# python imports from vim functions run previously are still available, as 
# well as the variables defined.

# this function, if called twice on same keyword(first edit, then an update) 
# should know that it doesn't need to create another keyword, just to update

# reopen database connection
store._connection = store.get_database().connect()

# initialize state machine to handle case 00

#m = gotoword_state_machine.StateMachine()
#m.add_state("Start", start_transitions)
#m.add_state("read_context_state", read_context_transitions)
#m.add_state("end_state", end_state, end_state=1)
gotoword_state_machine.m.set_start("Start")
#m.run('start')

# get first positional argument
try:
    context = vim.eval("a:1")
    context = unicode(context)
except vim.error:
    context = ''

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

store.close()
EOF
endfunction



if !exists(":HelperDelete")
  " developer mode
  command -nargs=0 HelperDelete call Helper_delete()
  " production mode
  "command -nargs=0 HelperDelete call s:Helper_delete()
endif


" production mode
"function s:Helper_delete()
" development mode
function! Helper_delete()
" TODO: should take optional positional arguments indicating the context
" One could delete the definition for one context while keeping the others

" TODO: what plugin functions need to be run first so that this function can
" be called? 

python << EOF

# this function deletes from DB the keyword whose content in help_buffer 
# is displayed;
# in the future, it could delete from DB the word under cursor.

# python imports from vim functions run previously are still available, as 
# well as the variables defined.

# reopen database connection
store._connection = store.get_database().connect()

# TODO: prompt a question for user to confirm if he wants keyword with name x 
# to be deleted. 
# Edge case: user calls Help_buffer on word, but word doesn't exist so he 
# starts filling the definition, but he changes his mind and wants to delete 
# the keyword - calls :HelperDelete, because he thinks kw in the db, but it 
# isn't, so db will throw a python storm error. Provide a backup for this...

if keyword:
    kw_name = keyword.name
    store.remove(keyword)
    store.commit()
    print("Keyword %s and its definition removed from database" % kw_name)
else:
    print("Can't delete a word and its definition if it's not in the database.")

store.close()

EOF
endfunction


" TODO: create a HelperDeleteContext and/or HelperDefineContext or
" HelperContext delete/new/list         new or save or add; which one?


if !exists(":HelperAllWords")
  " developer mode
  command -nargs=0 HelperAllWords call Helper_all_words()
  " production mode
  "command -nargs=0 HelperAllWords call s:Helper_all_words()
endif


" production mode
"function s:HelperAllWords()
" development mode
function! Helper_all_words()
" this function displays all keywords from DB in help_buffer, sorted in 
" alphabetical order

" TODO: should take optional positional arguments indicating the context
" like Helper_all_words('python') to display all words in python context

if !exists("g:gotoword_initialized")
   call s:Initialize_gotoword() 
endif

python << EOF
# python imports from vim functions run previously are still available, as 
# well as the variables defined.

# reopen database connection
store._connection = store.get_database().connect()
# select only the keyword names
result = store.execute("SELECT name FROM keyword;")
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
vim.command("exe 'set noro'")                     # set noreadonly
#help_buffer[:] = "\t".join(names)
help_buffer[:] = names
vim.command("exe 'set ro'")                       # set noreadonly

store.close()

EOF
endfunction
