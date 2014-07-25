#!/usr/bin/python

'''
This module implements the logic for Helper_save() vim function from
gotoword.vim file.
It implements the finite state machine from a Python course found here:
    http://www.python-courses.eu/finite_state_machine.php

For now, the states of the machine apply only for the case when the
keyword doesn't exist in DB and context is not specified by the user
when saving the keyword definition -> 0 0 case.

The logical steps of such a case:
# keyword doesn't exist, context doesn't exist                                             0 0
    # Do you want to specify a context?
        # abort [a]
        # yes -> create keyword with context   1
        # no -> create keyword with no context 0
'''

try:
    import vim
except ImportError:
    print("ImportError: vim module is useful only when the script is run inside vim compiled")

# build module interface for when it's being imported
__all__ = ["StateMachine", "read_context_transitions", "start_transitions", "end_state"]


class StateMachine:
    def __init__(self):
        self.handlers = {}
        self.startState = None
        self.endStates = []

    def add_state(self, name, handler, end_state=0):
        name = name.upper()
        self.handlers[name] = handler
        if end_state:
            self.endStates.append(name)

    def set_start(self, name):
        self.startState = name.upper()

    def run(self, cargo):
        try:
            handler = self.handlers[self.startState]
        except:
            raise StandardError("Initialization error: must call "
                                ".set_start() before .run()")
        if not self.endStates:
            raise  StandardError("Initialization error: at least one state "
                                 "must be an end_state")

        while True:
            (newState, cargo) = handler(cargo)
            if newState.upper() in self.endStates:
                print("reached ", newState)
                break
            else:
                handler = self.handlers[newState.upper()]


def start_transitions(txt=''):
    # TODO: give vim as arg to this fct. so this module doesn't need to import
    # vim
    '''Handler for 'Start' state. Handles input in order to advance to
    next state.'''

    print("Do you want to specify a context that this definition of the word "
          "applies in?")
    message = "[Y]es define it    [N]o do not define it    [A]bort"
    #print("[Y]es I'll define it    [N]o I won't define it    [A]bort")
    #answer = vim.eval("")
    # following vim cmds are needed because:
    #   http://vim.wikia.com/wiki/User_input_from_a_script
    vim.command('call inputsave()')
    # put vim cursor here:
    vim.command("let user_input = input('" + message + ": ')")
    vim.command('call inputrestore()')
    # TODO: how to solve the prompt issue??
    vim.command('echo')     # make prompt pass to next line, for pretty printing
    answer = vim.eval('user_input')
    #answer = 'Y'
    answer = answer.upper().strip()
    if answer.startswith('Y'):
        new_state = "read_context_state"
    elif answer.startswith('N'):
        new_state = "new_keyword_state"
    else:
        # [A]bort
        new_state = "end_state"
    return (new_state, answer)


def read_context_transitions(answer=''):
    print("read_context_state")
    return ("end_state", answer)


def end_state(answer):
    if answer == 'abort':
        print("Aborted. Keyword definition not saved.")
    else:
        print("Keyword %s saved with context %s" % "testend")
              # TODO: how can more definitions be stored for each context, answer.contexts)
    return ("end_state", answer)


#if __name__ == "__main__":
m = StateMachine()
m.add_state("Start", start_transitions)
m.add_state("read_context_state", read_context_transitions)
m.add_state("end_state", end_state, end_state=1)
m.set_start("Start")
#m.run('start')
