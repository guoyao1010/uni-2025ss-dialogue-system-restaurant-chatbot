import unittest
import re
from datastructures.dialogueact import DialogueAct
from datastructures.dialoguestate import DialogueState
from datastructures.defaults import get_greet_act
from languagegeneration.generators import SimpleGenerator
from languagegeneration.answer_templates import TEMPLATES
from database.database import Database

database = Database()


class TestNLG(unittest.TestCase):
    def setUp(self):
        self.nlg = SimpleGenerator()

    # Other Act_types (goodbye_confirm, goodbye)
    def test_goodbye_confirm(self):
        systemaction = DialogueAct(
            "confirm",
            {"act_slot": "goodbye", "template_value_list": {}},
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        assert any(
            output.startswith(t) for t in TEMPLATES["confirm"].values()
        ), f"Unexpected output: '{output}'"

    def test_goodbye(self):
        systemaction = DialogueAct("goodbye", {}, history=[get_greet_act])
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        assert any(
            output.startswith(t) for t in TEMPLATES["goodbye"].values()
        ), f"Unexpected output: '{output}'"

    # All tests with act_type "ask"
    def test_ask_slot_value_food(self):
        systemaction = DialogueAct(
            "ask",
            {
                "act_slot": "food",
                "template_value_list": None,
                "greeting": None,  # greet
                "any_new_negation_is_wildcard": False,  # wenn true, echte negetion. Wenn false, keine negeation
                "user_question": None,  # user_question
                "is_new_dont_care": False,  # dont_care
                "new_slot_select": False,  # new_select
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        assert any(TEMPLATES["ask"][f"food{i}"] in output for i in range(3))

    def test_ask_slot_value_area(self):
        systemaction = DialogueAct(
            "ask",
            {
                "act_slot": "area",
                "template_value_list": None,
                "greeting": None,  # greet
                "any_new_negation_is_wildcard": False,  # wenn true, echte negetion. Wenn false, keine negeation
                "user_question": None,  # user_question
                "is_new_dont_care": False,  # dont_care
                "new_slot_select": False,  # new_select
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        assert any(TEMPLATES["ask"][f"area{i}"] in output for i in range(3))

    def test_ask_slot_value_pricerange(self):
        systemaction = DialogueAct(
            "ask",
            {
                "act_slot": "pricerange",
                "template_value_list": None,
                "greeting": None,  # greet
                "any_new_negation_is_wildcard": False,  # wenn true, echte negetion. Wenn false, keine negeation
                "user_question": None,  # user_question
                "is_new_dont_care": False,  # dont_care
                "new_slot_select": False,  # new_select
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        assert any(TEMPLATES["ask"][f"pricerange{i}"] in output for i in range(3))

    def test_user_question_food(self):
        systemaction = DialogueAct(
            "ask",
            {
                "act_slot": "pricerange",
                "template_value_list": None,
                "greeting": None,  # greet
                "any_new_negation_is_wildcard": False,  # wenn true, echte negetion. Wenn false, keine negeation
                "user_question": "WHAT_FOOD",  # user_question
                "is_new_dont_care": False,  # dont_care
                "new_slot_select": False,  # new_select
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        # erwartet: eine von den drei antworten auf Frage
        # außerdem erwartet: eine von den neun Fragen zum slot value.
        assert any(
            output.startswith(t)
            for t in (
                "There are over 20 possible food types.",
                "More than 20 food types are available.",
                "You can choose from over 20 cuisines.",
            )
        ), f"Output did not start with expected WHAT_FOOD prefix: {output}"

        # Extract the food types from the sentence
        match = re.search(r":\s*(.+?),\s*(.+?)\s+or\s+(.+?)\.", output)
        assert match, f"Could not extract food types from output: {output}"
        food1, food2, food3 = match.groups()

        # Validate that we got 3 non-empty and distinct food examples
        for food in [food1, food2, food3]:
            assert food and isinstance(
                food, str
            ), f"One of the food examples is invalid: {food}"
        assert (
            len({food1, food2, food3}) == 3
        ), f"Food examples are not distinct: {food1}, {food2}, {food3}"

        # Check that the food types are actually present in the database
        valid_foods = set(database.get_all_attribute_values("food"))
        for food in [food1, food2, food3]:
            assert (
                food in valid_foods
            ), f"Extracted food type '{food}' not found in database list: {valid_foods}"

        # Check if system asks for slot value
        assert any(
            template in output
            for i in range(3)
            for template in [
                TEMPLATES["ask"][f"food{i}"],
                TEMPLATES["ask"][f"area{i}"],
                TEMPLATES["ask"][f"pricerange{i}"],
            ]
        ), f"Output did not contain any expected ask templates: {output}"

    def test_user_question_area(self):
        systemaction = DialogueAct(
            "ask",
            {
                "act_slot": "pricerange",
                "template_value_list": None,
                "greeting": None,  # greet
                "any_new_negation_is_wildcard": False,  # wenn true, echte negetion. Wenn false, keine negeation
                "user_question": "WHAT_AREA",  # user_question
                "is_new_dont_care": False,  # dont_care
                "new_slot_select": False,  # new_select
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        assert any(
            TEMPLATES["user_question"][f"WHAT_AREA{i}"] in output for i in range(3)
        )
        # expects: one of three answers from WHAT_AREA
        # second expect: asking for a slot value.
        assert any(
            template in output
            for i in range(3)
            for template in [
                TEMPLATES["ask"][f"food{i}"],
                TEMPLATES["ask"][f"area{i}"],
                TEMPLATES["ask"][f"pricerange{i}"],
            ]
        ), f"Output did not contain any expected ask templates: {output}"

    def test_user_question_pricerange(self):
        systemaction = DialogueAct(
            "ask",
            {
                "act_slot": "pricerange",
                "template_value_list": None,
                "greeting": None,  # greet
                "any_new_negation_is_wildcard": False,  # wenn true, echte negetion. Wenn false, keine negeation
                "user_question": "WHAT_PRICERANGE",  # user_question
                "is_new_dont_care": False,  # dont_care
                "new_slot_select": False,  # new_select
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        assert any(
            TEMPLATES["user_question"][f"WHAT_PRICERANGE{i}"] in output
            for i in range(3)
        )
        # erwartet: eine von den drei antworten auf die Frage
        # außerdem erwartet: eine von den neun Fragen zum slot value.
        assert any(
            template in output
            for i in range(3)
            for template in [
                TEMPLATES["ask"][f"food{i}"],
                TEMPLATES["ask"][f"area{i}"],
                TEMPLATES["ask"][f"pricerange{i}"],
            ]
        ), f"Output did not contain any expected ask templates: {output}"

    def test_user_question_what_can_you_do(self):
        systemaction = DialogueAct(
            "ask",
            {
                "act_slot": "pricerange",
                "template_value_list": None,
                "greeting": None,  # greet
                "any_new_negation_is_wildcard": False,  # wenn true, echte negetion. Wenn false, keine negeation
                "user_question": "WHAT_CAN_YOU_DO",  # user_question
                "is_new_dont_care": False,  # dont_care
                "new_slot_select": False,  # new_select
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        assert any(
            TEMPLATES["user_question"][f"WHAT_CAN_YOU_DO{i}"] in output
            for i in range(3)
        )
        # erwartet: eine von den drei antworten auf die Frage
        # außerdem erwartet: eine von den neun Fragen zum slot value.
        assert any(
            template in output
            for i in range(3)
            for template in [
                TEMPLATES["ask"][f"food{i}"],
                TEMPLATES["ask"][f"area{i}"],
                TEMPLATES["ask"][f"pricerange{i}"],
            ]
        ), f"Output did not contain any expected ask templates: {output}"

    def test_user_question_how_to_use(self):
        systemaction = DialogueAct(
            "ask",
            {
                "act_slot": "pricerange",
                "template_value_list": None,
                "greeting": None,  # greet
                "any_new_negation_is_wildcard": False,  # wenn true, echte negetion. Wenn false, keine negeation
                "user_question": "HOW_TO_USE",  # user_question
                "is_new_dont_care": False,  # dont_care
                "new_slot_select": False,  # new_select
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        assert any(
            TEMPLATES["user_question"][f"HOW_TO_USE{i}"] in output for i in range(3)
        )
        # erwartet: eine von den drei antworten auf die Frage
        # außerdem erwartet: eine von den neun Fragen zum slot value.
        assert any(
            template in output
            for i in range(3)
            for template in [
                TEMPLATES["ask"][f"food{i}"],
                TEMPLATES["ask"][f"area{i}"],
                TEMPLATES["ask"][f"pricerange{i}"],
            ]
        ), f"Output did not contain any expected ask templates: {output}"

    def test_user_question_out_of_scope(self):
        systemaction = DialogueAct(
            "ask",
            {
                "act_slot": "pricerange",
                "template_value_list": None,
                "greeting": None,  # greet
                "any_new_negation_is_wildcard": False,  # wenn true, echte negetion. Wenn false, keine negeation
                "user_question": "OUT_OF_SCOPE",  # user_question
                "is_new_dont_care": False,  # dont_care
                "new_slot_select": False,  # new_select
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        assert any(
            TEMPLATES["user_question"][f"OUT_OF_SCOPE{i}"] in output for i in range(3)
        )
        # erwartet: eine von den drei antworten auf die Frage
        # außerdem erwartet: eine von den neun Fragen zum slot value.
        assert any(
            template in output
            for i in range(3)
            for template in [
                TEMPLATES["ask"][f"food{i}"],
                TEMPLATES["ask"][f"area{i}"],
                TEMPLATES["ask"][f"pricerange{i}"],
            ]
        ), f"Output did not contain any expected ask templates: {output}"

    def test_user_question_restaurant_number(self):
        systemaction = DialogueAct(
            "ask",
            {
                "act_slot": "pricerange",
                "template_value_list": None,
                "greeting": None,  # greet
                "any_new_negation_is_wildcard": False,  # wenn true, echte negetion. Wenn false, keine negeation
                "user_question": "RESTAURANT_NUMBER",  # user_question
                "is_new_dont_care": False,  # dont_care
                "new_slot_select": False,  # new_select
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        assert any(
            TEMPLATES["user_question"][f"RESTAURANT_NUMBER{i}"] in output
            for i in range(3)
        )
        # erwartet: eine von den drei antworten auf WHAT_AREA
        # außerdem erwartet: eine von den neun Fragen zum slot value.
        assert any(
            template in output
            for i in range(3)
            for template in [
                TEMPLATES["ask"][f"food{i}"],
                TEMPLATES["ask"][f"area{i}"],
                TEMPLATES["ask"][f"pricerange{i}"],
            ]
        ), f"Output did not contain any expected ask templates: {output}"

    # still act_type "ask", testing confirmations
    def test_dont_care_confirm(self):
        systemaction = DialogueAct(
            "ask",
            {
                "act_slot": "area",
                "template_value_list": None,
                "greeting": None,  # greet
                "any_new_negation_is_wildcard": True,  # wenn true, echte negetion. Wenn false, keine negeation
                "user_question": None,  # user_question
                "is_new_dont_care": True,  # dont_care
                "new_slot_select": True,  # new_select
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        # erwartung ist, dass die negation bestätigt wird, dann eine der fragen zum slot pricerange
        self.assertIsInstance(output, str)
        assert any(
            output.startswith(t) for t in TEMPLATES["dont_care"].values()
        ), f"Unexpected output: '{output}'"
        assert any(TEMPLATES["ask"][f"area{i}"] in output for i in range(3))

    def test_exclusion_confirm(self):
        systemaction = DialogueAct(
            "ask",
            {
                "act_slot": "area",
                "template_value_list": None,
                "greeting": None,  # greet
                "any_new_negation_is_wildcard": True,  # wenn true, echte negetion. Wenn false, keine negeation
                "user_question": None,  # user_question
                "is_new_dont_care": False,  # dont_care
                "new_slot_select": True,  # new_select
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        # erwartung ist, dass die negation bestätigt wird, dann eine der fragen zum slot pricerange
        self.assertIsInstance(output, str)
        assert any(
            output.startswith(t) for t in TEMPLATES["deny"].values()
        ), f"Unexpected output: '{output}'"
        assert any(TEMPLATES["ask"][f"area{i}"] in output for i in range(3))

    def test_selection_confirm(self):
        systemaction = DialogueAct(
            "ask",
            {
                "act_slot": "pricerange",
                "template_value_list": None,
                "greeting": None,  # greet
                "any_new_negation_is_wildcard": False,  # wenn true, echte negetion. Wenn false, keine negeation
                "user_question": None,  # user_question
                "is_new_dont_care": False,  # dont_care
                "new_slot_select": True,  # new_select
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        # erwartung ist, dass die negation bestätigt wird, dann eine der fragen zum slot pricerange
        self.assertIsInstance(output, str)
        assert any(
            output.startswith(t) for t in TEMPLATES["confirm_select"].values()
        ), f"Unexpected output: '{output}'"
        assert any(TEMPLATES["ask"][f"pricerange{i}"] in output for i in range(3))

    def test_greet_back(self):
        systemaction = DialogueAct(
            "ask",
            {
                "act_slot": "pricerange",
                "template_value_list": None,
                "greeting": "Hi",  # greet
                "any_new_negation_is_wildcard": False,  # wenn true, echte negetion. Wenn false, keine negeation
                "user_question": None,  # user_question
                "is_new_dont_care": False,  # dont_care
                "new_slot_select": True,  # new_select
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        # expenctaion: starts with greeting "Hi".
        # other expectation: the sot question for pricerange is included.
        greeting = "Hi."
        self.assertTrue(
            output.startswith(greeting),
            f"Output does not start with expected greeting: {output}",
        )
        assert any(TEMPLATES["ask"][f"pricerange{i}"] in output for i in range(3))

    def test_all_conversation_extensions_at_once(self):
        systemaction = DialogueAct(
            "ask",
            {
                "act_slot": "pricerange",
                "template_value_list": None,
                "greeting": "Hi",  # greet
                "any_new_negation_is_wildcard": True,  # wenn true, echte negetion. Wenn false, keine negeation
                "user_question": "WHAT_AREA",  # user_question
                "is_new_dont_care": False,  # dont_care
                "new_slot_select": True,  # new_select
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        # expenctaion: starts with greeting "Hi".
        # exp: the negation is confirmed
        # exp: The user question is answered
        # other expectation: the sot question for pricerange is included.
        greeting = "Hi."
        self.assertTrue(
            output.startswith(greeting),
            f"Output does not start with expected greeting: {output}",
        )
        assert any(
            val in output for val in TEMPLATES["deny"].values()
        ), f"Unexpected output: '{output}'"
        assert any(
            TEMPLATES["user_question"][f"WHAT_AREA{i}"] in output for i in range(3)
        )
        assert any(TEMPLATES["ask"][f"pricerange{i}"] in output for i in range(3))

    # All tests with act_type "inform"
    def test_inform_result(self):
        systemaction = DialogueAct(
            "inform",
            {
                "act_slot": "result",
                "template_value_list": {
                    "food": "italian",
                    "pricerange": "moderate",
                    "area": "north",
                    "name": "Luigi's",
                    "address": "123 Pasta Lane",
                },
                "greeting": None,
                "user_question": None,
                "any_new_negation_is_wildcard": False,
                "is_new_dont_care": False,
                "new_slot_select": False,  # dieser fall sollte in ect nie eintreten. hier geht es darum, getrennt zu testen
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        # erw: auswahl des richtigen templates (inform, result) - > startswith?
        # die daten aus der tempalte value list sind enthalten.
        assert any(
            phrase in output for phrase in ("I found a ", "There's a", "You might like")
        ), f"Assertion failed. Output was: {output}"
        self.assertIn("italian", output)  # müsste doch in lowercase ausgegeben werden
        self.assertIn(
            "moderately priced", output
        )  # testet moderately priced gleich mit
        self.assertIn("moderately priced", output)
        self.assertIn("north", output)
        self.assertIn("123 Pasta Lane", output)

    # todos
    def test_inform_alternative_result(self):
        systemaction = DialogueAct(
            "inform",
            {
                "act_slot": "alternative_result",
                "template_value_list": {
                    "food": "italian",
                    "pricerange": "moderate",
                    "area": "north",
                    "name": "Luigi's",
                    "address": "123 Pasta Lane",
                },
                "greeting": None,
                "user_question": None,
                "any_new_negation_is_wildcard": False,
                "is_new_dont_care": False,
                "new_slot_select": False,  # dieser fall sollte in ect nie eintreten. hier geht es darum, getrennt zu testen
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        # erw: auswahl des richtigen templates (inform, result) - > startswith?
        # die daten aus der tempalte value list sind enthalten.
        assert any(
            phrase in output
            for phrase in (
                "Unfortunately I could not find a restaurant that exactly fits your preferences.",
                "I wasn't able to find a perfect match, but I did find a",
                "No exact match was found, but there is a",
            )
        ), f"Assertion failed. Output was: {output}"
        self.assertIn("italian", output)  # müsste doch in lowercase ausgegeben werden
        self.assertIn(
            "moderately priced", output
        )  # testet moderately priced gleich mit
        self.assertIn("north", output)
        self.assertIn("Luigi's", output)
        self.assertIn("123 Pasta Lane", output)

    def test_inform_result_by_name(self):
        systemaction = DialogueAct(
            "inform",
            {
                "act_slot": "result_by_name",
                "template_value_list": {
                    "food": "italian",
                    "pricerange": "moderate",
                    "area": "north",
                    "name": "Luigi's",
                    "address": "123 Pasta Lane",
                },
                "greeting": None,
                "is_new_negated": False,
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        # erw: auswahl des richtigen templates (inform, result) - > startswith?
        # die daten aus der tempalte value list sind enthalten.
        assert any(
            phrase in output
            for phrase in (
                "I found the restaurant you wanted",
                "The restaurant you're looking for is",
                "'Luigi's' is the place you asked for",
            )
        ), f"Assertion failed. Output was: {output}"
        self.assertIn("italian", output)  # müsste doch in lowercase ausgegeben werden
        self.assertIn(
            "moderately priced", output
        )  # testet moderately priced gleich mit
        self.assertIn("Luigi's", output)
        self.assertIn("123 Pasta Lane", output)

    def test_inform_no_result(self):
        systemaction = DialogueAct(
            "inform",
            {
                "act_slot": "no_result",
                "template_value_list": {
                    "food": "italian",
                    "pricerange": "moderate",
                    "area": "north",
                },
                "greeting": None,  # greet
                "is_new_negated": False,
                "any_new_negation_is_wildcard": False,  # wenn true, echte negetion. Wenn false, keine negeation
                "user_question": None,  # user_question
                "is_new_dont_care": False,  # dont_care
                "new_slot_select": False,  # new_select
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        # erw: auswahl des richtigen templates (inform, result) - > startswith?
        # die daten aus der tempalte value list sind enthalten.
        assert any(
            phrase in output
            for phrase in (
                "I'm sorry, I couldn't find any",
                "Unfortunately, there are no",
                "I couldn't locate a",
            )
        ), f"Assertion failed. Output was: {output}"
        self.assertIn("italian", output)  # müsste doch in lowercase ausgegeben werden
        self.assertIn(
            "moderately priced", output
        )  # testet moderately priced gleich mit
        self.assertIn("north", output)

    # inform with additional info
    def test_inform_phone(self):
        systemaction = DialogueAct(
            "inform",
            {
                "act_slot": "phone",
                "template_value_list": {
                    "food": "italian",
                    "pricerange": "cheap",
                    "area": "east",
                    "name": "Pizza Paradise",
                    "address": "Example Lane 123",
                    "phone": "0123 456 778",
                    "signature": "Bruscetta",
                    "description": "Stable italian fusion kitchen, with fresh ingredients, baked and cooked with love.",
                },
                "greeting": None,
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        assert any(
            output.startswith(t)
            for t in (
                "The phone number",
                "You can reach",
                "Pizza Paradise can be contacted",
            )
        ), f"Unexpected sentence start. Got output:\n{output}"
        self.assertIn(
            "Pizza Paradise",
            output,
            f"The restaurant name'Pizza Paradise' was not found in output:\n{output}",
        )
        self.assertIn("0123 456 778", output)

    def test_inform_no_phone(self):
        systemaction = DialogueAct(
            "inform",
            {
                "act_slot": "no_phone",
                "template_value_list": {
                    "food": "italian",
                    "pricerange": "cheap",
                    "area": "east",
                    "name": "Pizza Paradise",
                    "address": "Example Lane 123",
                    "phone": "0123 456 778",
                    "signature": "Bruscetta",
                    "description": "Stable italian fusion kitchen, with fresh ingredients, baked and cooked with love.",
                },
                "greeting": None,
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        assert any(
            output.startswith(t)
            for t in (
                "I'm sorry but",
                "Unfortunately, there’s no phone",
                "Pizza Paradise doesn't seem to have a listed phone",
            )
        ), f"Unexpected sentence start. Got output:\n{output}"
        self.assertIn(
            "Pizza Paradise",
            output,
            f"The restaurant name'Pizza Paradise' was not found in output:\n{output}",
        )

    def test_inform_signature(self):
        systemaction = DialogueAct(
            "inform",
            {
                "act_slot": "signature",
                "template_value_list": {
                    "food": "italian",
                    "pricerange": "cheap",
                    "area": "east",
                    "name": "Pizza Paradise",
                    "address": "Example Lane 123",
                    "phone": "0123 456 778",
                    "signature": "Bruscetta",
                    "description": "Stable italian fusion kitchen, with fresh ingredients, baked and cooked with love.",
                },
                "greeting": None,
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        assert any(
            output.startswith(t)
            for t in (
                "The signature dish of",
                "Pizza Paradise's signature dish is",
                "You should try the signature dish at",
            )
        ), f"Unexpected sentence start. Got output:\n{output}"
        self.assertIn(
            "Pizza Paradise",
            output,
            f"The restaurant name'Pizza Paradise' was not found in output:\n{output}",
        )
        self.assertIn(
            "Bruscetta",
            output,
        )

    def test_inform_no_signature(self):
        systemaction = DialogueAct(
            "inform",
            {
                "act_slot": "no_signature",
                "template_value_list": {
                    "food": "italian",
                    "pricerange": "cheap",
                    "area": "east",
                    "name": "Pizza Paradise",
                    "address": "Example Lane 123",
                    "phone": "0123 456 778",
                    "signature": "Bruscetta",
                    "description": "Stable italian fusion kitchen, with fresh ingredients, baked and cooked with love.",
                },
                "greeting": None,
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        assert any(
            output.startswith(t)
            for t in (
                "Sorry, Pizza Paradise has no signature",
                "Unfortunately, there’s no signature dish",
                "I couldn’t find a signature dish for",
            )
        ), f"Unexpected sentence start. Got output:\n{output}"
        self.assertIn(
            "Pizza Paradise",
            output,
            f"The restaurant name'Pizza Paradise' was not found in output:\n{output}",
        )

    def test_inform_description(self):
        systemaction = DialogueAct(
            "inform",
            {
                "act_slot": "description",
                "template_value_list": {
                    "food": "italian",
                    "pricerange": "cheap",
                    "area": "east",
                    "name": "Pizza Paradise",
                    "address": "Example Lane 123",
                    "phone": "0123 456 778",
                    "signature": "Bruscetta",
                    "description": "Stable italian fusion kitchen, with fresh ingredients, baked and cooked with love.",
                },
                "greeting": None,
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        assert any(
            output.startswith(t)
            for t in (
                "Happy to tell you more!",
                "Sure! Here's some more info:",
                "Here's what I know:",
            )
        ), f"Unexpected sentence start. Got output:\n{output}"
        self.assertIn(
            "Stable italian fusion kitchen, with fresh ingredients, baked and cooked with love.",
            output,
        )

    def test_inform_no_desciption(self):
        systemaction = DialogueAct(
            "inform",
            {
                "act_slot": "no_description",
                "template_value_list": {
                    "food": "italian",
                    "pricerange": "cheap",
                    "area": "east",
                    "name": "Pizza Paradise",
                    "address": "Example Lane 123",
                    "phone": "0123 456 778",
                    "signature": "Bruscetta",
                    "description": "Stable italian fusion kitchen, with fresh ingredients, baked and cooked with love.",
                },
                "greeting": None,
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        assert any(
            output.startswith(t)
            for t in (
                "I'm sorry to inform you that",
                "Unfortunately, there's no further description",
                "I couldn’t find any additional information",
            )
        ), f"Unexpected sentence start. Got output:\n{output}"
        self.assertIn(
            "Pizza Paradise",
            output,
        )

    # Sonderfall: hier wird eine Liste von DialogueActs übergeben. Wie stelle ich die dar?
    def test_inform_additional_info_all(self):
        systemaction = [
            DialogueAct(
                "inform",
                {
                    "act_slot": "description",
                    "template_value_list": {
                        "food": "italian",
                        "pricerange": "cheap",
                        "area": "east",
                        "name": "Pizza Paradise",
                        "address": "Example Lane 123",
                        "phone": "0123 456 778",
                        "signature": "Bruscetta",
                        "description": "Stable italian fusion kitchen, with fresh ingredients, baked and cooked with love.",
                    },
                    "greeting": None,
                },
                history=[get_greet_act],
            ),
            DialogueAct(
                "inform",
                {
                    "act_slot": "phone",
                    "template_value_list": {
                        "food": "italian",
                        "pricerange": "cheap",
                        "area": "east",
                        "name": "Pizza Paradise",
                        "address": "Example Lane 123",
                        "phone": "0123 456 778",
                        "signature": "Bruscetta",
                        "description": "Stable italian fusion kitchen, with fresh ingredients, baked and cooked with love.",
                    },
                    "greeting": None,
                },
                history=[get_greet_act],
            ),
            DialogueAct(
                "inform",
                {
                    "act_slot": "signature",
                    "template_value_list": {
                        "food": "italian",
                        "pricerange": "cheap",
                        "area": "east",
                        "name": "Pizza Paradise",
                        "address": "Example Lane 123",
                        "phone": "0123 456 778",
                        "signature": "Bruscetta",
                        "description": "Stable italian fusion kitchen, with fresh ingredients, baked and cooked with love.",
                    },
                    "greeting": None,
                },
                history=[get_greet_act],
            ),
        ]
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        # prüfen ob description starts are there
        assert any(
            phrase in output
            for phrase in (
                "Happy to tell you more!",
                "Sure! Here's some more info:",
                "Here's what I know:",
            )
        ), f"Unexpected sentence start. Got output:\n{output}"

        # prüfen ob phone antwort drin ist
        assert any(
            phrase in output
            for phrase in (
                "The phone number",
                "You can reach",
                "Pizza Paradise can be contacted",
            )
        ), f"Unexpected sentence start. Got output:\n{output}"

        # prüfen ob signature dish antwort drin ist
        assert any(
            phrase in output
            for phrase in (
                "The signature dish of",
                "Pizza Paradise's signature dish is",
                "You should try the signature dish at",
            )
        ), f"Unexpected sentence start. Got output:\n{output}"

        # prüfen ob name stimmt
        self.assertIn("Pizza Paradise", output)
        # prüfen ob description stimmt
        self.assertIn(
            "Stable italian fusion kitchen, with fresh ingredients, baked and cooked with love.",
            output,
        )
        # prüfen ob phone number stimmt
        self.assertIn("0123 456 778", output)
        # prüfen ob signature dish stimmt
        self.assertIn(
            "Bruscetta",
            output,
        )

    # immer noch act_type "inform", jetzt mit conversation extensions
    def test_inform_answer_user_question(self):
        systemaction = DialogueAct(
            "inform",
            {
                "act_slot": "result",
                "template_value_list": {
                    "food": "italian",
                    "pricerange": "moderate",
                    "area": "north",
                    "name": "Luigi's",
                    "address": "123 Pasta Lane",
                },
                "greeting": None,
                "user_question": "WHAT_AREA",
                "any_new_negation_is_wildcard": False,
                "is_new_dont_care": False,
                "new_slot_select": False,  # dieser fall sollte in ect nie eintreten. hier geht es darum, getrennt zu testen
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        # erw: auswahl des richtigen templates (inform, result) - > startswith?
        # die daten aus der tempalte value list sind enthalten.
        assert any(
            TEMPLATES["user_question"][f"WHAT_AREA{i}"] in output for i in range(3)
        )
        assert any(
            phrase in output for phrase in ("I found a ", "There's a", "You might like")
        ), f"Assertion failed. Output was: {output}"
        self.assertIn("italian", output)  # müsste doch in lowercase ausgegeben werden
        self.assertIn(
            "moderately priced", output
        )  # testet moderately priced gleich mit
        self.assertIn("moderately priced", output)
        self.assertIn("north", output)
        self.assertIn("123 Pasta Lane", output)

    def test_inform_dont_care_confirm(self):  # possible skip, can be integrated above
        systemaction = DialogueAct(
            "inform",
            {
                "act_slot": "result",
                "template_value_list": {
                    "food": "italian",
                    "pricerange": "moderate",
                    "area": "north",
                    "name": "Luigi's",
                    "address": "123 Pasta Lane",
                },
                "greeting": None,
                "user_question": None,
                "any_new_negation_is_wildcard": True,
                "is_new_dont_care": True,
                "new_slot_select": True,  # dieser fall sollte in ect nie eintreten. hier geht es darum, getrennt zu testen
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        # erw: auswahl des richtigen templates (inform, result) - > startswith?
        # die daten aus der tempalte value list sind enthalten.
        assert any(
            output.startswith(t) for t in TEMPLATES["dont_care"].values()
        ), f"Unexpected output: '{output}'"
        assert any(
            phrase in output for phrase in ("I found a ", "There's a", "You might like")
        ), f"Assertion failed. Output was: {output}"
        self.assertIn("italian", output)  # müsste doch in lowercase ausgegeben werden
        self.assertIn(
            "moderately priced", output
        )  # testet moderately priced gleich mit
        self.assertIn("moderately priced", output)
        self.assertIn("north", output)
        self.assertIn("123 Pasta Lane", output)

    def test_inform_exclusion_confirm(self):  # possible skip, can be integrated above
        systemaction = DialogueAct(
            "inform",
            {
                "act_slot": "result",
                "template_value_list": {
                    "food": "italian",
                    "pricerange": "moderate",
                    "area": "north",
                    "name": "Luigi's",
                    "address": "123 Pasta Lane",
                },
                "greeting": None,
                "user_question": None,
                "any_new_negation_is_wildcard": True,
                "is_new_dont_care": False,
                "new_slot_select": True,  # dieser fall sollte in ect nie eintreten. hier geht es darum, getrennt zu testen
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        # erw: auswahl des richtigen templates (inform, result) - > startswith?
        # die daten aus der tempalte value list sind enthalten.
        assert any(
            output.startswith(t) for t in TEMPLATES["deny"].values()
        ), f"Unexpected output: '{output}'"
        assert any(
            phrase in output for phrase in ("I found a ", "There's a", "You might like")
        ), f"Assertion failed. Output was: {output}"
        self.assertIn("italian", output)  # müsste doch in lowercase ausgegeben werden
        self.assertIn(
            "moderately priced", output
        )  # testet moderately priced gleich mit
        self.assertIn("moderately priced", output)
        self.assertIn("north", output)
        self.assertIn("123 Pasta Lane", output)

    def test_inform_selection_confirm(self):  # possibe skip, can be integrated above
        systemaction = DialogueAct(
            "inform",
            {
                "act_slot": "result",
                "template_value_list": {
                    "food": "italian",
                    "pricerange": "moderate",
                    "area": "north",
                    "name": "Luigi's",
                    "address": "123 Pasta Lane",
                },
                "greeting": None,
                "user_question": None,
                "any_new_negation_is_wildcard": False,
                "is_new_dont_care": False,
                "new_slot_select": True,  # dieser fall sollte in ect nie eintreten. hier geht es darum, getrennt zu testen
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        # erw: auswahl des richtigen templates (inform, result) - > startswith?
        # die daten aus der tempalte value list sind enthalten.
        assert any(
            output.startswith(t) for t in TEMPLATES["confirm_select"].values()
        ), f"Unexpected output: '{output}'"
        assert any(
            phrase in output for phrase in ("I found a ", "There's a", "You might like")
        ), f"Assertion failed. Output was: {output}"
        self.assertIn("italian", output)  # müsste doch in lowercase ausgegeben werden
        self.assertIn(
            "moderately priced", output
        )  # testet moderately priced gleich mit
        self.assertIn("moderately priced", output)
        self.assertIn("north", output)
        self.assertIn("123 Pasta Lane", output)

    def test_inform_greet_back(self):
        systemaction = DialogueAct(
            "inform",
            {
                "act_slot": "result",
                "template_value_list": {
                    "food": "italian",
                    "pricerange": "moderate",
                    "area": "north",
                    "name": "Luigi's",
                    "address": "123 Pasta Lane",
                },
                "greeting": None,
                "user_question": None,
                "any_new_negation_is_wildcard": False,
                "is_new_dont_care": False,
                "new_slot_select": True,  # dieser fall sollte in ect nie eintreten. hier geht es darum, getrennt zu testen
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        # erw: auswahl des richtigen templates (inform, result) - > startswith?
        # die daten aus der tempalte value list sind enthalten.
        assert any(
            output.startswith(t) for t in TEMPLATES["confirm_select"].values()
        ), f"Unexpected output: '{output}'"
        assert any(
            phrase in output for phrase in ("I found a ", "There's a", "You might like")
        ), f"Assertion failed. Output was: {output}"
        self.assertIn("italian", output)  # müsste doch in lowercase ausgegeben werden
        self.assertIn(
            "moderately priced", output
        )  # testet moderately priced gleich mit
        self.assertIn("moderately priced", output)
        self.assertIn("north", output)
        self.assertIn("123 Pasta Lane", output)

    def test_inform_conversation_extension_all_at_once(self):
        systemaction = DialogueAct(
            "inform",
            {
                "act_slot": "result",
                "template_value_list": {
                    "food": "italian",
                    "pricerange": "moderate",
                    "area": "north",
                    "name": "Luigi's",
                    "address": "123 Pasta Lane",
                },
                "greeting": "Hi",
                "user_question": "WHAT_PRICERANGE",
                "any_new_negation_is_wildcard": True,
                "is_new_dont_care": False,
                "new_slot_select": True,  # dieser fall sollte in ect nie eintreten. hier geht es darum, getrennt zu testen
            },
            history=[get_greet_act],
        )
        output = self.nlg.generate(systemaction)
        self.assertIsInstance(output, str)
        # erw: auswahl des richtigen templates (inform, result) - > startswith?
        # die daten aus der tempalte value list sind enthalten.
        # startswith grreting back
        greeting = "Hi."
        self.assertTrue(
            output.startswith(greeting),
            f"Output does not start with expected greeting: {output}",
        )
        assert any(
            val in output for val in TEMPLATES["deny"].values()
        ), f"Unexpected output: '{output}'"
        assert any(
            TEMPLATES["user_question"][f"WHAT_PRICERANGE{i}"] in output
            for i in range(3)
        )
        assert any(
            phrase in output for phrase in ("I found a ", "There's a", "You might like")
        ), f"Assertion failed. Output was: {output}"
        self.assertIn("italian", output)  # müsste doch in lowercase ausgegeben werden
        self.assertIn(
            "moderately priced", output
        )  # testet moderately priced gleich mit
        self.assertIn("moderately priced", output)
        self.assertIn("north", output)
        self.assertIn("123 Pasta Lane", output)
