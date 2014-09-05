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

" prevent vim from loading twice the plugin
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
  command -nargs=? HelperSave call s:Helper_save(<f-args>)   
  " ? means zero or one argument
endif

" This command saves to DB the helper buffer, which should already exist
" Eg. :HelperSave            - keyword is in db, so context is known
"     :HelperSave kivy       - create new keyword, kivy is the context

if !exists(":HelperDelete")
  command -nargs=0 HelperDelete call s:Helper_delete()
endif

" TODO: create a HelperDeleteContext and/or HelperDefineContext or
" HelperContext delete/new/list         new or save or add; which one?
if !exists(":HelperAllWords")
  command -nargs=0 HelperAllWords call s:Helper_all_words()
endif


" --------------------------------
" FUNCTIONS 
" --------------------------------

function! s:Help_buffer(word)           
    " fct name always starts with uppercase
    " s: means function is local to script, not part of the global namespace

python << EOF
# get function argument
word = gotoword.vim.eval("a:word")      # get argument by name
# word = vim.eval("a:1")                # get argument by position (first one)

keyword = app.vim_wrapper.update_buffer(word)
EOF

    let g:loaded_Help_buffer = 1
endfunction


function! s:Helper_save(...)             " fct has a variable number of args
    " To redefine a function that already exists, use the ! 
    " This way, we reload for each subsequent function call
    if !exists("g:loaded_Help_buffer")
      echo "There is nothing to save. HelperSave needs to be called after Helper command."
      return 
    endif
    try
      " get first positional argument
      let context = a:1      
      " python imports from vim functions run previously are still available, 
      " as well as the variables defined.
      python context = gotoword.vim.eval("context")
      python context = unicode(context).lower()
    "catch /^Vim\%((\a\+)\)\=:E121/
    catch /.*/           " catch all errors that appear when no args exist
      python context = ''
    endtry
    python app.helper_save(context)
    " OR
    " gotoword.helper_save(context, gotoword.store)
    " TODO: gotoword.helper_save(keyword, context, gotoword.store)
endfunction


function! s:Helper_delete()
    " TODO: should take optional positional arguments indicating the context
    " One could delete the definition for one context while keeping the others

    " TODO: what plugin functions need to be run first so that this function can
    " be called? They should be: Helper and/or Helper_save
    " so it should test in vim code for function flags...
    python app.helper_delete(keyword)
    "python gotoword.helper_delete(keyword, gotoword.store)
endfunction


function! s:Helper_all_words()
    " this function displays all keywords from DB in help_buffer, sorted in 
    " alphabetical order
    
    " TODO: should take optional positional arguments indicating the context
    " like Helper_all_words('python') to display all words in python context
    python app.helper_all_words()
endfunction



" MAIN 

" --------------------------------
" Add our plugin to the path
" --------------------------------
python import sys
python import vim
python sys.path.append(vim.eval('expand("<sfile>:h")'))
"python sys.path.append(vim.eval('expand("<sfile>:h")') + '/gotoword')
" :help sfile

" DEBUG
"python print vim.eval('expand("<sfile>:h")') + '/gotoword'
"python print sys.path

" prevent vim from running the python app if the app is already running
" remotely (eg. in ipython, etc.)
if exists("g:gotoword_remote_start")
  finish
endif

python <<EOF
try:
    from gotoword import gotoword, utils
except ImportError:
    import gotoword, utils
app = gotoword.App()
app.main()
EOF
