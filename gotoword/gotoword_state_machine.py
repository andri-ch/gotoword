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


def start_transitions(cargo):
    # TODO: give vim as arg to this fct. so this module doesn't need to import
    # vim
    '''Handler for 'Start' state. Handles input in order to advance to
    next state.'''

    answer = vim.eval("""inputlist(["Do you want to specify a context that this definition of the word applies in?", \
            "1. Yes, I will provide a context", \
            "2. No, I won't provide a context", \
            "3. Abort"])
            """)
    answer = answer.upper().strip()
    if answer.startswith('1'):
        new_state = "read_context_state"
    elif answer.startswith('2'):
        new_state = "new_keyword_state"
    else:
        # Abort
        new_state = "end_state"
    return (new_state, cargo)


def read_context_transitions(cargo):
    print("read_context_state")
    # read context from user
    # create keyword with context:
    # but for now create it without context
    func, store, keyword, buf = cargo

    kw = func(store, keyword, buf)
    print("kw: %s " % kw)
    return ("end_state", cargo)


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
