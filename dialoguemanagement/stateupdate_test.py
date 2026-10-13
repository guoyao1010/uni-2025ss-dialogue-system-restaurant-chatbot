import unittest
from datastructures.dialogueact import DialogueAct
from datastructures.dialoguestate import DialogueState
from datastructures.defaults import get_greet_act
from dialoguemanagement.stateupdate import SimpleStateUpdater
from languageunderstanding.understandingunits import SimpleNLU
from languageunderstanding.understandingunits_test import choice_in_top_n
from dialoguemanagement.dialoguedecision import DialogueDecider
from config import get_default_slots, REQUIRED_SLOTS, ALL_SLOTS


class TestStateUpdate(unittest.TestCase):
    def setUp(self):
        self.stateUpdate = SimpleStateUpdater()
        self.nlu = SimpleNLU()

    def test_update(self):
        # DialogueState({"intent":"find.restaurant","area":"centre", "pricerange":"cheap"})
        state = DialogueState(get_default_slots(), [get_greet_act()])
        state = self.stateUpdate.update(
            act=self.nlu.parse("i want cheap food in the centre"),
            state=state,
        )

        self.assertIsInstance(state, DialogueState)
        assert choice_in_top_n(
            string="centre",
            negated=False,
            top_n=1,
            specifications=state.slots["specify"]["area"],
        )
        assert choice_in_top_n(
            string="cheap",
            negated=False,
            top_n=1,
            specifications=state.slots["specify"]["pricerange"],
        )

    def test_update_with_simple_negation(self):
        state = DialogueState(get_default_slots(), [get_greet_act()])

        # Test if after negation the negated slot value is added to the state-set and new_negated_slot_values is True
        state = self.stateUpdate.update(
            act=self.nlu.parse("not expensive"),
            state=state,
        )

        self.assertIsInstance(state, DialogueState)

        assert choice_in_top_n(
            string="expensive",
            negated=True,
            top_n=1,
            specifications=state.slots["specify"]["pricerange"],
        )

        assert "expensive" in state.negated_slot_values
        assert state.any_new_negation_is_wildcard is True

        # new negated slot values should be set to False after text with no negation

        state = self.stateUpdate.update(
            act=self.nlu.parse("i want cheap food in the centre"),
            state=state,
        )

        # after dialog decision the new_negated_slot_values should be set False for the next update
        dialogDecision = DialogueDecider()
        dialogDecision.actOn(state)
        assert state.any_new_negation_is_wildcard is False

    def test_update_with_multiple_negation(self):
        state = DialogueState(get_default_slots(), [get_greet_act()])
        state = self.stateUpdate.update(
            act=self.nlu.parse(
                "I don't want cheap food and no italian and please not in the centre"
            ),
            state=state,
        )

        # check state specify slots for negated values
        assert choice_in_top_n(
            string="cheap",
            negated=True,
            top_n=5,
            specifications=state.slots["specify"]["pricerange"],
        )
        assert choice_in_top_n(
            string="italian",
            negated=True,
            top_n=5,
            specifications=state.slots["specify"]["food"],
        )
        assert choice_in_top_n(
            string="centre",
            negated=True,
            top_n=5,
            specifications=state.slots["specify"]["area"],
        )

        # check set negated values and new_negated_slot_values for Boolean
        assert "cheap" in state.negated_slot_values
        assert "italian" in state.negated_slot_values
        assert "centre" in state.negated_slot_values

        assert state.any_new_negation_is_wildcard is True

        # check if negated values are removed after text with no negation
        state = self.stateUpdate.update(
            act=self.nlu.parse("I want food in the centre and cheap pricerange"),
            state=state,
        )

        dialogDecision = DialogueDecider()
        dialogDecision.actOn(state)
        assert state.any_new_negation_is_wildcard is False

    def test_update_negation_in_and_out_of_list(self):
        state = DialogueState(get_default_slots(), [get_greet_act()])
        state = self.stateUpdate.update(
            act=self.nlu.parse("i want to eat in the centre and not expensive"),
            state=state,
        )
        assert choice_in_top_n(
            string="expensive",
            negated=True,
            top_n=1,
            specifications=state.slots["specify"]["pricerange"],
        )
        assert "expensive" in state.negated_slot_values
        assert state.any_new_negation_is_wildcard is True

        # update but still expensive should be negated
        state = self.stateUpdate.update(
            act=self.nlu.parse("i want to eat in the south and not expensive"),
            state=state,
        )
        assert choice_in_top_n(
            string="expensive",
            negated=True,
            top_n=1,
            specifications=state.slots["specify"]["pricerange"],
        )
        assert "expensive" in state.negated_slot_values
        assert state.any_new_negation_is_wildcard is False

        # update but expensive should not be negated anymore
        state = self.stateUpdate.update(
            act=self.nlu.parse("i want to eat expensive food"),
            state=state,
        )
        # expensive should not be negated anymore
        assert choice_in_top_n(
            string="expensive",
            negated=False,
            top_n=1,
            specifications=state.slots["specify"]["pricerange"],
        )
        assert "expensive" not in state.negated_slot_values

        dialogDecision = DialogueDecider()
        dialogDecision.actOn(state)
        assert state.any_new_negation_is_wildcard is False

    def test_update_with_wildcard(self):
        state = DialogueState(get_default_slots(), [get_greet_act()])
        state = self.stateUpdate.update(
            act=self.nlu.parse(
                "pricerange doesnt matter"
            ),  # "any Pricerange or doesn't does not work with current NLU
            state=state,
        )

        assert choice_in_top_n(
            string="*",
            negated=None,  # wildcard can be negated or not it is ignored for db-search anyway
            top_n=5,
            specifications=state.slots["specify"]["pricerange"],
        )

    def test_update_with_wildcard_and_negation(self):
        state = DialogueState(get_default_slots(), [get_greet_act()])
        state = self.stateUpdate.update(
            act=self.nlu.parse(
                "pricerange doesnt matter but not expensive"
            ),  # "any Pricerange" does not work with current NLU
            state=state,
        )
        assert choice_in_top_n(
            string="*",
            negated=None,  # wildcard can be negated or not (negation of wildcard is ignored for db-search anyway)
            top_n=5,
            specifications=state.slots["specify"]["pricerange"],
        )
        assert choice_in_top_n(
            string="expensive",
            negated=True,
            top_n=5,
            specifications=state.slots["specify"]["pricerange"],
        )
        assert "expensive" in state.negated_slot_values
        assert state.any_new_negation_is_wildcard is True

    def test_update_last_slot_is_saved(self):
        state = DialogueState(get_default_slots(), [get_greet_act()])
        state = self.stateUpdate.update(
            act=self.nlu.parse("hi"),
            state=state,
        )

        assert state.slots["specify"]["food"] == []
        dialogDecision = DialogueDecider()
        dialogDecision.actOn(state)
        assert state.previous_slot_type == "food"

        # check if the last slot is saved in the state
        state = self.stateUpdate.update(
            act=self.nlu.parse("i want chinese food"),
            state=state,
        )
        # check if the last slot is still saved
        assert state.previous_slot_type == "food"

        # check if the next slot to be asked is saved
        dialogDecision = DialogueDecider()
        dialogDecision.actOn(state)
        assert state.previous_slot_type == "pricerange"
        assert state.slots["specify"]["pricerange"] == []

        state = self.stateUpdate.update(
            act=self.nlu.parse("i want a cheap restaurant"),
            state=state,
        )
        # check if the last slot is still saved
        assert state.previous_slot_type == "pricerange"

        # check for the next slot to be asked and if it is saved
        dialogDecision = DialogueDecider()
        dialogDecision.actOn(state)
        assert state.previous_slot_type == "area"
        assert state.slots["specify"]["area"] == []

        # check if the last slot is saved in the state
        state = self.stateUpdate.update(
            act=self.nlu.parse("i want to eat in the centre"),
            state=state,
        )
        # check if the last slot is still saved
        assert state.previous_slot_type == "area"

    def test_update_last_slot_is_saved(self):
        state = DialogueState(get_default_slots(), [get_greet_act()])
        state = self.stateUpdate.update(act=self.nlu.parse("hi"), state=state)
        # now the system should ask for the first not specified slot: food (look config.py for required slots)
        # dialoguedecision needs to be called because here the previous slot is set
        dialogDecision = DialogueDecider()
        dialogDecision.actOn(state)
        assert state.previous_slot_type == "food"
        assert state.slots["specify"]["food"] == []

        state = self.stateUpdate.update(
            act=self.nlu.parse("i want chinese food but not italian"),
            state=state,
        )
        assert (
            state.previous_slot_type == "food"
        )  # check if the last slot is still saved

        # check for the next slot to be asked and if it is saved
        dialogDecision = DialogueDecider()
        dialogDecision.actOn(state)
        assert state.previous_slot_type == "area"
        assert state.slots["specify"]["area"] == []

        state = self.stateUpdate.update(
            act=self.nlu.parse("i don't want to eat in the centre"),
            state=state,
        )
        # check if the last slot is still saved
        assert state.previous_slot_type == "area"

        # check for the next slot to be asked and if it is saved"
        dialogDecision = DialogueDecider()
        dialogDecision.actOn(state)
        assert state.previous_slot_type == "pricerange"

        assert state.slots["specify"]["pricerange"] == []

        state = self.stateUpdate.update(
            act=self.nlu.parse("pricerange doesnt matter but not expensive"),
            state=state,
        )

        # check if the last slot is still saved
        assert state.previous_slot_type == "pricerange"

    # i removed test_sequential_slot_filling because it did not include a single assertion - Koos

    # I added the unittests for the goodbye-states - Sandra
    def test_goodbye_if_bye(self):
        state = DialogueState(get_default_slots(), [get_greet_act()])
        goodbye_act = DialogueAct(
            intent="bye",
            slots={"goodbye": True},
            history=state.history,
        )
        update_state = self.stateUpdate.update(state, goodbye_act)

        self.assertEqual(update_state.slots["goodbye_stage"], 1)
        self.assertFalse(update_state.slots["confirm_goodbye"])
        self.assertFalse(update_state.slots["goodbye"])

    def test_goodbye_confirmation_answer_yes(self):
        slots = get_default_slots()
        slots["goodbye_stage"] = 1
        state = DialogueState(slots)

        goodbye_act = DialogueAct(
            intent="bye",
            slots={"answer": "yes"},
            history=state.history,
        )
        update_state = self.stateUpdate.update(state, goodbye_act)

        expected_specify = {slot: [] for slot in ALL_SLOTS}

        self.assertEqual(update_state.slots["goodbye_stage"], 2)
        self.assertEqual(update_state.slots["confirm_goodbye"], True)
        self.assertEqual(update_state.slots["goodbye"], True)
        self.assertEqual(update_state.slots["intent"], "bye")
        self.assertEqual(dict(update_state.slots["specify"]), expected_specify)
        self.assertEqual(update_state.resultList, [])

    """To ask:     
    key = (item["string"], item["negated"], item["backup_for"])
    """

    def test_goodbye_confirmation_answer_no(self):
        state = DialogueState(get_default_slots(), [get_greet_act()])
        state.slots["goodbye_stage"] = 1
        state.slots["specify"] = {
            "food": [
                {
                    "string": "italian (0.992951), romanian (0.636907), portuguese (0.633602), european (0.625143), australian (0.475629), catalan (0.452122)",
                    "negated": False,
                    "confidence": 1.0,
                    "backup_for": None,
                }
            ],
            "pricerange": [],
            "name": [],
            "area": [],
        }

        expected_specify = {
            "food": [
                {
                    "string": "italian (0.992951), romanian (0.636907), portuguese (0.633602), european (0.625143), australian (0.475629), catalan (0.452122)",
                    "negated": False,
                    "confidence": 1.0,
                    "backup_for": None,
                }
            ],
            "pricerange": [],
            "name": [],
            "area": [],
        }

        goodbye_act = DialogueAct(
            intent="bye",
            slots={
                "answer": "no",
                "goodbye": False,
                "specify": {
                    "food": [],
                    "pricerange": [],
                    "area": [],
                    "name": [],
                },
                "user_question": None,
                "inform": [],
                "greeting": "",
                "dont_like_choice": False,
                "confirm_goodbye": False,
                "user_prompt": None,
                "n_failures": 0,
            },
            history=[],
        )

        update_state = self.stateUpdate.update(state, goodbye_act)

        self.assertEqual(update_state.slots["goodbye_stage"], 0)
        self.assertEqual(update_state.slots["confirm_goodbye"], False)
        self.assertEqual(update_state.slots["goodbye"], False)
        self.assertEqual(update_state.slots["specify"], expected_specify)
        self.assertEqual(update_state.resultList, [])

    def test_goodbye_confirmation_answer_not_yes_no(self):
        state = DialogueState(get_default_slots(), [get_greet_act()])
        state.slots["goodbye_stage"] = 1
        state.slots["specify"] = {
            "food": [
                {
                    "string": "italian (0.992951), romanian (0.636907), portuguese (0.633602), european (0.625143), australian (0.475629), catalan (0.452122)",
                    "negated": False,
                    "confidence": 1.0,
                    "backup_for": None,
                }
            ],
            "pricerange": [],
            "name": [],
            "area": [],
        }

        expected_specify = {
            "food": [
                {
                    "string": "italian (0.992951), romanian (0.636907), portuguese (0.633602), european (0.625143), australian (0.475629), catalan (0.452122)",
                    "negated": False,
                    "confidence": 1.0,
                    "backup_for": None,
                }
            ],
            "pricerange": [],
            "name": [],
            "area": [],
        }

        goodbye_act = DialogueAct(
            intent="bye",
            slots={
                "answer": "I think I want to continue",
                "goodbye": False,
                "specify": {
                    "food": [],
                    "pricerange": [],
                    "area": [],
                    "name": [],
                },
                "user_question": None,
                "inform": [],
                "greeting": "",
                "dont_like_choice": False,
                "confirm_goodbye": False,
                "user_prompt": None,
                "n_failures": 0,
            },
            history=[],
        )

        update_state = self.stateUpdate.update(state, goodbye_act)

        self.assertEqual(update_state.slots["goodbye_stage"], 0)
        self.assertEqual(update_state.slots["confirm_goodbye"], False)
        self.assertEqual(update_state.slots["goodbye"], False)
        self.assertEqual(update_state.slots["specify"], expected_specify)
        self.assertEqual(update_state.resultList, [])

    """ -----------Test: Alternative Result gets recoginized correctly------------"""

    def test_alternative_result_inform(self):
        state = DialogueState(get_default_slots(), [get_greet_act()])

        user_act = DialogueAct(
            intent="inform",
            slots={
                "answer": "",
                "goodbye": False,
                "specify": {
                    "area": [
                        {
                            "string": "north",
                            "negated": False,
                            "confidence": 1.0,
                            "backup_for": None,
                        }
                    ],
                    "food": [
                        {
                            "string": "italian",
                            "negated": False,
                            "confidence": 1.0,
                            "backup_for": None,
                        }
                    ],
                    "pricerange": [
                        {
                            "string": "expensive",
                            "negated": False,
                            "confidence": 1.0,
                            "backup_for": None,
                        },
                    ],
                    "name": [],
                },
                "user_question": None,
                "inform": [],
                "greeting": "",
                "dont_like_choice": False,
                "confirm_goodbye": False,
                "alternative_result": False,
                "user_prompt": None,
                "n_failures": 0,
            },
            history=[],
        )

        def mock_restaurant_database_lookup(slot_values, state):
            return (
                [
                    {
                        "id": "19176",
                        "name": "clowns cafe",
                        "addr": "54 king street city centre",
                        "area": "centre",
                        "food": "italian",
                        "phone": "01223 355711",
                        "pricerange": "expensive",
                        "postcode": "c.b 1, 1 l.n",
                        "signature": "not available",
                        "description": "clowns cafe serve a variety of drinks as well as italian dishes such as pasta ciabatta and salads",
                    }
                ],
                {"area": "centre", "pricerange": "expensive", "food": "italian"},
                0.9,
            )

        self.stateUpdate.find_top_restaurant = (
            mock_restaurant_database_lookup  # anpassen!
        )

        updated_state = self.stateUpdate.update(state, user_act)

        self.assertIn("alternative_result", updated_state.slots)
        self.assertTrue(updated_state.slots["alternative_result"])

    # def test_alternative_result_with_wildcard(self):

    # def test_alternative_result_with_negation(self):
    #  state = DialogueState(get_default_slots(), [get_greet_act()])

    def test_no_result_found_in_database(self):
        state = DialogueState(get_default_slots(), [get_greet_act()])
        state = self.stateUpdate.update(
            act=self.nlu.parse("I want german food in the north that should be cheap"),
            state=state,
        )

        self.assertEqual(state.resultList, [])
        # self.assertTrue(state.slots.get("no_result", False))
        self.assertFalse(state.slots.get("alternative_result", False))

    def test_count_matching_slots_counts_correctly(self):
        slot_types = {
            "food": [{"string": "chinese", "negated": False, "backup_for": ""}],
            "area": [{"string": "centre", "negated": False, "backup_for": ""}],
            "pricerange": [{"string": "cheap", "negated": False, "backup_for": ""}],
        }
        state = DialogueState(get_default_slots(), [get_greet_act()])

        state.slots["specify"]["food"].append({"string": "chinese"})
        state.slots["specify"]["area"].append({"string": "centre"})
        state.slots["specify"]["pricerange"].append({"string": "moderate"})

        matcher = SimpleStateUpdater()
        match_count = matcher.count_matching_slots(slot_types, state)

        assert match_count == 2

    def test_count_matching_slots_with_wildcard(self):
        slot_types = {
            "food": [{"string": "chinese", "negated": False, "backup_for": "*"}],
            "area": [{"string": "centre", "negated": False, "backup_for": ""}],
            "pricerange": [{"string": "cheap", "negated": False, "backup_for": ""}],
        }

        state = DialogueState(get_default_slots(), [get_greet_act()])

        state.slots["specify"]["food"].append({"string": "indian"})
        state.slots["specify"]["area"].append({"string": "centre"})
        state.slots["specify"]["pricerange"].append({"string": "cheap"})

        matcher = SimpleStateUpdater()
        result = matcher.count_matching_slots(slot_types, state)

        # "food" counts because of wildcard, area & pricerange match exactly
        assert result == 3

    def test_count_matching_slots_with_negation(self):
        slot_types = {
            "food": [
                {"string": "chinese", "negated": True, "backup_for": ""}
            ],  # in get_options if something is negated but nothing else is specified it is wildcard witout negated options
            "area": [{"string": "centre", "negated": False, "backup_for": ""}],
            "pricerange": [{"string": "cheap", "negated": False, "backup_for": ""}],
        }

        state = DialogueState(get_default_slots(), [get_greet_act()])
        state.slots["specify"]["food"].append({"string": "chinese"})  # match ignored
        state.slots["specify"]["area"].append({"string": "centre"})
        state.slots["specify"]["pricerange"].append({"string": "cheap"})

        matcher = SimpleStateUpdater()
        result = matcher.count_matching_slots(slot_types, state)

        # food is negated and must be ignored -> only 2 match
        assert result == 2

    def test_count_matching_slots_with_negation_and_wildcard(self):
        # chinese food is negated, but implicitly a wildcard: so everytihng except chinese should count/match
        slot_types = {
            "food": [{"string": "italian", "negated": True, "backup_for": "*"}],
            "area": [{"string": "centre", "negated": False, "backup_for": ""}],
            "pricerange": [{"string": "cheap", "negated": False, "backup_for": ""}],
        }

        state = DialogueState(get_default_slots(), [get_greet_act()])
        state.slots["specify"]["food"].append(
            {"string": "chinese"}
        )  # match should be valid for food, because of wildcard (italian is NOT chinese, user only does not want chinese therefore backup_for is "*" set by get_options)
        state.slots["specify"]["area"].append({"string": "centre"})
        state.slots["specify"]["pricerange"].append({"string": "cheap"})

        matcher = SimpleStateUpdater()
        result = matcher.count_matching_slots(slot_types, state)
        assert result == 3

    """-----Test case: User names required slot after restaurant name result  ------ """

    def test_reset_state_after_required_slot_input(self):
        """-----Test case: User names required slot after restaurant name result -----"""

        # Step 1: User gives a restaurant name
        state = DialogueState(get_default_slots(), [get_greet_act()])
        act1 = self.nlu.parse("i want to eat in Yu Garden")
        state = self.stateUpdate.update(state, act1)

        # Confirm that the restaurant result is found
        self.assertTrue(len(state.resultList) > 0)
        self.assertEqual(state.resultList[0]["name"], "Yu Garden")
        self.assertEqual(state.found_params.get("name"), "Yu Garden")

        # Step 2: User inputs a new required slot (e.g. food type)
        act2 = self.nlu.parse("i want to eat italian")
        state = self.stateUpdate.update(state, act2)

        # Assert that the state was reset:
        # 1. resultList should be empty (or changed)
        # self.assertTrue(
        #     state.resultList == [] or state.resultList[0]["name"] != "Yu Garden"
        # )

        # 2. name slot should be cleared
        self.assertEqual(state.slots["specify"]["name"], [])

        # 3. food slot should now include 'italian'
        self.assertTrue(state.slots["specify"]["food"])
        self.assertIn("italian", state.slots["specify"]["food"][0]["string"].lower())

    """-----Test Case: Handling user questions (what pricerange)  ------ """

    def test_user_question_about_pricerange(self):
        # Step 1: Simulate user asking about price ranges using NLU
        user_input = "what are possible price ranges?"
        act = self.nlu.parse(user_input)

        # Step 2: Update the dialogue state
        state = DialogueState(get_default_slots(), [get_greet_act()])
        updated_state = self.stateUpdate.update(state, act)

        # Step 3: Assert user_question is recognized and stored correctly
        self.assertEqual(updated_state.slots["user_question"], "WHAT_PRICERANGE")

    """-----Test Case: Handling user questions (what area)  ------ """

    def test_user_question_about_pricerange(self):
        user_input = "What are the areas?"
        act = self.nlu.parse(user_input)

        state = DialogueState(get_default_slots(), [get_greet_act()])
        updated_state = self.stateUpdate.update(state, act)

        self.assertEqual(updated_state.slots["user_question"], "WHAT_AREA")

    """-----Test Case: Handling user questions (what food type)  ------ """

    def test_user_question_about_food(self):
        user_input = "Which types of food are there?"
        act = self.nlu.parse(user_input)

        state = DialogueState(get_default_slots(), [get_greet_act()])
        updated_state = self.stateUpdate.update(state, act)

        self.assertEqual(updated_state.slots["user_question"], "WHAT_FOOD")

    """-----Test Case: Handling user questions (what can you do)  ------ """

    def test_user_question_about_what_can_you_do(self):
        user_input = "What can you do?"
        act = self.nlu.parse(user_input)

        state = DialogueState(get_default_slots(), [get_greet_act()])
        updated_state = self.stateUpdate.update(state, act)

        self.assertEqual(updated_state.slots["user_question"], "WHAT_CAN_YOU_DO")

    """-----Test Case: Handling user questions (how to use)  ------ """

    def test_user_question_about_what_can_you_do(self):
        user_input = "How should I use this bot?"
        act = self.nlu.parse(user_input)

        state = DialogueState(get_default_slots(), [get_greet_act()])
        updated_state = self.stateUpdate.update(state, act)

        self.assertEqual(updated_state.slots["user_question"], "HOW_TO_USE")

    """-----Test Case: Handling user questions (OUT_OF_SCOPE)  ------ """

    def test_user_question_about_out_of_scope(self):
        user_input = "Can you order food for me?"
        act = self.nlu.parse(user_input)

        state = DialogueState(get_default_slots(), [get_greet_act()])
        updated_state = self.stateUpdate.update(state, act)

        self.assertEqual(updated_state.slots["user_question"], "OUT_OF_SCOPE")

    """-----Test Case: Handling user questions (RESTAURANT_NUMBER)  ------ """

    def test_user_question_about_retaurant_number(self):
        user_input = "How many restaurants are there to choose from?"
        act = self.nlu.parse(user_input)

        state = DialogueState(get_default_slots(), [get_greet_act()])
        updated_state = self.stateUpdate.update(state, act)

        self.assertEqual(updated_state.slots["user_question"], "RESTAURANT_NUMBER")
