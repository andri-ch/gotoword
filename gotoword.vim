" Vim global plugin for displaying info about the word under cursor
" Last Change:	2015 February 21
" Maintainer:	Andrei Chiver  <andreichiver@gmail.com>
" License:	This file is placed in the public domain.


" SHORT DESCRIPTION
" plugin that opens a help file (a note) in a separate buffer for the  word 
" under the cursor and displays information about it. The help file can 
" be created, updated and deleted by the user on the spot.
"
" Usually the word belongs to a context, and same word can belong to different
" contexts, so it can have a definition for each context it belongs to.
"
" All this information is retrieved from a database.



" WHAT IS IT USEFUL FOR?
" TODO: write some more use cases
" Mainly, you can use it as a quick reminder.
" For example, when you're inside a document, you don't remember the 
" meaning/all the details about a word/all implications for that word, but you 
" did write something about it a while ago, so you can open up the note.
" This could be later extended to get info that others have written so that
" you can benefit from it.
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


if !has('python')
    echo "Error: Required vim compiled with +python"
    echo "To check the python configuration, type in a terminal the following: "
    echo "vim --version | grep --color '+python'"
    finish                             " like python's sys.exit()
endif

" TODO: check for python 2 or python 3 if it works only on python3.

" prevent vim from loading the plugin twice
if exists("g:gotoword_loaded")
  finish
endif
let g:gotoword_loaded = 1


" --------------------------------
" COMMANDS 
" --------------------------------

if !exists(":Helper")
  "command -nargs=0 -range Helper call s:Help_buffer(<line1>, <line2>)
  command -nargs=? -range Helper call s:Help_buffer(<line1>, <line2>, <f-args>)
endif
" We define the command :Helper to call the function Help_buffer. 
" The -nargs argument states how many arguments the command will take.
" :call Help_buffer(expand("<cword>"))   " call fct with word under the cursor 
" Eg:
" Situation 1: display a note for the word under the cursor
" :Helper 
" Situation 2: display a note for any word you want
" :Helper word_you_want
" Situation 3: display a note for a visual selection, select word/words
" :Helper

if !exists(":HelperSave")
  command -nargs=? HelperSave call s:Helper_save(<f-args>)   
  " -nargs=*    Any number of arguments are allowed (0, 1, or many)
  " -nargs=?    zero or one argument
endif

" This command saves to DB the helper buffer, which should already exist
" Eg. :HelperSave            - keyword is in db, so context is known
"     :HelperSave kivy       - create new keyword, kivy is the context

if !exists(":HelperDelete")
  command -nargs=0 HelperDelete call s:Helper_delete()
endif

if !exists(":HelperDeleteContext")
  command -nargs=1 HelperDeleteContext call s:Helper_delete_context(<f-args>)
" Eg. :HelperDeleteContext python
endif


" TODO: create a HelperDeleteContext and/or HelperDefineContext or
" HelperContext delete/new/list         new or save or add; which one?
if !exists(":HelperAllWords")
  command -nargs=0 HelperAllWords call s:Helper_all_words()
endif

if !exists(":HelperAllContexts")
  " lists all available contexts that words can belong to (eg. python, c++,
  " etc.)
  command -nargs=0 HelperAllContexts call s:Helper_all_contexts()
endif

if !exists(":HelperContextWords")
  " lists all available words that belong to context (eg. python context could
  " have django, flask, pyramid, as keywords, etc.)
  command -nargs=1 HelperContextWords call s:Helper_context_words(<f-args>)
  " SYNOPSIS
  "   :HelperContextWords python
  "   Do not add simple or double quotes around argument because function handles them 
  "   differently;
  "   Bad examples:
  "   :HelperContextWords "python"
  "   :HelperContextWords 'python'
endif

if !exists(":HelperWordContexts")             
"" OBSOLETE, it should be a python function
  " lists all contexts current keyword belongs to (eg. unittest word could
  " belong to 'python' context and to 'testing' context, etc.)
  command -nargs=0 HelperWordContexts call s:Helper_word_contexts()
  " SYNOPSIS
  "   :HelperWordContexts
endif


" --------------------------------
" FUNCTIONS 
" --------------------------------

function! s:Help_buffer(...)           
"function! s:Help_buffer(word)           
    " TODO: rename this function to Helper
    " fct name always starts with uppercase
    " s: means function is local to script, not part of the global namespace
  if a:0 == 2
    "echomsg "situation 1 or 3"
    let lines = getline(a:1, a:2)
    let mode = visualmode(1)
    if mode != '' && line("'<") == a:1
      "echomsg "mode != ''"
      if mode == "v"
        "echomsg "character-wise visual mode"
        let start = col("'<") - 1
        let end = col("'>") - 1
        " slice i:w
        " n end before start in case the selection is only one line
        let lines[-1] = lines[-1][: end]
        let lines[0] = lines[0][start :]
        " just for debugging; word in this case should be the whole selected
        " text.
        "let word = join(lines, ' ')
        let word = lines
        "echo word
      elseif mode == "\<c-v>"
        "echomsg "block-wise visual mode"
        let start = col("'<")
        if col("'>") < start
          let start = col("'>")
        endif
        let start = start - 1
        call map(lines, 'v:val[start :]')
        " just for debugging; word in this case should be the whole selected
        " text.
        "let word = join(lines, ' ')
        let word = lines
        "echo word
      endif
    else
      " Situation 1
      "echomsg "this is branch with no visual mode"
      " Eg: this expands "python.py" to "python", the word under cursor ends at 
      " . (dot)
      let word = expand("<cword>")
      "let word = expand("<cWORD>")
    endif
  elseif a:0 == 3
    " Situation 2 
    "echomsg "this is branch a:0 == 3"
    let argtype = type(a:3)
    if argtype == 1
      " a String
      "echomsg "this is branch with argtype == 1"
      let word = a:3
      let lines = split(a:1, "\n")
    else
      echoe 'gotoword: Argument must be a string.'
      return
    endif
  else
    echoe 'gotoword: Invalid number of arguments for Helper.'
    return
  endif

