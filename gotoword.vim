" Vim global plugin for displaying info about the word under cursor
" Last Change:	2014 June 17
" Maintainer:	Andrei Chiver  <andreichiver@gmail.com>
" License:	This file is placed in the public domain.


" SHORT DESCRIPTION
" plugin that opens a help file in a separate buffer for the  word under 
" cursor and displays information about it.
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
"TODO: figure out how to change Keyword class in order to introduce contexts
" figure how if context is a table with different context columns, if it's a
" one to many or many to one relation, etc.



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
  command -nargs=0 Helper call s:Help_buffer(expand("<cword>"))
endif
" We define the command :Helper to call the function Help_buffer. 
" The -nargs argument states how many arguments the command will take.
" :call Help_buffer(expand("<cword>"))   " call fct with word under the cursor 

if !exists(":HelperSave")
  command -nargs=* HelperSave call s:Helper_save(<f-args>)   
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

function! s:Help_buffer(word)           
    " TODO: rename this function to Helper
    " fct name always starts with uppercase
    " s: means function is local to script, not part of the global namespace

python << EOF
# get function argument
word = gotoword.vim.eval("a:word")      # get argument by name
# word = vim.eval("a:1")                # get argument by position (first one)

app.keyword = app.vim_wrapper.update_buffer(word)
EOF

    let g:loaded_Help_buffer = 1
endfunction


function! s:Helper_save(...)             " fct has a variable number of args
    " SYNOPSIS
    "   Helper_save()
    "   Helper_save(context)
    "   Helper_save(context, test_answer)
    " To redefine a function that already exists, use the ! 
    " # TODO: do we need ! ?!? 
    " This way, we reload for each subsequent function call
    if !exists("g:loaded_Help_buffer")
      " TODO: is this working?
      echo "There is nothing to save. HelperSave needs to be called after Helper command."
      return 
    endif

    if a:0 == 1
        " get first positional argument
        let context = a:1      
        let test_answer = ''
    elseif a:0 == 2
        let context = a:1
        let test_answer = a:2
    else
        let context = ''
        let test_answer = ''
    endif
"    try
"      " get first positional argument
"      let context = a:1      
"      " python imports from vim functions run previously are still available, 
"      " as well as the variables defined.
"      python context = gotoword.vim.eval("context")
"      python context = unicode(context).lower()
"    "catch /^Vim\%((\a\+)\)\=:E121/
"    catch /.*/           " catch all errors that appear when no args exist
"      python context = ''
"    endtry

python << EOF
context = gotoword.vim.eval("context")
# for testing purposes, context that is "" in vim will be transformed to '' 
# (empty string) in python; 
if context == '""':
    context = ''       # empty string => False in a boolean context
context = unicode(context.strip()).lower()
test_answer = gotoword.vim.eval("test_answer")
#python test_answer = unicode(test_answer).lower()
test_answer = test_answer.strip().lower()

app.helper_save(context, test_answer)
# OR
# gotoword.helper_save(context, gotoword.store)
# TODO: gotoword.helper_save(keyword, context, gotoword.store)

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


" MAIN 
" When this script is loaded into VIM, the following code is executed:
python <<EOF

import sys
import vim
# --------------------------------
# Add our plugin to the path
# --------------------------------
sys.path.append(vim.eval('expand("<sfile>:h")'))
#python sys.path.append(vim.eval('expand("<sfile>:h")') + '/gotoword')
# :help sfile

# DEBUG
# python print vim.eval('expand("<sfile>:h")') + '/gotoword'
# python print sys.path

try:
    from gotoword import gotoword, utils
except ImportError:
    import gotoword, utils


app = gotoword.App()
app.main()
EOF
