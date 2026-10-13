import re
from datastructures.dialogueact import DialogueAct
from languagegeneration.answer_templates import TEMPLATES
from .utils import get_random_food_examples
from .utils import randomize_by_index
from .utils import get_randomized_template
from .utils import _normalize_whitespace


class SimpleGenerator(object):

    def __init__(self):
        pass

    # Generator - takes in a DialogueAct (in special cases a list of DialogueActs) and returns a string.
    def generate(self, systemaction) -> str:
        # handels the case that a list of DialogueActs is handed over. 
        # Is for example needed, when phone, description, signature are all asked at once.
        if isinstance(systemaction, list):
            return " ".join([self.generate(act) for act in systemaction])
       
        # here act_type and act_slot are retieved from the DialogueAct
        act_type = systemaction.intent
        act_slot = systemaction.slots.get("act_slot")

        if act_type not in TEMPLATES:
            return "error, intent unknown"

        ACT_TYPE_NEEDS_VALUES = {
            "inform",
        }  # these act types need values inserted

        # act_types that are randomized by the randomize_by_index logic
        RANDOMIZED_BY_INDEX = [
            "ask",
            "inform",
            "user_questions",
            "inform_before_result",
        ]

        # All act_types that do not need values inserted
        if act_type not in ACT_TYPE_NEEDS_VALUES:
            # added to handle greeting at start of the onversation
            if act_slot is None:
                greet_at_start = get_randomized_template(act_type)
                if greet_at_start:
                    return greet_at_start
                else:
                    return TEMPLATES["fallback"][""]

            # all act_types that dont need values and are not the greeting
            else:

                # act_types that need no values inserted and are randomized_by_index
                if act_type in RANDOMIZED_BY_INDEX:
                    slot_key = randomize_by_index(act_slot)
                    template = TEMPLATES[act_type].get(slot_key)
                    if template:
                        sentence = template
                    else:
                        sentence = TEMPLATES["fallback"][""]
                # act_types that need no values inserted and are randomized by get_randomized_template
                else:
                    template = get_randomized_template(act_type)
                    if template:
                        sentence = template
                    else:
                        sentence = TEMPLATES["fallback"][""]
                        
        # act_types that need values inserted ("inform")
        else:
            template_value_list = systemaction.slots.get("template_value_list", {})
            for key, val in template_value_list.items():
                if key == "area" and val == "*":
                    template_value_list[key] = "city"
                elif val == "*":
                    template_value_list[key] = ""
            # Special grammar case: "moderate" is rephrased to "moderately priced" for the answer sentence
            if "pricerange" in template_value_list:
                if template_value_list["pricerange"] == "moderate":
                    template_value_list["pricerange"] = "moderately priced"

            # "inform" answer is randomized_by_index
            slot_key = randomize_by_index(act_slot)
            template = TEMPLATES[act_type].get(slot_key)

            if template:
                sentence = template.format(
                    **template_value_list
                )  # values from template_value_list are inserted to the template here

                # removes unnecessary whitespaces
                sentence = _normalize_whitespace(sentence)

            else:
                sentence = TEMPLATES["fallback"][""]

        # Extensions of the normal conversation flow that are added to the answer generated above
        greeting = systemaction.slots.get("greeting")  # greeting?
        question_type = systemaction.slots.get(
            "user_question"
        )  # user_question_type for example: "What_AREA", "None"
        exclusion = systemaction.slots.get(
            "any_new_negation_is_wildcard"
        )  # any negation to react on? yes or no.
        dont_care = systemaction.slots.get(
            "is_new_dont_care"
        )  # any dont_care in last user input?
        slot_select = systemaction.slots.get(
            "new_slot_select"
        )  # any slot newly filled with last user input?

        # Choosing the right answer from the template. This only happens if the type is not "None".
        if question_type:

            # user_question template answer picked randomized_by_index, e.g."WHAT_FOOD2"
            question_type_key = randomize_by_index(question_type)
            answer = TEMPLATES["user_question"][
                question_type_key
            ]  # key error wieder möglich, ohne .get()

            # three random food type examples are given to the user
            if question_type == "WHAT_FOOD":
                examples = get_random_food_examples()
                if answer and len(examples) == 3:
                    answer = answer.format(examples[0], examples[1], examples[2])

            sentence = f"{answer} {sentence}"

        # if user does not care about a slot value, the bot confirms and states it will just pick any option
        if dont_care:
            dont_care_confirm = get_randomized_template("dont_care")
            if dont_care_confirm:
                sentence = f"{dont_care_confirm} {sentence}"
            else:
                return TEMPLATES["fallback"][""]

        # if a slot valus (or many) is explicitly excluded by the user, the bot confirms
        # and informs that it will choose something else than the excluded value(s)
        elif exclusion:
            exclusion_confirm = get_randomized_template("deny")
            if exclusion_confirm:
                sentence = f"{exclusion_confirm} {sentence}"
            else:
                return TEMPLATES["fallback"][""]

        # if the user made a new selection through last input, the system briefly confirms
        elif slot_select:
            select_confirm = get_randomized_template("confirm_select")
            if select_confirm:
                sentence = f"{select_confirm} {sentence}"
            else:
                return TEMPLATES["fallback"][""]

        # if user greets randomly in conversation, system greets back
        if greeting:
            sentence = f"{greeting}. {sentence}"

        return sentence
