*gotoword.txt*	Plugin for displaying info about the word under cursor

Plugin that opens its own help buffer in the same window for word under the 
cursor, displaying info retrieved from its database or other sources.
It is like a dictionary where you can write multiple definitions of a word, 
based on context it is used in.

It offers basic CRUD (Create, Read, Update, Delete) capabilities.
Create - Helper, user adds the definition of the word, HelperSave
Read - Helper called for the word under the cursor
Update - Helper, user edits the opened help buffer, then HelperSave 
Delete - HelperDelete

Commands:
:Helper {word}
	Display info or allows to add a description or update for {word}.
:HelperSave
    This command saves to database the contents from help buffer, which should 
    exist.
:HelperDelete
    This command deletes from database the keyword whose contents are
    displayed in the help buffer.
:HelperAllWords
    Displays all keywords from DB in help_buffer, sorted in 
    alphabetical order.
 
						*gotoword-settings*
This plugin doesn't have any settings.