python << EOF
# get function argument
#word = gotoword.vim.eval("a:word")      # get argument by name, Help_buffer(word)
# word = vim.eval("a:1")                # get argument by position (first one)
#word = gotoword.vim.eval("word")
word = gotoword.vim.eval("word")
if type(word) == list:
    for i, line in enumerate(word):
        word[i] = line.strip()
if len(word) == 1:
    # one line of text only (one or more words)
    word = word[0]
else:
    pass
    # multiple lines should be used to extract context, etc.
#logger.debug("INPUT IS: %s" % type(word), extra={'className': ''})

app.keyword = app.vim_wrapper.update_buffer(word)
EOF

  let g:loaded_Help_buffer = 1
endfunction


"function! s:Helper_save(context)             " fct has a variable number of args
function! s:Helper_save(...)             " fct has a variable number of args
    " SYNOPSIS
    "   Helper_save()
    "   Helper_save(context)
    "   Helper_save(context, test_answer)
    " To redefine a function that already exists, use the ! 
    " # TODO: do we need ! ?!? 
    " This way, we reload for each subsequent function call
    if !exists("g:loaded_Help_buffer")
      echo "There is nothing to save. HelperSave needs to be called after Helper command."
      return 
    endif

    if a:0 == 1
        " get first positional argument
        let context = a:1      
    "    let test_answer = ''
    "elseif a:0 == 2
    "    let context = a:1
    "    let test_answer = a:2
    else
        let context = ''
    "    let test_answer = ''
    endif

python << EOF
context = gotoword.vim.eval("context")
# for testing purposes, context that is "" in vim will be transformed to '' 
# (empty string) in python; 
if context == '""':
    context = ''       # empty string => False in a boolean context
context = unicode(context.strip()).lower()
#test_answer = gotoword.vim.eval("test_answer")
#test_answer = test_answer.strip().lower()
test_answer = ""
# TODO: get rid of test_answer
app.helper_save(context, test_answer)

EOF
endfunction


function! s:Helper_delete()
    " TODO: should take optional positional arguments indicating the context
    " One could delete the definition for one context while keeping the others

    " TODO: what plugin functions need to be run first so that this function can
    " be called? They should be: Helper and/or Helper_save
    " so it should test in vim code for function flags...
    python app.helper_delete(app.keyword)
    "python gotoword.helper_delete(keyword, gotoword.store)
endfunction


function! s:Helper_delete_context(context)
    " deletes a context from database
    python context = gotoword.vim.eval("a:context")
    python context = unicode(context.strip()).lower()
    python app.helper_delete_context(context)
endfunction


function! s:Helper_all_words()
    " this function displays all keywords from DB in help_buffer, sorted in 
    " alphabetical order
    
    " TODO: should take optional positional arguments indicating the context
    " like Helper_all_words('python') to display all words in python context
    python app.helper_all_words()
endfunction


function! s:Helper_all_contexts()
    " this function displays all contexts from DB in help_buffer, sorted in 
    " alphabetical order
    
    " TODO: should take optional positional arguments indicating the context
    " like Helper_all_words('python') to display all words in python context
    python app.helper_all_contexts()
endfunction


function! s:Helper_context_words(context)
    " this function displays in help_buffer all keywords from DB that belong 
    " to context, sorted in alphabetical order
    python context = gotoword.vim.eval("a:context")
    " sanitize arg; TODO: define a sanitize() fct
    python context = unicode(context.strip()).lower()
    python app.helper_context_words(context)
endfunction


function! s:Helper_word_contexts()
"    " Displays in help buffer all contexts the current keyword belongs to,
"    " sorted in alphabetical order
"    " TODO: this should work for the current keyword or for the word under the
"    " cursor?
    python app.helper_word_contexts()
endfunction


function! Get_visual_selection()
  " Why is this not a built-in Vim script function?!
  let [lnum1, col1] = getpos("'<")[1:2]
  let [lnum2, col2] = getpos("'>")[1:2]
  let lines = getline(lnum1, lnum2)
  let lines[-1] = lines[-1][: col2 - (&selection == 'inclusive' ? 1 : 2)]
  let lines[0] = lines[0][col1 - 1:]
  return join(lines, "\n")
endfunction


" MAIN 
" When this script is loaded into VIM, the following code is executed:
python <<EOF

import vim
import sys
import logging

# --------------------------------
# Add our plugin to the path
# --------------------------------
gotoword_plugin_path = vim.eval('expand("<sfile>:h")')
# :help sfile
#sys.path.insert(1, gotoword_plugin_path)

## hack for plugin to work during development
sys.path.insert(1, '/home/andrei/.vim/andrei_plugins/gotoword')



from gotoword import settings
settings.setup(settings.DATABASE)
from gotoword import gotoword_logging
logger = gotoword_logging.set_up_logging(logging.DEBUG, 'vim')
#gotoword_logging.logger.debug("SCRIPT STARTED", extra={'className': ""}),
logger.debug("SCRIPT STARTED", extra={'className': ""}),

from gotoword import gotoword
from gotoword import utils


app = gotoword.App()
app.main()
EOF
