from copy import deepcopy
import unittest
from datastructures.dialogueact import DialogueAct
from datastructures.dialoguestate import DialogueState
from dialoguemanagement.dialoguedecision import DialogueDecider
from config import get_default_slots, NLU_RETURN_TOP_N_OPTIONS
from languageunderstanding.understandingunits import SimpleNLU
from languageunderstanding.understandingunits_test import choice_in_top_n


class TestDialogueState(unittest.TestCase):
    def setUp(self):
        self.nlu = SimpleNLU()

    def test_update_replace(self):

        state = DialogueState(self.nlu.parse("i want cheap british food").slots)

        updated_state = state.update(
            self.nlu.parse("i want italian food"), behaviour="replace"
        )

        assert isinstance(updated_state, DialogueState)

        assert not choice_in_top_n(
            string="british",
            negated=False,
            top_n=float("inf"),
            specifications=updated_state.slots["specify"]["food"],
        )
        assert choice_in_top_n(
            string="italian",
            negated=False,
            top_n=1,
            specifications=updated_state.slots["specify"]["food"],
        )
        assert choice_in_top_n(
            string="cheap",
            negated=False,
            top_n=1,
            specifications=updated_state.slots["specify"]["pricerange"],
        )

    def test_update_add(self):
        state = DialogueState(self.nlu.parse("i want cheap british food").slots)

        updated_state = state.update(
            self.nlu.parse("i want italian food"), behaviour="add"
        )

        assert isinstance(updated_state, DialogueState)

        assert not choice_in_top_n(
            string="british",
            negated=False,
            top_n=1,
            specifications=updated_state.slots["specify"]["food"],
        )
        assert choice_in_top_n(
            string="british",
            negated=False,
            top_n=2,
            specifications=updated_state.slots["specify"]["food"],
        )
        assert choice_in_top_n(
            string="italian",
            negated=False,
            top_n=1,
            specifications=updated_state.slots["specify"]["food"],
        )
        assert choice_in_top_n(
            string="cheap",
            negated=False,
            top_n=1,
            specifications=updated_state.slots["specify"]["pricerange"],
        )
