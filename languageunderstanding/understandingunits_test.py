from typing import Union, List
import unittest
from datastructures.dialogueact import DialogueAct
from typing import Optional

from languageunderstanding.understandingunits import SimpleNLU, rules

from config import CONFIDENCE_DROPOUT_THRESHOLD, NLU_RETURN_TOP_N_OPTIONS


def specification_in(
    string: Union[str, None],
    confidence: Union[float, None],
    negated: Union[bool, None],
    specifications: List[dict],
):

    for specification in specifications:
        if (
            ((specification["string"] == string) or (string is None))
            and ((specification["confidence"] >= confidence) or (confidence is None))
            and ((specification["negated"] == negated) or (negated is None))
        ):
            return True

    return False


def choice_in_top_n(
    string: str,
    negated: Optional[bool],
    top_n: int,
    specifications: List[dict],
):
    n = 0
    for specification in specifications:
        if (specification["string"] == string) and (
            specification["negated"] == negated or negated is None
        ):
            return True
        n += 1
        if n == top_n:
            break
    return False


# nlu = SimpleNLU
class TestNLU(unittest.TestCase):
    def setUp(self):
        self.nlu = SimpleNLU()

    def test_not_south_or_north(self):
        dialogue_act = self.nlu.parse(
            "i dont care i want to eat in the south and not the north"
        )
        assert choice_in_top_n(
            string="south",
            negated=False,
            top_n=2,
            specifications=dialogue_act.slots["specify"]["area"],
        )
        assert choice_in_top_n(
            string="north",
            negated=True,
            top_n=5,
            specifications=dialogue_act.slots["specify"]["area"],
        )
        assert dialogue_act.slots["specify"]["name"] == []
        assert dialogue_act.slots["specify"]["pricerange"] == []
        assert dialogue_act.slots["specify"]["food"] == []
        assert dialogue_act.slots["inform"] == []
        assert dialogue_act.slots["answer"] == "*"
        assert not dialogue_act.slots["dont_like_choice"]
        assert not dialogue_act.slots["goodbye"]
        assert dialogue_act.slots["user_question"] is None

    def test_not_chinese_pr_thai_but_pizza_hut(self):
        dialogue_act = self.nlu.parse(
            "want to eat cheap food but i dont like chineses or thai food. How about italian? Is pizza hut open?"
        )
        assert choice_in_top_n(
            string="chinese",
            negated=True,
            top_n=3,
            specifications=dialogue_act.slots["specify"]["food"],
        )
        assert choice_in_top_n(
            string="thai",
            negated=True,
            top_n=3,
            specifications=dialogue_act.slots["specify"]["food"],
        )
        assert choice_in_top_n(
            string="italian",
            negated=False,
            top_n=3,
            specifications=dialogue_act.slots["specify"]["food"],
        )
        assert choice_in_top_n(
            string="cheap",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["pricerange"],
        )
        assert dialogue_act.slots["specify"]["name"][0]["string"].startswith(
            "pizza hut"
        )
        assert dialogue_act.slots["specify"]["name"][1]["string"].startswith(
            "pizza hut"
        )
        assert dialogue_act.slots["specify"]["name"][2]["string"].startswith(
            "pizza hut"
        )
        assert dialogue_act.slots["inform"] == []
        assert dialogue_act.slots["answer"] == None
        assert not dialogue_act.slots["dont_like_choice"]
        assert not dialogue_act.slots["goodbye"]
        assert dialogue_act.slots["user_question"] is None

    def test_question_about_cheap_place_in_north(self):
        dialogue_act = self.nlu.parse(
            "Is there a cheap place in the north part of town?"
        )
        assert choice_in_top_n(
            string="cheap",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["pricerange"],
        )
        assert choice_in_top_n(
            string="north",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["area"],
        )
        assert not dialogue_act.slots["dont_like_choice"]
        assert not dialogue_act.slots["goodbye"]
        assert dialogue_act.slots["user_question"] is None

    def test_italian_and_address_request(self):
        dialogue_act = self.nlu.parse("Italian, please. Can you give me the address?")
        assert choice_in_top_n(
            string="italian",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["food"],
        )
        assert "addr" in dialogue_act.slots["inform"]
        assert not dialogue_act.slots["dont_like_choice"]
        assert not dialogue_act.slots["goodbye"]
        assert dialogue_act.slots["user_question"] is None

    def test_world_food_in_east(self):
        dialogue_act = self.nlu.parse(
            "I'd like a place that serves world food in the east part of town."
        )
        assert choice_in_top_n(
            string="world",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["food"],
        )
        assert choice_in_top_n(
            string="east",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["area"],
        )
        assert not dialogue_act.slots["dont_like_choice"]
        assert not dialogue_act.slots["goodbye"]
        assert dialogue_act.slots["user_question"] is None

    def test_caribbean_and_moderate(self):
        dialogue_act = self.nlu.parse(
            "I am looking for a restaurant that serves Caribbean food and in the moderate price range."
        )
        assert choice_in_top_n(
            string="caribbean",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["food"],
        )
        assert choice_in_top_n(
            string="moderate",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["pricerange"],
        )
        assert not dialogue_act.slots["dont_like_choice"]
        assert not dialogue_act.slots["goodbye"]
        assert dialogue_act.slots["user_question"] is None

    def test_modern_european_yes(self):
        dialogue_act = self.nlu.parse(
            "Yes, how about a restaurant that serves modern european food?"
        )
        assert choice_in_top_n(
            string="modern european",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["food"],
        )
        assert dialogue_act.slots["inform"] == []
        assert not dialogue_act.slots["dont_like_choice"]
        assert not dialogue_act.slots["goodbye"]
        assert dialogue_act.slots["user_question"] is None

    def test_under_25_dollars(self):
        dialogue_act = self.nlu.parse("Yes, under $25.00 per entree.")
        assert choice_in_top_n(
            string="cheap",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["pricerange"],
        )
        assert dialogue_act.slots["answer"] == "yes"
        assert not dialogue_act.slots["dont_like_choice"]
        assert not dialogue_act.slots["goodbye"]
        assert dialogue_act.slots["user_question"] is None

    def test_inexpensive_in_east(self):
        dialogue_act = self.nlu.parse(
            "Can you please recommend an inexpensive restaurant in the East part of town?"
        )
        assert choice_in_top_n(
            string="cheap",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["pricerange"],
        )
        assert choice_in_top_n(
            string="east",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["area"],
        )
        assert dialogue_act.slots["user_question"] is None

    def test_expensive_italian_after_disappointment(self):
        dialogue_act = self.nlu.parse(
            "Bummer. Could you help me find some expensive Italian food then?"
        )
        assert choice_in_top_n(
            string="expensive",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["pricerange"],
        )
        assert choice_in_top_n(
            string="italian",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["food"],
        )
        assert dialogue_act.slots["user_question"] is None

    def test_thank_you_goodbye(self):
        dialogue_act = self.nlu.parse("Thank you goodbye.")
        assert dialogue_act.slots["inform"] == []
        assert dialogue_act.slots["answer"] is None
        assert dialogue_act.slots["goodbye"]
        assert dialogue_act.slots["user_question"] is None

    def test_how_expensive(self):
        dialogue_act = self.nlu.parse(
            "Thanks, how expensive is that restaurant and what food do they serve?"
        )
        assert dialogue_act.slots["inform"] == ["food", "pricerange"]
        assert dialogue_act.slots["answer"] is None
        assert not dialogue_act.slots["goodbye"]
        assert dialogue_act.slots["specify"] == {
            "food": [],
            "pricerange": [],
            "name": [],
            "area": [],
        }
        assert dialogue_act.slots["user_question"] is None

    # test on 05.16 by Yao
    def test_inform_addr_specify_italian(self):
        dialogue_act = self.nlu.parse("The Italien place and the address, please.")
        assert dialogue_act.slots["inform"] == ["addr"]
        # assert dialogue_act.slots["specify"] == ["italian"]
        assert choice_in_top_n(
            string="italian",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["food"],
        )
        assert dialogue_act.slots["user_question"] is None

    def test_not_german_but_chinese(self):
        dialogue_act = self.nlu.parse(
            "I don't want german food but i want to try a chinese."
        )
        assert choice_in_top_n(
            string="german",
            negated=True,
            top_n=2,
            specifications=dialogue_act.slots["specify"]["food"],
        )
        assert choice_in_top_n(
            string="chinese",
            negated=False,
            top_n=2,
            specifications=dialogue_act.slots["specify"]["food"],
        )
        assert dialogue_act.slots["user_question"] is None

    # test on 20250518 by Yao
    def test_yes_north_but_not_expensive(self):
        dialogue_act = self.nlu.parse(
            "yes i want to eat in the north but i don't want an expensive restaurant"
        )
        assert choice_in_top_n(
            string="north",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["area"],
        )
        assert choice_in_top_n(
            string="expensive",
            negated=True,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["pricerange"],
        )
        assert dialogue_act.slots["answer"] == "yes"
        assert not dialogue_act.slots["goodbye"]
        assert dialogue_act.slots["user_question"] is None

    def test_implicit_negation_north_too_far_prefer_south(self):
        dialogue_act = self.nlu.parse(
            "no, north is too far for me, i prefer to eat in the south."
        )
        assert choice_in_top_n(
            string="north",
            negated=True,
            top_n=2,
            specifications=dialogue_act.slots["specify"]["area"],
        )
        assert choice_in_top_n(
            string="south",
            negated=False,
            top_n=2,
            specifications=dialogue_act.slots["specify"]["area"],
        )
        assert dialogue_act.slots["answer"] == "no"
        assert not dialogue_act.slots["dont_like_choice"]
        assert not dialogue_act.slots["goodbye"]
        assert dialogue_act.slots["user_question"] is None

    def test_vietnamese_food_no_price_preference(self):
        dialogue_act = self.nlu.parse(
            "I am looking for a restaurant that serves Vietnamese food. I don't care about the price range."
        )
        assert choice_in_top_n(
            string="vietnamese",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["food"],
        )
        assert choice_in_top_n(
            string="*",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["pricerange"],
        )
        assert dialogue_act.slots["user_question"] is None

    def test_no_food_preference(self):
        dialogue_act = self.nlu.parse("I do not care what type of food.")
        assert dialogue_act.slots["answer"] is None
        assert choice_in_top_n(
            string="*",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["food"],
        )
        assert dialogue_act.slots["user_question"] is None

    def test_italian_and_not_romanian(self):
        dialogue_act = self.nlu.parse("I want cheap food, italian but not romanian.")

        assert choice_in_top_n(
            string="cheap",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["pricerange"],
        )
        assert choice_in_top_n(
            string="italian",
            negated=False,
            top_n=2,
            specifications=dialogue_act.slots["specify"]["food"],
        )
        assert not choice_in_top_n(
            string="italian",
            negated=True,
            top_n=10,
            specifications=dialogue_act.slots["specify"]["food"],
        )
        assert choice_in_top_n(
            string="romanian",
            negated=True,
            top_n=2,
            specifications=dialogue_act.slots["specify"]["food"],
        )
        assert not choice_in_top_n(
            string="romanian",
            negated=False,
            top_n=10,
            specifications=dialogue_act.slots["specify"]["food"],
        )
        assert dialogue_act.slots["user_question"] is None

    def test_greeting(self):
        dialogue_act = self.nlu.parse("Grüß Gott, i want food.")
        assert dialogue_act.slots["greeting"] == "Grüß Gott"
        assert dialogue_act.slots["user_question"] is None

    # test by Yao on 05.29
    def test_no_confidence_below_threshold(self):
        dialogue_act = self.nlu.parse("expensie restaurant")
        confidence_threshold = CONFIDENCE_DROPOUT_THRESHOLD["name"]

        for candidate in dialogue_act.slots["specify"]["name"]:
            self.assertGreaterEqual(
                candidate["confidence"],
                confidence_threshold,
                f"Low-confidence name prediction found: {candidate}",
            )
        assert dialogue_act.slots["user_question"] is None

    def test_ask_about_pricerange(self):
        dialogue_act = self.nlu.parse("what priceranges are there?")
        assert dialogue_act.slots["user_question"] == "WHAT_PRICERANGE"

    def test_ask_about_area(self):
        dialogue_act = self.nlu.parse("which areas are there?")
        assert dialogue_act.slots["user_question"] == "WHAT_AREA"

    def test_ask_about_food(self):
        dialogue_act = self.nlu.parse("what food types are there?")
        assert dialogue_act.slots["user_question"] == "WHAT_FOOD"

    def test_backup_options_pricerange(self):
        dialogue_act = self.nlu.parse("i want to have expensive food")
        assert NLU_RETURN_TOP_N_OPTIONS["pricerange"] >= 2
        assert dialogue_act.slots["specify"]["pricerange"][0]["string"] == "expensive"
        assert (
            dialogue_act.slots["specify"]["pricerange"][1]["string"] == "moderate"
            or dialogue_act.slots["specify"]["pricerange"][2]["string"] == "moderate"
        )

    def test_area_dont_care(self):
        dialogue_act = self.nlu.parse("I dont care what area")
        assert dialogue_act.slots["answer"] is None
        assert choice_in_top_n(
            string="*",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["area"],
        )

    def test_dont_care_area_price_and_food(self):
        dialogue_act = self.nlu.parse(
            "yes, any area, pricerange and foodtype is fine for me."
        )
        assert dialogue_act.slots["answer"] == "yes"
        assert choice_in_top_n(
            string="*",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["area"],
        )
        assert choice_in_top_n(
            string="*",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["food"],
        )
        assert choice_in_top_n(
            string="*",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["pricerange"],
        )

    def test_no_backups_for_negations(self):
        dialogue_act = self.nlu.parse("No, I dont want australian food.")
        assert choice_in_top_n(
            string="australian",
            negated=True,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["food"],
        )
        assert len(dialogue_act.slots["specify"]["food"]) == 1

    def test_no_backups_for_negations_with_other_options(self):
        dialogue_act = self.nlu.parse(
            "No, I dont want australian food, but i want german food."
        )
        assert choice_in_top_n(
            string="australian",
            negated=True,
            top_n=2,
            specifications=dialogue_act.slots["specify"]["food"],
        )
        assert choice_in_top_n(
            string="german",
            negated=False,
            top_n=2,
            specifications=dialogue_act.slots["specify"]["food"],
        )
        assert (
            len(dialogue_act.slots["specify"]["food"])
            == NLU_RETURN_TOP_N_OPTIONS["food"] + 1
        )

    def test_misspelling(self):
        dialogue_act = self.nlu.parse("I want to eat Italien in the centre")
        assert choice_in_top_n(
            string="italian",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["food"],
        )
        assert choice_in_top_n(
            string="centre",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["area"],
        )

    def test_all_foodtypes(self):
        for foodtype in rules["slotvalues"]["food"]:
            dialogue_act = self.nlu.parse(f"I want to eat {foodtype} in the centre")
            assert choice_in_top_n(
                string=foodtype,
                negated=False,
                top_n=1,
                specifications=dialogue_act.slots["specify"]["food"],
            ), f"Couldnt find {foodtype}"
            assert choice_in_top_n(
                string="centre",
                negated=False,
                top_n=1,
                specifications=dialogue_act.slots["specify"]["area"],
            )

    def test_one_word_responses(self):
        for word, slot in [
            ("cheap", "pricerange"),
            ("moderate", "pricerange"),
            ("expensive", "pricerange"),
            ("mexican", "food"),
            ("sri lankan", "food"),
            ("north", "area"),
            ("east", "area"),
            ("south", "area"),
            ("west", "area"),
            ("centre", "area"),
        ]:
            dialogue_act = self.nlu.parse(word)
            assert choice_in_top_n(
                string=word,
                negated=False,
                top_n=1,
                specifications=dialogue_act.slots["specify"][slot],
            ), f"Couldnt find {word} for slot = {slot}"

    def test_area_recognition_after_food_and_price(self):
        dialogue_act = self.nlu.parse("italian centre cheap")

        assert choice_in_top_n(
            string="italian",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["food"],
        )
        assert choice_in_top_n(
            string="cheap",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["pricerange"],
        )
        assert choice_in_top_n(
            string="centre",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["area"],
        )

        assert dialogue_act.slots["user_question"] is None
        assert not dialogue_act.slots["dont_like_choice"]
        assert not dialogue_act.slots["goodbye"]

    def test_many_negations(self):
        dialogue_act = self.nlu.parse(
            "I dont want chinese, japanese, asian orientall, cantonese, or japanese"
        )

        assert choice_in_top_n(
            string="chinese",
            negated=True,
            top_n=4,
            specifications=dialogue_act.slots["specify"]["food"],
        )
        assert choice_in_top_n(
            string="japanese",
            negated=True,
            top_n=4,
            specifications=dialogue_act.slots["specify"]["food"],
        )
        assert choice_in_top_n(
            string="asian oriental",
            negated=True,
            top_n=4,
            specifications=dialogue_act.slots["specify"]["food"],
        )
        assert choice_in_top_n(
            string="cantonese",
            negated=True,
            top_n=4,
            specifications=dialogue_act.slots["specify"]["food"],
        )

    def test_phone_detection(self):
        dialogue_act = self.nlu.parse("Can I have the phone number?")

        self.assertIn("phone", dialogue_act.slots["inform"])

    def test_address_detection(self):
        dialogue_act = self.nlu.parse("I need the address of the place")
        self.assertIn("addr", dialogue_act.slots["inform"])

    def test_postcode_detection(self):
        dialogue_act = self.nlu.parse("What's the postcode?")
        self.assertIn("postcode", dialogue_act.slots["inform"])

    def test_food_detection(self):
        dialogue_act = self.nlu.parse("What type of food do they serve?")
        self.assertIn("food", dialogue_act.slots["inform"])

    def test_area_detection(self):
        dialogue_act = self.nlu.parse("Whicharea is it located in?")
        self.assertIn("area", dialogue_act.slots["inform"])

    def test_pricerange_detection(self):
        dialogue_act = self.nlu.parse("How expensive is it?")
        self.assertIn("pricerange", dialogue_act.slots["inform"])
        self.assertEqual(dialogue_act.slots["specify"]["pricerange"], [])

    def test_signature_detection(self):
        dialogue_act = self.nlu.parse("What is their signature dish?")
        self.assertIn("signature", dialogue_act.slots["inform"])

    def test_name_detection(self):
        dialogue_act = self.nlu.parse("What is the name?")
        self.assertIn("name", dialogue_act.slots["inform"])

    def test_description_detection(self):
        dialogue_act = self.nlu.parse("Can you describe the place?")
        self.assertIn("description", dialogue_act.slots["inform"])

    def test_multiple_slots_detection(self):
        dialogue_act = self.nlu.parse(
            "What is the name, what type of food do they serve, and whicharea is it located in?"
        )
        self.assertIn("name", dialogue_act.slots["inform"])
        self.assertIn("food", dialogue_act.slots["inform"])
        self.assertIn("area", dialogue_act.slots["inform"])
        self.assertEqual(dialogue_act.slots["specify"]["pricerange"], [])
        self.assertEqual(dialogue_act.slots["specify"]["food"], [])
        self.assertEqual(dialogue_act.slots["specify"]["area"], [])
        self.assertEqual(dialogue_act.slots["specify"]["name"], [])

    def test_multiple_with_price_signature(self):
        dialogue_act = self.nlu.parse(
            "How expensive is it and what is their signature dish?"
        )
        self.assertIn("pricerange", dialogue_act.slots["inform"])
        self.assertIn("signature", dialogue_act.slots["inform"])
        self.assertEqual(dialogue_act.slots["specify"]["pricerange"], [])

    def test_opposite_negated_area(self):
        dialogue_act = self.nlu.parse("i want to eat in the north")
        assert choice_in_top_n(
            string="north",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["area"],
        )

        assert choice_in_top_n(
            string="south",
            negated=True,
            top_n=5,
            specifications=dialogue_act.slots["specify"]["area"],
        )

    def test_opposite_negated_price(self):
        dialogue_act = self.nlu.parse("a cheap restaurant")
        assert choice_in_top_n(
            string="cheap",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["pricerange"],
        )
        assert choice_in_top_n(
            string="expensive",
            negated=True,
            top_n=3,
            specifications=dialogue_act.slots["specify"]["pricerange"],
        )
        assert not choice_in_top_n(
            string="expensive",
            negated=False,
            top_n=3,
            specifications=dialogue_act.slots["specify"]["pricerange"],
        )

    def test_negated_not_negated(self):
        dialogue_act = self.nlu.parse("i dont want to eat in the north")
        assert choice_in_top_n(
            string="north",
            negated=True,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["area"],
        )

        assert not choice_in_top_n(
            string="south",
            negated=True,
            top_n=5,
            specifications=dialogue_act.slots["specify"]["area"],
        )

    def test_not_centre(self):
        dialogue_act = self.nlu.parse("i don´t want centre")
        assert choice_in_top_n(
            string="centre",
            negated=True,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["area"],
        )

    def test_surprise_me(self):
        dialogue_act = self.nlu.parse("surprise me")
        assert dialogue_act.slots["answer"] == "*"
        assert dialogue_act.slots["surprise_me"]

    def test_cheap_not_expensive(self):
        dialogue_act = self.nlu.parse("I want chinese cheap not expensive")
        assert choice_in_top_n(
            string="chinese",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["food"],
        )
        assert choice_in_top_n(
            string="cheap",
            negated=False,
            top_n=2,
            specifications=dialogue_act.slots["specify"]["pricerange"],
        )
        assert choice_in_top_n(
            string="expensive",
            negated=True,
            top_n=2,
            specifications=dialogue_act.slots["specify"]["pricerange"],
        )

    def test_all_areas_negated(self):
        dialogue_act = self.nlu.parse("Not cheap, moderately priced or expensive")

        assert choice_in_top_n(
            string="cheap",
            negated=True,
            top_n=3,
            specifications=dialogue_act.slots["specify"]["pricerange"],
        )
        assert choice_in_top_n(
            string="moderate",
            negated=True,
            top_n=3,
            specifications=dialogue_act.slots["specify"]["pricerange"],
        )
        assert choice_in_top_n(
            string="expensive",
            negated=True,
            top_n=3,
            specifications=dialogue_act.slots["specify"]["pricerange"],
        )

    def test_boost_confidence_restaurant_names(self):
        dialogue_act = self.nlu.parse("restaurant two two")
        assert dialogue_act.slots["specify"]["name"][0]["confidence"] >= 0.8

        dialogue_act = self.nlu.parse("the niralla")
        assert dialogue_act.slots["specify"]["name"][0]["confidence"] >= 0.8

    def test_dont_like_choice(self):
        dialogue_act = self.nlu.parse("I dont like this restaurant")
        assert dialogue_act.slots["dont_like_choice"]

    def test_inform(self):
        dialogue_act = self.nlu.parse("Tell me more about this restaurant")
        assert dialogue_act.slots["inform"] == ["description"]

    def test_parse_error(self):
        dialogue_act = self.nlu.parse("south,chinese, expensive")
        assert choice_in_top_n(
            string="expensive",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["pricerange"],
        )

        assert choice_in_top_n(
            string="chinese",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["food"],
        )

        assert choice_in_top_n(
            string="south",
            negated=False,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["area"],
        )

    def test_no_indian_food(self):
        dialogue_act = self.nlu.parse("no indian food")
        assert choice_in_top_n(
            string="indian",
            negated=True,
            top_n=1,
            specifications=dialogue_act.slots["specify"]["food"],
        )

    def test_find_question_by_substring(self):
        dialogue_act = self.nlu.parse(
            "Servus, can you share the phone number and adress of the place please? Can you send me the link of the restaurant?",
        )
        assert dialogue_act.slots["user_question"] == "OUT_OF_SCOPE"

    def test_no_weird_results_from_signature(self):
        dialogue_act = self.nlu.parse(
            "description and signatue dish",
        )
        assert not dialogue_act.slots["specify"]["food"]
        assert not dialogue_act.slots["specify"]["name"]
        assert not dialogue_act.slots["specify"]["pricerange"]
        assert not dialogue_act.slots["specify"]["area"]
        assert not dialogue_act.slots["inform"] == ["description", "signature"]

    def test_no_weird_results_from_moin(self):
        dialogue_act = self.nlu.parse(
            "moin",
        )
        assert not dialogue_act.slots["specify"]["food"]
        assert not dialogue_act.slots["specify"]["name"]
        assert not dialogue_act.slots["specify"]["pricerange"]
        assert not dialogue_act.slots["specify"]["area"]
        assert dialogue_act.slots["greeting"] == "Moin"
