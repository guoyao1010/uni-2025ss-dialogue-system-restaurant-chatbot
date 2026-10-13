from datastructures.dialoguestate import DialogueState
from datastructures.dialogueact import DialogueAct
from config import get_default_slots


def get_root_state():
    state = DialogueState(slots=get_default_slots(), history=[])
    state.is_first_turn = True
    return state


def get_greet_act():
    return DialogueAct("greet", {}, history=[get_root_state()])
