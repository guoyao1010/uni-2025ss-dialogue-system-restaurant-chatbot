from copy import deepcopy
import unittest
from DialogueAgent import DialogueAgent
from datastructures.dialoguestate import DialogueState
from datastructures.dialogueact import DialogueAct
from languagegeneration.answer_templates import TEMPLATES
from datastructures.defaults import get_greet_act, get_root_state
from languageunderstanding.understandingunits_test import choice_in_top_n


class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.agent = DialogueAgent()

    def test_single_message(self):
        msg, state, act = self.agent._dialoguePipeline(
            "i want cheap chinese food in the south", get_root_state(), get_greet_act()
        )
        assert msg.startswith(("Got it.", "Alright!", "Okay, thanks."))
        assert any(
            phrase in msg for phrase in ("I found a ", "There's a", "You might like")
        )
        assert isinstance(state.resultList, list)
        assert state.resultList[0]["pricerange"] == "cheap"
        assert state.resultList[0]["food"] == "chinese"
        assert state.resultList[0]["area"] == "south"
        _, state, act = self.agent._dialoguePipeline("bye", state, act)
        assert state.slots["goodbye_stage"] == 1  # neue Prüfung da Goodbye-Logik anders
        _, state, act = self.agent._dialoguePipeline("yes", state, act)
        assert state.slots["goodbye"] == True  # neue Prüfung

    def test_run_happy_path(self):
        _, state, act = self.agent._dialoguePipeline(
            "I want to eat chinese food", get_root_state(), get_greet_act()
        )
        _, state, act = self.agent._dialoguePipeline(
            "I want to eat in the south", state, act
        )
        msg, state, act = self.agent._dialoguePipeline(
            "I want a cheap restaurant", state, act
        )
        assert msg.startswith(("Got it.", "Alright!", "Okay, thanks."))
        assert any(
            phrase in msg for phrase in ("I found a ", "There's a", "You might like")
        )
        assert isinstance(state.resultList, list)
        assert state.resultList[0]["pricerange"] == "cheap"
        assert state.resultList[0]["food"] == "chinese"
        assert state.resultList[0]["area"] == "south"
        _, state, act = self.agent._dialoguePipeline("bye", state, act)
        assert state.slots["goodbye_stage"] == 1
        _, state, act = self.agent._dialoguePipeline("yes", state, act)
        assert state.slots["goodbye"]

    def test_slot_correction(self):
        _, state, act = self.agent._dialoguePipeline(
            "I want to eat german food", get_root_state(), get_greet_act()
        )
        _, state, act = self.agent._dialoguePipeline(
            "I want to eat in the south", state, act
        )
        _, state, act = self.agent._dialoguePipeline(
            "I want to eat chinese food", state, act
        )
        msg, state, act = self.agent._dialoguePipeline(
            "I want a cheap restaurant", state, act
        )
        assert msg.startswith(("Got it.", "Alright!", "Okay, thanks."))
        assert any(
            phrase in msg for phrase in ("I found a ", "There's a", "You might like")
        )
        assert isinstance(state.resultList, list)
        assert state.resultList[0]["pricerange"] == "cheap"
        assert state.resultList[0]["food"] == "chinese"
        assert state.resultList[0]["area"] == "south"
        _, state, act = self.agent._dialoguePipeline("bye", state, act)
        assert state.slots["goodbye_stage"] == 1
        _, state, act = self.agent._dialoguePipeline("yes", state, act)
        assert state.slots["goodbye"]

    def test_impossible_params(self):
        _, state, act = self.agent._dialoguePipeline(
            "I want a cheap restaurant", get_root_state(), get_greet_act()
        )
        _, state, act = self.agent._dialoguePipeline(
            "I want to eat british food", state, act
        )
        msg, state, act = self.agent._dialoguePipeline(
            "I want to eat in the north", state, act
        )
        assert isinstance(state.resultList, list)
        # KOOS: restaurant list will be empty, because the slots don't match the requirements:
        if state.resultList:
            assert state.resultList[0]["pricerange"] in ("cheap", "moderate")
            assert state.resultList[0]["food"] in (
                "british",
                "english",
                "scottish",
                "australian",
            )
            assert state.resultList[0]["area"] in ("north", "east", "west", "centre")

    def test_impossible_params_then_change_foodtype(self):
        _, state, act = self.agent._dialoguePipeline(
            "I want a cheap restaurant", get_root_state(), get_greet_act()
        )
        _, state, act = self.agent._dialoguePipeline(
            "I want to eat british food", state, act
        )
        _, state, act = self.agent._dialoguePipeline(
            "I want to eat in the south", state, act
        )
        msg, state, act = self.agent._dialoguePipeline(
            "Ok, if that isnt possible then i want chinese food", state, act
        )
        assert isinstance(state.resultList, list)
        assert state.resultList[0]["pricerange"] == "cheap"
        assert state.resultList[0]["food"] == "chinese"
        assert state.resultList[0]["area"] == "south"

        assert msg.startswith(("Got it.", "Alright!", "Okay, thanks."))
        assert any(
            phrase in msg for phrase in ("I found a ", "There's a", "You might like")
        )
        _, state, act = self.agent._dialoguePipeline("bye", state, act)
        assert state.slots["goodbye_stage"] == 1
        _, state, act = self.agent._dialoguePipeline("yes", state, act)
        assert state.slots["goodbye"]

    def test_alternative_choice(self):
        _, state, act = self.agent._dialoguePipeline(
            "I want a moderately priced restaurant", get_root_state(), get_greet_act()
        )
        _, state, act = self.agent._dialoguePipeline(
            "I want to eat chinese food", state, act
        )
        msg, state, act = self.agent._dialoguePipeline(
            "I want to eat in the east", state, act
        )

        assert isinstance(state.resultList, list)
        # Roman: restaurant list will be not empty anymore, because the slots  match the requirements again (n_matching_slots and combination_confidence - fixed to arithmetic mean)
        if state.resultList:
            assert state.resultList[0]["pricerange"] in (
                "expensive",
                "cheap",
                "moderate",
            )  # moderate is adjacent to all other options
            assert state.resultList[0]["food"] in ("chinese", "japanese", "thai")
            assert state.resultList[0]["area"] in ("east", "centre", "north", "south")

    # test by Yao
    def test_greetings(self):
        msg, state, act = self.agent._dialoguePipeline(
            "hi, I want a moderately priced restaurant",
            get_root_state(),
            get_greet_act(),
        )
        assert msg.startswith("Hi")
        msg, state, act = self.agent._dialoguePipeline(
            "I want to eat chinese food", state, act
        )
        assert not msg.startswith("Hi")
        msg, state, act = self.agent._dialoguePipeline(
            "Grüß Gott, I want to eat in the east", state, act
        )
        assert msg.startswith("Grüß Gott.")

    def test_forget(self):
        msg, state, act = self.agent._dialoguePipeline(
            "i want cheap chinese food in the south", get_root_state(), get_greet_act()
        )
        assert msg.startswith(("Got it.", "Alright!", "Okay, thanks."))
        assert any(
            phrase in msg for phrase in ("I found a ", "There's a", "You might like")
        )
        assert isinstance(state.resultList, list)
        assert state.resultList[0]["pricerange"] == "cheap"
        assert state.resultList[0]["food"] == "chinese"
        assert state.resultList[0]["area"] == "south"
        _, state, act = self.agent._dialoguePipeline("bye", state, act)
        assert state.slots["goodbye_stage"] == 1
        _, state, act = self.agent._dialoguePipeline("yes", state, act)
        assert state.slots["goodbye"]

        msg, state, act = self.agent._dialoguePipeline("Hi", state, act)
        assert state.resultList == []

    def test_dont_care_about_area(self):
        _, state, act = self.agent._dialoguePipeline(
            "i want chinese food", get_root_state(), get_greet_act()
        )
        _, state, act = self.agent._dialoguePipeline("i dont care", state, act)
        _, state, act = self.agent._dialoguePipeline("cheap", state, act)
        assert state.resultList[0]["pricerange"] == "cheap"
        assert state.resultList[0]["food"] == "chinese"

    def test_german_message(self):
        _, state, act = self.agent._dialoguePipeline(
            "ich möchte cheap", get_root_state(), get_greet_act()
        )
        _, state, act = self.agent._dialoguePipeline("ich möchte north", state, act)
        _, state, act = self.agent._dialoguePipeline("ich möchte deutsch", state, act)

        assert isinstance(state.resultList, list)

    def test_no_appology_for_positive_specification_with_negation(self):
        message, state, act = self.agent._dialoguePipeline(
            "i want cheap chinese food not expensive", get_root_state(), get_greet_act()
        )
        for _, template in TEMPLATES["deny"].items():
            assert not message.startswith(template)

    def test_surprise_me(self):
        message, state, act = self.agent._dialoguePipeline(
            "surprise me", get_root_state(), get_greet_act()
        )
        assert state.resultList

    def test_surprise_me_after_goodbye(self):
        message, state, act = self.agent._dialoguePipeline(
            "surprise me", get_root_state(), get_greet_act()
        )
        assert state.resultList
        message, state, act = self.agent._dialoguePipeline("goodbye", state, act)
        message, state, act = self.agent._dialoguePipeline("yes", state, act)
        assert not state.resultList
        message, state, act = self.agent._dialoguePipeline(
            "surprise me", state, act
        )  # goodbye is re-triggered here
        assert state.resultList

    def test_surprise_me_slot_specific(self):
        message, state, act = self.agent._dialoguePipeline(
            "hi", get_root_state(), get_greet_act()
        )
        assert not state.resultList
        message, state, act = self.agent._dialoguePipeline("surprise me", state, act)
        assert not state.resultList

    def test_exclude_name_after_result(self):
        message, state, act = self.agent._dialoguePipeline(
            "I want cheap italian food in the centre", get_root_state(), get_greet_act()
        )
        assert state.resultList

        top_choice = state.resultList[0]
        message, state, act = self.agent._dialoguePipeline(
            f"i dont want to eat at {top_choice['name']} restaurant", state, act
        )
        assert state.resultList
        assert state.resultList[0] != top_choice

    def test_exclude_name_before_result(self):
        message, state, act = self.agent._dialoguePipeline(
            "i dont want to eat at Pizza hut", get_root_state(), get_greet_act()
        )

        message, state, act = self.agent._dialoguePipeline(
            "I want cheap italian food in the centre", state, act
        )
        assert "pizza hut" not in state.resultList[0]["name"]

    def test_exclude_name_with_last_specification(self):
        message, state, act = self.agent._dialoguePipeline(
            "I want cheap italian food in the centre but not pizza hut",
            get_root_state(),
            get_greet_act(),
        )
        assert "pizza hut" not in state.resultList[0]["name"]

    def test_ask_back_same_slot_after_question(self):
        message, state, act = self.agent._dialoguePipeline(
            "Hi", get_root_state(), get_greet_act()
        )
        message, state, act = self.agent._dialoguePipeline(
            "I want german food", state, act
        )
        message, state, act = self.agent._dialoguePipeline(
            "what are possible price ranges", state, act
        )
        assert any(
            TEMPLATES["user_question"][f"WHAT_PRICERANGE{i}"] in message
            for i in range(3)
        )
        assert any(TEMPLATES["ask"][f"pricerange{i}"] in message for i in range(3))

    def test_area_not_recognized_as_dont_care(self):
        message, state, act = self.agent._dialoguePipeline(
            "Hi", get_root_state(), get_greet_act()
        )
        message, state, act = self.agent._dialoguePipeline("i dont care", state, act)
        assert len(state.slots["specify"]["food"]) == 1
        message, state, act = self.agent._dialoguePipeline("north", state, act)
        assert "choose something for you" not in message
        assert "I'll pick you something." not in message

    def test_dont_retrigger_goodbye(self):
        message, state, act = self.agent._dialoguePipeline(
            "Hi", get_root_state(), get_greet_act()
        )
        message, state, act = self.agent._dialoguePipeline("goodbye", state, act)
        message, state, act = self.agent._dialoguePipeline("yes", state, act)
        message, state, act = self.agent._dialoguePipeline("surprise me", state, act)
        assert not message in TEMPLATES["goodbye"].values()

    def test_answer_new_user_questions(self):
        message, state, act = self.agent._dialoguePipeline(
            "how many restaurants do you know?", get_root_state(), get_greet_act()
        )
        assert any(
            variant in message
            for variant in [
                TEMPLATES["user_question"]["RESTAURANT_NUMBER0"],
                TEMPLATES["user_question"]["RESTAURANT_NUMBER1"],
                TEMPLATES["user_question"]["RESTAURANT_NUMBER2"],
            ]
        )

        message, state, act = self.agent._dialoguePipeline(
            "please tell me a joke", get_root_state(), get_greet_act()
        )
        assert any(
            variant in message
            for variant in [
                TEMPLATES["user_question"]["OUT_OF_SCOPE0"],
                TEMPLATES["user_question"]["OUT_OF_SCOPE1"],
                TEMPLATES["user_question"]["OUT_OF_SCOPE2"],
            ]
        )
        message, state, act = self.agent._dialoguePipeline(
            "How can i use this bot?", get_root_state(), get_greet_act()
        )
        assert any(
            variant in message
            for variant in [
                TEMPLATES["user_question"]["HOW_TO_USE0"],
                TEMPLATES["user_question"]["HOW_TO_USE1"],
                TEMPLATES["user_question"]["HOW_TO_USE2"],
            ]
        )
        message, state, act = self.agent._dialoguePipeline(
            "what can you do?", get_root_state(), get_greet_act()
        )
        assert any(
            variant in message
            for variant in [
                TEMPLATES["user_question"]["WHAT_CAN_YOU_DO0"],
                TEMPLATES["user_question"]["WHAT_CAN_YOU_DO1"],
                TEMPLATES["user_question"]["WHAT_CAN_YOU_DO2"],
            ]
        )

    def test_inform_after_result(self):
        msg, state, act = self.agent._dialoguePipeline(
            "i want cheap chinese food in the south", get_root_state(), get_greet_act()
        )

        assert isinstance(state.resultList, list)
        assert state.resultList[0]["pricerange"] == "cheap"
        assert state.resultList[0]["food"] == "chinese"
        assert state.resultList[0]["area"] == "south"
        message, state, act = self.agent._dialoguePipeline(
            "Give me the description", state, act
        )

        assert any(
            message.startswith(phrase)
            for phrase in (
                "Happy to ",
                "Sure!",
                "Here's what ",
                "I'm sorry ",
                "Unfortunately, ",
                "I couldn’t find ",
            )
        )

    def test_multiple_inform_after_result(self):
        msg, state, act = self.agent._dialoguePipeline(
            "i want cheap chinese food in the south", get_root_state(), get_greet_act()
        )
        assert isinstance(state.resultList, list)
        assert state.resultList[0]["pricerange"] == "cheap"
        assert state.resultList[0]["food"] == "chinese"
        assert state.resultList[0]["area"] == "south"

        message, state, act = self.agent._dialoguePipeline(
            "Give me the phone and description", state, act
        )

        phone_phrases = [
            "The phone number of",
            "You can reach",
            "can be contacted",
            "no phone number listed",
            "no phone number available",
            "doesn't seem to have a listed phone number",
        ]

        description_phrases = [
            "Happy to tell you more!",
            "Here's some more info:",
            "Here's what I know",
            "Unfortunately, there's no further description",
            "I couldn’t find any additional information",
            "I'm sorry to inform you",
        ]

        assert any(phrase in message for phrase in phone_phrases) and any(
            phrase in message for phrase in description_phrases
        )

    def test_inform_no_result_yet(self):

        message, state, act = self.agent._dialoguePipeline(
            "i want cheap chinese food", get_root_state(), get_greet_act()
        )

        assert hasattr(state, "resultList"), "state hat kein Attribut resultList"
        assert (
            state.resultList == [] or state.resultList is None
        ), "resultList sollte leer oder None sein"

        msg, state, act = self.agent._dialoguePipeline("i want description", state, act)

        inform_phrases = [
            "Sorry - first you",
            "Please tell me",
            "At this moment",
        ]

        ask_phrases = [
            "Which area",
            "What part of",
            "Which city area",
        ]

        assert any(phrase in msg for phrase in inform_phrases) and any(
            phrase in msg for phrase in ask_phrases
        )

    def test_selection_not_possible_price(self):
        message, state, act = self.agent._dialoguePipeline(
            "I want chinese food in any area", get_root_state(), get_greet_act()
        )
        message, state, act = self.agent._dialoguePipeline(
            "Not cheap, moderately priced or expensive", state, act
        )
        assert any(
            [message in template for template in TEMPLATES["impossible"].values()]
        )

    def test_selection_not_possible_area(self):
        message, state, act = self.agent._dialoguePipeline(
            "I want cheap, chinese food", get_root_state(), get_greet_act()
        )
        message, state, act = self.agent._dialoguePipeline(
            "not in the north, east, south, west or centre", state, act
        )
        assert any(
            [message in template for template in TEMPLATES["impossible"].values()]
        )

    def test_selection_almost_impossible_area(self):
        message, state, act = self.agent._dialoguePipeline(
            "I want cheap, chinese food", get_root_state(), get_greet_act()
        )
        message, state, act = self.agent._dialoguePipeline(
            "not in the north, east, south or west", state, act  # should be centre
        )
        assert not any(
            [message in template for template in TEMPLATES["impossible"].values()]
        )

    def test_backup_to_star_any_area(self):
        message, state, act = self.agent._dialoguePipeline(
            "Italian, north", get_root_state(), get_greet_act()
        )
        message, state, act = self.agent._dialoguePipeline("any", state, act)
        message, state, act = self.agent._dialoguePipeline("not italian", state, act)
        assert not "*" in message

    def test_backup_to_star_any_price(self):
        message, state, act = self.agent._dialoguePipeline(
            "Italian, cheap", get_root_state(), get_greet_act()
        )
        message, state, act = self.agent._dialoguePipeline("any", state, act)
        message, state, act = self.agent._dialoguePipeline("not italian", state, act)
        assert not "*" in message

    def test_backup_to_star_any_food(self):
        message, state, act = self.agent._dialoguePipeline(
            "cheap, north", get_root_state(), get_greet_act()
        )
        message, state, act = self.agent._dialoguePipeline("any", state, act)
        message, state, act = self.agent._dialoguePipeline("not italian", state, act)
        assert not "*" in message

    def test_remove_backups_after_negation(self):
        message, state, act = self.agent._dialoguePipeline(
            "Hi i want italian food", get_root_state(), get_greet_act()
        )
        message, state, act = self.agent._dialoguePipeline(
            "Hi i dont want italian food", state, act
        )
        assert all(
            [x["negated"] or x["string"] == "*" for x in state.slots["specify"]["food"]]
        )
        message, state, act = self.agent._dialoguePipeline("cheap, north", state, act)
        assert state.resultList[0]["food"] != "italian"

    def test_show_area_hint_to_user(self):
        message, state, act = self.agent._dialoguePipeline(
            "Hi", get_root_state(), get_greet_act()
        )
        for i in range(3):
            message, state, act = self.agent._dialoguePipeline(
                "I want to eat in Bamberg", state, act
            )
            assert state.slots["user_prompt"] == "ask\\food"
            assert state.slots["n_failures"] == i + 1
        assert (
            "There are over 20 possible food types. Three examples are:" in message
            or "More than 20 food types are available. For example:" in message
            or "You can choose from over 20 cuisines. Some include:" in message
        )

    def test_show_hint_to_user(self):
        message, state, act = self.agent._dialoguePipeline(
            "Italian in the cenre", get_root_state(), get_greet_act()
        )
        for i in range(3):
            message, state, act = self.agent._dialoguePipeline(
                "ein unbekannter preis", state, act
            )
            assert state.slots["n_failures"] == i + 1

        assert (
            TEMPLATES["user_question"]["WHAT_PRICERANGE0"] in message
            or TEMPLATES["user_question"]["WHAT_PRICERANGE1"] in message
            or TEMPLATES["user_question"]["WHAT_PRICERANGE2"] in message
        )

    def test_spam_empty_message(self):
        message, state, act = self.agent._dialoguePipeline(
            "Hi", get_root_state(), get_greet_act()
        )
        for i in range(10):
            message, state, act = self.agent._dialoguePipeline(
                "I want to eat in Bamberg", state, act
            )
            assert state.slots["user_prompt"] == "ask\\food"

    def test_hint_dissapears_after_selection(self):
        message, state, act = self.agent._dialoguePipeline(
            "Italian in the cenre", get_root_state(), get_greet_act()
        )
        for i in range(3):
            message, state, act = self.agent._dialoguePipeline(
                "ein unbekannter preis", state, act
            )
            assert state.slots["n_failures"] == i + 1
        message, state, act = self.agent._dialoguePipeline("cheap", state, act)
        assert (
            TEMPLATES["user_question"]["WHAT_PRICERANGE0"] not in message
            and TEMPLATES["user_question"]["WHAT_PRICERANGE1"] not in message
            and TEMPLATES["user_question"]["WHAT_PRICERANGE2"] not in message
        )

    def test_explicit_user_question_takes_prescedence_over_help(self):
        message, state, act = self.agent._dialoguePipeline(
            "Italian in the cenre", get_root_state(), get_greet_act()
        )
        for i in range(3):
            message, state, act = self.agent._dialoguePipeline(
                "ein unbekannter preis", state, act
            )
            assert state.slots["n_failures"] == i + 1
        message, state, act = self.agent._dialoguePipeline(
            "how many restaurants are there?", state, act
        )
        assert (
            TEMPLATES["user_question"]["WHAT_PRICERANGE0"] not in message
            and TEMPLATES["user_question"]["WHAT_PRICERANGE1"] not in message
            and TEMPLATES["user_question"]["WHAT_PRICERANGE2"] not in message
        )
        assert "110 restaurants" in message

    def test_negate_name(self):
        message, state, act = self.agent._dialoguePipeline(
            "I want to eat at the best restaurant in town: clowns cafe",
            get_root_state(),
            get_greet_act(),
        )
        assert choice_in_top_n(
            string="clowns cafe",
            negated=False,
            top_n=1,
            specifications=state.slots["specify"]["name"],
        )

        message, state, act = self.agent._dialoguePipeline(
            "Nevermind, i dont like this place", state, act
        )
        assert choice_in_top_n(
            string="clowns cafe",
            negated=True,
            top_n=1,
            specifications=state.slots["specify"]["name"],
        )
        assert not choice_in_top_n(
            string="clowns cafe",
            negated=False,
            top_n=float("inf"),
            specifications=state.slots["specify"]["name"],
        )
        assert not state.resultList

    def test_dont_like_choice_is_persistent(self):
        message, state, act = self.agent._dialoguePipeline(
            "I want, cheap food in the north. Chinese or Indian or Italian",
            get_root_state(),
            get_greet_act(),
        )
        found = {state.resultList[0]["name"]}
        for _ in range(100):
            message, state, act = self.agent._dialoguePipeline(
                "i dont like this place", state, act
            )
            if not state.resultList:
                break
            result = state.resultList[0]["name"]
            assert result not in found
            found.add(result)

    def test_correct_phone_number(self):
        message, state, act = self.agent._dialoguePipeline(
            "clowns cafe",
            get_root_state(),
            get_greet_act(),
        )
        assert "Clowns Cafe" in message
        message, state, act = self.agent._dialoguePipeline("phone number", state, act)
        self.assertIn("01223 355711", message)

    def test_dont_ask_back_after_slot_is_filled(self):
        message, state, act = self.agent._dialoguePipeline(
            "i want to eat German food",
            get_root_state(),
            get_greet_act(),
        )
        message, state, act = self.agent._dialoguePipeline(
            "what food types are there", state, act
        )
        assert (
            "There are over 20 possible food types." in message
            or "More than 20 food types are available." in message
            or "You can choose from over 20 cuisines." in message
        )
        if isinstance(act, list):
            act = act[0]
        assert act.slots["act_slot"] != "food"

    def test_no_help_messages_after_result(self):
        message, state, act = self.agent._dialoguePipeline(
            "italian centre expensive",
            get_root_state(),
            get_greet_act(),
        )
        for _ in range(3):
            message, state, act = self.agent._dialoguePipeline("", state, act)
        assert all([x not in message for x in TEMPLATES["user_question"].values()])

    def test_negated_params_negated_in_message(self):
        message, state, act = self.agent._dialoguePipeline(
            "I want german food, cheap, not north",
            get_root_state(),
            get_greet_act(),
        )
        assert not state.resultList
        assert "not north" in message

    def test_ask_back_restaurant_name_is_persistent(self):
        message, state, act = self.agent._dialoguePipeline(
            "Italian Hut",
            get_root_state(),
            get_greet_act(),
        )
        assert not state.resultList
        message, state, act = self.agent._dialoguePipeline(" ", state, act)
        assert not state.resultList

    def test_names_are_persistent(self):
        message, state, act = self.agent._dialoguePipeline(
            "Moin, i want Pizza Hut",
            get_root_state(),
            get_greet_act(),
        )
        assert state.resultList
        message, state, act = self.agent._dialoguePipeline(" ", state, act)
        assert state.resultList
        message, state, act = self.agent._dialoguePipeline(" ", state, act)
        assert state.resultList
        message, state, act = self.agent._dialoguePipeline(" ", state, act)

    def test_dont_care_confirmed(self):
        dont_care_confirm_messages = tuple(TEMPLATES["dont_care"].values())

        message, state, act = self.agent._dialoguePipeline(
            "Hi",
            get_root_state(),
            get_greet_act(),
        )

        message, state, act = self.agent._dialoguePipeline("i dont care", state, act)
        assert any([x in message for x in dont_care_confirm_messages])
        message, state, act = self.agent._dialoguePipeline("i dont care", state, act)
        assert any([x in message for x in dont_care_confirm_messages])
        message, state, act = self.agent._dialoguePipeline("i dont care", state, act)
        assert state.resultList

    def test_wildcards_are_persistent(self):
        message, state, act = self.agent._dialoguePipeline(
            "surprise me",
            get_root_state(),
            get_greet_act(),
        )
        first_result = deepcopy(state.resultList)
        phone = first_result[0]["phone"]

        message, new_state, act = self.agent._dialoguePipeline(
            "phone number", state, act
        )
        assert phone in message
        assert first_result == state.resultList

    def test_dont_change_restaurant_at_inform(self):
        message, state, act = self.agent._dialoguePipeline(
            "panish, centre, not expensive",
            get_root_state(),
            get_greet_act(),
        )
        name = state.resultList[0]["name"]
        message, new_state, act = self.agent._dialoguePipeline(
            "phone number", state, act
        )
        assert name.lower() in message.lower()
        message, new_state, act = self.agent._dialoguePipeline(
            "description and signatue dish", state, act
        )
        assert name.lower() in message.lower()

    def test_no_result_message_for_dont_care_is_filled(self):
        message, state, act = self.agent._dialoguePipeline(
            "Hi",
            get_root_state(),
            get_greet_act(),
        )
        for _ in range(3):
            message, state, act = self.agent._dialoguePipeline(
                "i dont care", state, act
            )
        assert state.resultList
        for i in range(110):
            message, state, act = self.agent._dialoguePipeline(
                "another one", state, act
            )
            assert state.resultList or "city" in message
            if "city" in message and not state.resultList:
                assert i >= 10
                break
