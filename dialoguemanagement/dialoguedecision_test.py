import unittest
from datastructures.dialogueact import DialogueAct
from datastructures.dialoguestate import DialogueState
from datastructures.defaults import get_greet_act
from dialoguemanagement.stateupdate import SimpleStateUpdater
from dialoguemanagement.dialoguedecision import DialogueDecider
from config import get_default_slots
from languageunderstanding.understandingunits import SimpleNLU
from datastructures.dialoguestate import DialogueState


class TestDialogueDecider(unittest.TestCase):
    def setUp(self):
        self.decider = DialogueDecider()
        self.nlu = SimpleNLU()
        self.state_update = SimpleStateUpdater()

    def print_state_and_act(self, state, sysact):  # debugging hilfsfunktion
        print("DialogueState - Input:")
        print(state)
        print("\nSystem DialogueAct (Output):")
        print(sysact)
        print("\n")

    """-------  Test cases: Asking for a missing REQUIRED_SLOT---------"""

    def test_ask_missing_slot(self):

        state = DialogueState(
            {
                "specify": {
                    "food": [],  # missing slot
                    "area": [{"string": "centre", "negated": False, "confidence": 1.0}],
                    "pricerange": [
                        {"string": "cheap", "negated": False, "confidence": 1.0}
                    ],
                    "name": [],
                },
                "goodbye": False,
                "greeting": "",
                "user_question": None,
                "user_prompt": None,
                "n_failures": 0,
                "inform": [],
            },
            history=[],
        )
        state.found_params = {"area": "centre", "pricerange": "cheap"}

        sysact = self.decider.actOn(state)

        self.assertIsInstance(sysact[0], DialogueAct)
        self.assertEqual("ask", sysact[0].intent)  # erwartet: Absicht = "ask"
        self.assertEqual(
            sysact[0].slots["act_slot"], "food"
        )  # erwartet: Slot ist "food"
        self.assertIsNone(
            sysact[0].slots["template_value_list"]
        )  # erwartet: Vorschlagsliste leer

    # Zweiter Testfall: Area fehlt
    def test_area_missing(self):
        act = self.nlu.parse("I want cheap british food")
        state = DialogueState(get_default_slots(), [get_greet_act()])
        state = self.state_update.update(
            act=act, state=state
        )  # is needed before sysact action
        sysact = self.decider.actOn(state)

        self.assertIsInstance(sysact[0], DialogueAct)
        self.assertEqual("ask", sysact[0].intent)  # erwartet: intent = "ask"
        self.assertEqual(sysact[0].slots["act_slot"], "area")

    # Dritter Testfall: Pricerange fehlt
    def test_pricerange_missing(self):
        act = self.nlu.parse("I want british food in the centre")
        state = DialogueState(get_default_slots(), [get_greet_act()])
        state = self.state_update.update(
            act=act, state=state
        )  # is needed before sysact action

        sysact = self.decider.actOn(state)

        self.assertIsInstance(sysact[0], DialogueAct)
        self.assertEqual("ask", sysact[0].intent)  # erwartet: intent = "ask"
        self.assertEqual(
            sysact[0].slots["act_slot"], "pricerange"
        )  # nachfragen: Wert fehlt

    """ -------- Test Case: All REQUIRED_SLOTS filled, result found -> inform result ---------------------"""

    def test_slots_filled_inform(self):
        state = DialogueState(
            {
                "specify": {
                    "food": [
                        {"string": "chinese", "negated": False, "confidence": 1.0}
                    ],
                    "area": [{"string": "centre", "negated": False, "confidence": 1.0}],
                    "pricerange": [
                        {"string": "cheap", "negated": False, "confidence": 1.0}
                    ],  # all slots filled
                    "name": [],
                },
                "inform": [],
                "goodbye": False,
                "greeting": "",
                "user_question": None,
                "user_prompt": None,
                "n_failures": 0,
            },
            history=[],
        )

        state.found_params = {
            "food": "chinese",
            "area": "centre",
            "pricerange": "cheap",
        }

        state.resultList = [
            {
                "name": "Nikos",
                "addr": "345 Canal Street",
                "phone": "73873783784",
                "signature": "not available",
                "description": "not available",
            }
        ]

        sysact = self.decider.actOn(state)

        self.assertIsInstance(sysact, DialogueAct)  # Typ: ist es ein DialogeAct
        self.assertEqual(sysact.intent, "inform")  # erwartet: Absicht = "inform"

        self.assertEqual(sysact.slots["act_slot"], "result")

        expected_values = {
            "food": "chinese",
            "pricerange": "cheap",
            "area": "centre",
            "name": "Nikos",
            "address": "345 Canal Street",
            "phone": "73873783784",
            "signature": "not available",
            "description": "not available",
        }

        self.assertIn("template_value_list", sysact.slots)
        self.assertEqual(
            sysact.slots["template_value_list"], expected_values
        )  # template werte = result

    """ ---------- Test Case: ALL REQUIRED SLOTS filled, result: no result -> inform result ---------------------"""

    def test_slots_filled_no_result_inform(self):
        state = DialogueState(
            {
                "specify": {
                    "food": [
                        {"string": "italian", "negated": False, "confidence": 1.0}
                    ],
                    "area": [
                        {"string": "downtown", "negated": False, "confidence": 1.0}
                    ],
                    "pricerange": [
                        {"string": "moderate", "negated": False, "confidence": 1.0}
                    ],
                    "name": [],
                },
                "goodbye": False,
                "user_question": None,
                "user_prompt": None,
                "n_failures": 0,
                "greeting": "",
                "inform": "",
            },
            history=[],
        )

        state.found_params = {
            "food": "italian",
            "area": "downtown",
            "pricerange": "moderate",
        }

        state.resultList = []  # Kein Ergebnis: leere Liste

        sysact = self.decider.actOn(state)

        self.assertIsInstance(sysact, DialogueAct)
        self.assertEqual(sysact.intent, "inform")
        self.assertEqual(sysact.slots["act_slot"], "no_result")

        expected_values = {
            "food": "italian",  # Hat template_value_list die gesuchten Slots?
            "pricerange": "moderate",
            "area": "downtown",
        }
        self.assertEqual(sysact.slots["template_value_list"], expected_values)

    """ -------- Test CASED: Goodbye-Handling in different Goodbye-Stages ------------  """

    def test_goodbye_sets_confirmation(self):
        state = self.nlu.parse("bye")
        state.slots["goodbye_stage"] = 1

        sysact = self.decider.actOn(state)
        self.assertEqual(sysact.intent, "confirm")
        self.assertEqual(sysact.slots.get("act_slot"), "goodbye")

    def test_goodbye_when_confirmed_yes(self):
        state = self.nlu.parse("yes")
        state.slots["goodbye_stage"] = 2
        state.slots["confirm_goodbye"] = True

        sysact = self.decider.actOn(state)

        self.assertEqual(sysact.intent, "goodbye")
        self.assertEqual(
            sysact.slots, get_default_slots(), "Expected default slots dict."
        )

    def test_goodbye_when_confirmed_no(self):
        act = self.nlu.parse("no")
        state = DialogueState(get_default_slots(), [get_greet_act()])
        state = self.state_update.update(act=act, state=state)
        state.slots["goodbye_stage"] = 0
        state.slots["confirm_goodbye"] = False

        sysact = self.decider.actOn(state)

        self.assertNotEqual(sysact[0].intent, "goodbye")
        self.assertNotEqual(sysact[0].intent, "confirm")
        self.assertEqual(sysact[0].intent, "ask")
        self.assertIn("act_slot", sysact[0].slots)

    def test_goodbye_when_confirmation_not_yes_no(self):
        act = self.nlu.parse("ich glaube ich will doch weitermachen")
        state = DialogueState(get_default_slots(), [get_greet_act()])
        state = self.state_update.update(act=act, state=state)
        state.slots["goodbye_stage"] = 1
        state.slots["confirm_goodbye"] = False

        sysact = self.decider.actOn(state)

        self.assertEqual(sysact.intent, "confirm")
        self.assertEqual(sysact.slots.get("act_slot"), "goodbye")

    """------ Testfall: Nur Alternative Results gefunden - inform User ----- """

    def test_alternative_result_found(self):
        decider = DialogueDecider()

        state = DialogueState(
            {
                "specify": {
                    "food": [{"string": "italian", "negated": False}],
                    "pricerange": [{"string": "expensive", "negated": False}],
                    "area": [{"string": "north", "negated": False}],
                    "name": [],
                },
                "inform": [],
                "goodbye": False,
                "greeting": "",
                "user_question": None,
                "user_prompt": None,
                "n_failures": 0,
                "alternative_result": True,
            },
            history=[],
        )

        state.found_params = {
            "food": "italian",
            "pricerange": "expensive",
            "area": "centre",
        }

        state.resultList = [
            {
                "name": "Clowns Cafe",
                "addr": "54 King Street City Centre",
                "food": "italian",
                "pricerange": "expensive",
                "area": "centre",
                "phone": "000938393893",
                "signature": "not available",
                "description": "not available",
            }
        ]

        act = decider.actOn(state)

        self.assertIsInstance(act, DialogueAct)
        self.assertEqual(act.intent, "inform")
        self.assertEqual(act.slots.get("act_slot"), "alternative_result")
        self.assertIn("name", act.slots.get("template_value_list", {}))
        self.assertEqual(act.slots["template_value_list"]["name"], "Clowns Cafe")

    """-----Test case: User directly names restaurant name ------ """

    def test_direct_restaurant_name_high_confidence_inform(self):

        # User directly input the restaurant name (confidence higher than 0.7)

        act = self.nlu.parse("i want to eat in the Yu Garden")
        state = self.state_update.update(
            DialogueState(get_default_slots(), [get_greet_act()]), act
        )

        # Provide expected result in resultList (information in database)
        state.resultList = [
            {
                "name": "Yu Garden",
                "addr": "529 newmarket road fen ditton",
                "area": "east",
                "food": "chinese",
                "phone": "01223 248882",
                "pricerange": "expensive",
                "signature": "not available",
                "description": "yu garden serves authentic chinese cuisine",
            }
        ]

        # Populate found_params as the updater would
        state.found_params = {
            "name": "Yu Garden",
            "area": "east",
            "pricerange": "expensive",
            "food": "chinese",
            "signature": "not available",
            "phone": "01223 248882",
            "description": "yu garden serves authentic chinese cuisine",
        }

        # Call the Decider
        sysact = self.decider.actOn(state)

        # Expected act: inform with result_by_name
        self.assertIsInstance(sysact, DialogueAct)
        self.assertEqual(sysact.intent, "inform")
        self.assertEqual(sysact.slots["act_slot"], "result_by_name")

        expected_fields = [
            "name",
            "address",
            "area",
            "food",
            "phone",
            "pricerange",
            "signature",
            "description",
        ]
        for field in expected_fields:
            self.assertIn(field, sysact.slots["template_value_list"])
            self.assertTrue(sysact.slots["template_value_list"][field])

    """-----Test case: Restaurant name fallback for inaccurate input   ------ """

    def test_fallback_when_restaurant_name_confidence_low(self):

        # Simulate a DialogueState with name slot containing low-confidence results below 0.7
        state = DialogueState(get_default_slots(), [get_greet_act()])

        state.slots["specify"]["name"] = [
            {
                "string": "Piiizzzza Huuuuut",
                "confidence": 0.36,
                "negated": False,
            },
        ]

        # Updater may still set a resultList, but decider should ignore it due to low confidence
        state.resultList = [
            {
                "name": "Shiraz Restaurant",
                "addr": "84 regent street city centre",
                "area": "centre",
                "food": "mediterranean",
                "phone": "01223 307581",
                "pricerange": "expensive",
                "signature": "not available",
                "description": "shiraz serves traditional mediterranean cuisine accompanied by an extensive wine list with beers and spirits also available",
            }
        ]

        state.found_params = {
            "name": "Shiraz Restaurant",
            "area": "centre",
            "pricerange": "expensive",
            "food": "mediterranean",
            "signature": "not available",
            "phone": "01223 307581",
            "description": "shiraz serves traditional mediterranean cuisine accompanied by an extensive wine list with beers and spirits also available",
        }

        # Call the decider
        sysact = self.decider.actOn(state)

        # Expected behavior: fallback is triggered due to low confidence
        self.assertIsInstance(sysact, DialogueAct)
        self.assertEqual(sysact.intent, "ask")
        self.assertEqual(sysact.slots.get("act_slot"), "restaurant_clarification")

    """Test Case: If specific information (e.g., phone number) is given & result available and requested."""

    def test_result_and_inform_requested(self):

        state = DialogueState(get_default_slots(), [get_greet_act()])
        state.resultList = [
            {
                "name": "Clowns Cafe",
                "addr": "54 King Street City Centre",
                "food": "italian",
                "pricerange": "expensive",
                "area": "centre",
                "phone": "000938393893",
                "signature": "not available",
                "description": "not available",
            }
        ]
        state.slots["inform"] = ["description"]
        state.found_params = {
            "food": "italian",
            "pricerange": "expensive",
            "area": "centre",
        }
        state.slots["greeting"] = ""
        state.slots["specify"]["name"] = [{"confidence": 0.9, "negated": False}]
        state.new_negated_slot_values = False

        sysacts = self.decider.actOn(state)
        self.assertIsInstance(sysacts, list)
        act_slots = [act.slots["act_slot"] for act in sysacts]
        self.assertIn("no_description", act_slots)

    """ ----- Test Case:  Multiple requested inform slots (e.g., phone and description) should be returned together ----- """

    def test_result_and_multiple_inform_requested(self):

        state = DialogueState(get_default_slots(), [get_greet_act()])
        state.resultList = [
            {
                "name": "Clowns Cafe",
                "addr": "54 King Street City Centre",
                "food": "italian",
                "pricerange": "expensive",
                "area": "centre",
                "phone": "000938393893",
                "signature": "not available",
                "description": "not available",
            }
        ]
        state.slots["inform"] = ["description", "phone"]
        state.found_params = {
            "food": "italian",
            "pricerange": "expensive",
            "area": "centre",
        }
        state.slots["greeting"] = ""
        state.slots["specify"]["name"] = [{"confidence": 0.9, "negated": False}]
        state.new_negated_slot_values = False

        sysacts = self.decider.actOn(state)
        self.assertIsInstance(sysacts, list)
        act_slots = [act.slots["act_slot"] for act in sysacts]
        self.assertIn("no_description", act_slots)
        self.assertIn("phone", act_slots)

    """-----Test Case: User asks for a restaurant information (e.g., description) before resultList exists  ------ """

    def test_inform_slot_before_results(self):
        """
        DialogueDecider should return a list of 2 dialogue acts:
        1.'inform_before_result'
        2. followed by 'ask' for the next missing slot
        """
        # Step 1: Simulate user already provided 2 preferences (area and food)
        state = DialogueState(get_default_slots(), [get_greet_act()])
        act1 = self.nlu.parse("I want italian in the north")
        state = self.state_update.update(state, act1)

        # No results yet, pricerange still missing
        self.assertEqual(len(state.resultList), 0)

        # Step 2: Simulate user asking for "description"
        act2 = self.nlu.parse("Give me the description please.")
        state = self.state_update.update(state, act2)

        # Confirm description is now in inform slot
        self.assertIn("description", state.slots["inform"])

        # Step 3: Call the Decider
        sysacts = self.decider.actOn(state)

        # Assert we got a list of DialogueActs with two elements
        self.assertIsInstance(sysacts, list)
        self.assertEqual(len(sysacts), 2)

        # Check the first act is 'inform_before_result'
        self.assertEqual(sysacts[0].intent, "inform_before_result")
        self.assertEqual(sysacts[0].slots["act_slot"], "no_result_to_inform")

        # Check the second act is 'ask' for next missing slot (e.g., pricerange)
        self.assertEqual(sysacts[1].intent, "ask")
        self.assertEqual(sysacts[1].slots["act_slot"], "pricerange")

    """-----Test Case: Handling user questions (what pricerange)  ------ """

    def test_user_question_what_pricerange(self):

        state = DialogueState(get_default_slots(), [get_greet_act()])
        state.slots["user_question"] = "WHAT_PRICERANGE"
        state.new_dont_care = False
        state.new_slot_selected = False
        state.any_new_negation_is_wildcard = False

        sysact = self.decider.actOn(state)

        self.assertIsInstance(sysact, DialogueAct)
        self.assertEqual(sysact.intent, "ask")
        self.assertEqual(sysact.slots["act_slot"], "pricerange")
        self.assertEqual(sysact.slots["user_question"], "WHAT_PRICERANGE")
        self.assertFalse(sysact.slots["is_new_dont_care"])
        self.assertFalse(sysact.slots["new_slot_select"])
        self.assertFalse(sysact.slots["any_new_negation_is_wildcard"])

    """-----Test Case: Handling user questions (what area)  ------ """

    def test_user_question_area_about_what_area(self):
        # Decider should return DialogueAct(ask, act_slot='area')

        state = DialogueState(get_default_slots(), [get_greet_act()])

        # Step 1: Simulate state where user_question is 'WHAT_AREA'
        state.slots["user_question"] = "WHAT_AREA"

        # reset the flags
        state.new_dont_care = False
        state.new_slot_selected = False
        state.any_new_negation_is_wildcard = False

        # Step 2: Call the Decider
        sysact = self.decider.actOn(state)

        # Step 3: Assertions
        self.assertIsInstance(sysact, DialogueAct)
        self.assertEqual(sysact.intent, "ask")
        self.assertEqual(sysact.slots["act_slot"], "area")
        self.assertEqual(sysact.slots["user_question"], "WHAT_AREA")
        self.assertFalse(sysact.slots["is_new_dont_care"])
        self.assertFalse(sysact.slots["new_slot_select"])
        self.assertFalse(sysact.slots["any_new_negation_is_wildcard"])

    """-----Test Case: Handling user questions (what food)  ------ """

    def test_user_question_what_food(self):

        state = DialogueState(get_default_slots(), [get_greet_act()])
        state.slots["user_question"] = "WHAT_FOOD"
        state.new_dont_care = False
        state.new_slot_selected = False
        state.any_new_negation_is_wildcard = False

        sysact = self.decider.actOn(state)

        self.assertIsInstance(sysact, DialogueAct)
        self.assertEqual(sysact.intent, "ask")
        self.assertEqual(sysact.slots["act_slot"], "food")
        self.assertEqual(sysact.slots["user_question"], "WHAT_FOOD")
        self.assertFalse(sysact.slots["is_new_dont_care"])
        self.assertFalse(sysact.slots["new_slot_select"])
        self.assertFalse(sysact.slots["any_new_negation_is_wildcard"])

    """-----Test Case: Handling user questions (WHAT_CAN_YOU_DO)  ------ """

    def test_user_question_what_can_you_do(self):

        state = DialogueState(get_default_slots(), [get_greet_act()])
        state.slots["user_question"] = "WHAT_CAN_YOU_DO"

        sysact = self.decider.actOn(state)

        # Check that sysact is a list
        self.assertIsInstance(sysact, list)

        # Check that all items are DialogueAct instances
        for act in sysact:
            self.assertIsInstance(act, DialogueAct)

    """-----Test Case: Handling user questions (HOW_TO_USE)  ------ """

    def test_user_question_how_to_use(self):

        state = DialogueState(get_default_slots(), [get_greet_act()])
        state.slots["user_question"] = "HOW_TO_USE"

        sysact = self.decider.actOn(state)

        self.assertIsInstance(sysact, list)
        for act in sysact:
            self.assertIsInstance(act, DialogueAct)

    """-----Test Case: Handling user questions (OUT_OF_SCOPE)  ------ """

    def test_user_question_out_of_scope(self):

        state = DialogueState(get_default_slots(), [get_greet_act()])
        state.slots["user_question"] = "OUT_OF_SCOPE"

        sysact = self.decider.actOn(state)

        self.assertIsInstance(sysact, list)
        for act in sysact:
            self.assertIsInstance(act, DialogueAct)

    """-----Test Case: Handling user questions (RESTAURANT_NUMBER)  ------ """

    def test_user_question_restaurant_number(self):

        state = DialogueState(get_default_slots(), [get_greet_act()])
        state.slots["user_question"] = "RESTAURANT_NUMBER"

        sysact = self.decider.actOn(state)

        self.assertIsInstance(sysact, list)
        for act in sysact:
            self.assertIsInstance(act, DialogueAct)

    """-----Test Case: Handling user questions (RESTAURANT_SIGNATURE) if Database entry empty  ------ """

    def test_inform_empty(self):
        state = DialogueState(get_default_slots(), [get_greet_act()])
        state.slots["inform"] = ["signature"]
        state.resultList = [
            {
                "name": "Test",
                "addr": "Addr",
                "phone": "012345",
                "signature": "",  # leerer sting
                "description": "Nice place",
            }
        ]
        state.found_params = {
            "area": "centre",
            "food": "italian",
            "pricerange": "cheap",
        }
        acts = self.decider.actOn(state)
        self.assertIsInstance(acts, list)
        self.assertIn("no_signature", [act.slots["act_slot"] for act in acts])

    """ --- Test Case: System should return an 'impossible' act when all possible areas have been negated."""

    def test_impossible_constraints_area(self):
        state = DialogueState(get_default_slots(), [get_greet_act()])

        state.slots["specify"]["area"] = [
            {"string": val, "negated": True}
            for val in ["north", "south", "east", "west", "centre"]
        ]
        sysact = self.decider.actOn(state)
        self.assertEqual(sysact.intent, "impossible")
        self.assertEqual(sysact.slots["act_slot"], "area")
