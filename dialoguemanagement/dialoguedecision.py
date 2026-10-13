import random
from datastructures.dialoguestate import DialogueState
from datastructures.dialogueact import DialogueAct
from datastructures.defaults import get_greet_act, get_root_state
from config import REQUIRED_SLOTS


class DialogueDecider(object):

    def __init__(self):
        pass

    def get_informed_response(self, state, results, first_result):
        """
        Returns inform DialogueActs for requested slots if information is available.
        """

        inform_slot = state.slots["inform"]
        # Wenn ein result da + value in inform > sammle entsprechende values für act-Liste
        inform_acts = []  # list of collected inform slots

        # inform == phone sammle phone Info, keine Prüfung auf nicht vorhanden > phone Nummbern sind immer vorhanden
        for slot in inform_slot:
            if slot == "phone":
                if (
                    not first_result["phone"]
                    or "not available" in first_result["phone"]
                ):
                    inform_acts.append(
                        DialogueAct(
                            "inform",
                            {
                                "act_slot": "no_phone",
                                "template_value_list": results,
                                "greeting": False,
                            },
                            history=state.history,
                        )
                    )
                else:
                    inform_acts.append(
                        DialogueAct(
                            "inform",
                            {
                                "act_slot": "phone",
                                "template_value_list": results,
                                "greeting": False,
                            },
                            history=state.history,
                        )
                    )
            # wenn inform == signature > sammle signature Info, prüfe zunächst ob vorhanden oder "not available"
            elif slot == "signature":
                if (
                    not first_result["signature"]
                    or "not available" in first_result["signature"]
                ):
                    inform_acts.append(
                        DialogueAct(
                            "inform",
                            {
                                "act_slot": "no_signature",
                                "template_value_list": results,
                                "greeting": False,
                            },
                            history=state.history,
                        )
                    )
                else:
                    inform_acts.append(
                        DialogueAct(
                            "inform",
                            {
                                "act_slot": "signature",
                                "template_value_list": results,
                                "greeting": False,
                            },
                            history=state.history,
                        )
                    )
            # wenn inform == description > spiele description Info aus, prüfe zunächst ob vorhanden oder "not available"
            elif slot == "description":
                if (
                    not first_result["description"]
                    or "not available" in first_result["description"]
                ):
                    inform_acts.append(
                        DialogueAct(
                            "inform",
                            {
                                "act_slot": "no_description",
                                "template_value_list": results,
                                "greeting": False,
                            },
                            history=state.history,
                        )
                    )
                else:
                    inform_acts.append(
                        DialogueAct(
                            "inform",
                            {
                                "act_slot": "description",
                                "template_value_list": results,
                                "greeting": False,
                            },
                            history=state.history,
                        )
                    )
        if inform_acts:
            inform_acts[0].slots["greeting"] = state.slots["greeting"]
            return inform_acts
        else:
            return None

    def handle_goodbye(self, state: DialogueState):
        """
        Check if a goodbye sequence should be triggered based on the state
        """
        goodbye_stage = state.slots.get("goodbye_stage", 0)

        if goodbye_stage == 1:
            return DialogueAct(
                "confirm",
                {"act_slot": "goodbye", "template_value_list": {}},
                history=state.history,
            )

        if goodbye_stage == 2:
            return DialogueAct(
                "goodbye",
                {},
                history=[get_root_state()],
            )  # slots -> leer, Konversation endet

        return None

    def handle_restaurant_name_request(self, state: DialogueState):
        """
        Handles the case where the user specified a restaurant by name.
        If confidence is low, ask for clarification.
        If results exist, inform using available details.
        """

        positive_name_specifications = [
            x for x in state.slots["specify"]["name"] if not x["negated"]
        ]

        if not positive_name_specifications:
            return None

        top_result = positive_name_specifications[0]

        # first check if the confidence for name-result is high enough to prevent wrong result displays
        if top_result["confidence"] < 0.7 or (
            top_result["confidence"] < 0.45 and top_result["negated"]
        ):
            return DialogueAct(
                "ask",
                {"act_slot": "restaurant_clarification"},
                history=state.history,
            )

        if not state.resultList:
            return None

        first_result = state.resultList[0]

        results = {
            "food": state.found_params.get("food"),
            "pricerange": state.found_params.get("pricerange"),
            "area": state.found_params.get("area"),
            "name": first_result["name"],
            "address": first_result["addr"],
            "phone": first_result["phone"],
            "signature": first_result["signature"],
            "description": first_result["description"],
        }

        # check if user wants information (phone, description, signature) about the restaurant itself
        informed_result_response = self.get_informed_response(
            state, results, first_result
        )

        if informed_result_response:
            return informed_result_response

        return DialogueAct(
            "inform",
            {
                "act_slot": "result_by_name",
                "template_value_list": results,
                "greeting": state.slots["greeting"],
                "is_new_negated": state.new_negated_slot_values,
            },
            history=state.history,
        )

    def handle_user_questions(self, state: DialogueState):
        """
        Handles explicit user questions from the FAQ like "what kind of food?" or "what area?"
        If no positive info is found for the requested slot, return an 'ask' act.
        """

        #  User FAQ-Question Mapping
        question_to_slot_mapping = {
            "WHAT_PRICERANGE": "pricerange",
            "WHAT_AREA": "area",
            "WHAT_FOOD": "food",
        }

        user_question = state.slots["user_question"]
        if user_question not in question_to_slot_mapping.keys():
            return None

        slot = question_to_slot_mapping[user_question]
        positive_specifications = [
            x for x in state.slots["specify"][slot] if not x["negated"]
        ]

        if positive_specifications:
            return None

        # Set context
        state.previous_slot_type = question_to_slot_mapping[user_question]
        # all needed information from state for system act/generation
        is_new_dont_care = state.new_dont_care
        new_slot_selected = state.new_slot_selected
        any_new_negation_is_wildcard = state.any_new_negation_is_wildcard

        return DialogueAct(
            "ask",
            {
                "act_slot": slot,
                "template_value_list": None,
                "greeting": state.slots["greeting"],  # greet
                "any_new_negation_is_wildcard": any_new_negation_is_wildcard,  # wenn true, echte negation. Wenn false, keine negation
                "user_question": state.slots["user_question"],  # user_question
                "is_new_dont_care": is_new_dont_care,  # dont_care
                "new_slot_select": new_slot_selected,  # new_select
            },
            history=state.history,
        )

    def handle_impossible_constraints(self, state: DialogueState):
        """
        If the user has negated all available options for a slot,
        return an 'impossible' DialogueAct.
        """

        def get_n_negated_options(slot_type):
            return len(
                set(
                    [
                        x["string"]
                        for x in state.slots["specify"][slot_type]
                        if (x["negated"] and (x["string"] != "*"))
                    ]
                )
            )

        for slot_type, limit in [
            ("pricerange", 3),
            ("area", 5),
            ("name", 110),
        ]:
            if get_n_negated_options(slot_type) == limit:
                return DialogueAct(
                    "impossible",
                    {
                        "act_slot": slot_type,
                        "template_value_list": None,
                        "greeting": state.slots["greeting"],  # greet
                        "any_new_negation_is_wildcard": False,  # wenn true, echte negation. Wenn false, keine negation
                        "user_question": state.slots["user_question"],  # user_question
                        "is_new_dont_care": False,  # dont_care
                        "new_slot_select": False,  # new_select
                    },
                    history=state.history,
                )
        return None

    def actOn(self, state: DialogueState) -> DialogueAct:

        # Check for goodbye-related system actions
        goodbye_act = self.handle_goodbye(state)
        if goodbye_act:
            return goodbye_act

        # Check if user specified a restaurant by name
        named_result_act = self.handle_restaurant_name_request(state)
        if named_result_act:
            return named_result_act

        # Check for explicit user questions like WHAT_AREA, WHAT_FOOD, etc.
        user_questions = self.handle_user_questions(state)
        if user_questions:
            return user_questions

        # check if any selection is impossible
        impossible_act = self.handle_impossible_constraints(state)
        if impossible_act:
            return impossible_act

        # check if user fails to answer a required slots question repeatingly > Last effort to bring inform him about possibilities
        if (
            state.slots["n_failures"] >= 2
            and not state.slots["user_question"]
            and not state.slots["dont_like_choice"]
            and not state.resultList
        ):
            intent, act_slot = state.slots["user_prompt"].split("\\")

            if intent == "ask":
                if act_slot == "pricerange":
                    state.slots["user_question"] = "WHAT_PRICERANGE"
                if act_slot == "area":
                    state.slots["user_question"] = "WHAT_AREA"
                if act_slot == "food":
                    state.slots["user_question"] = "WHAT_FOOD"
            else:
                state.slots["user_question"] = random.choice(
                    ["WHAT_CAN_YOU_DO", "HOW_TO_USE"]
                )

        """
        Handle edge case: user asks for phone/description info but theres no result yet
        """
        if not state.resultList:
            inform_slot = state.slots["inform"]
            inform_ask_acts = []
            if any(
                slot in ("phone", "signature", "description") for slot in inform_slot
            ):
                inform_ask_acts.append(
                    DialogueAct(
                        "inform_before_result",
                        {
                            "act_slot": "no_result_to_inform",
                            "greeting": None,
                        },
                        history=state.history,
                    )
                )

            """MAIN LOGIC - ASK FOR REQUIRED SLOTS UNTIL ALL ARE FILLED TO GIVE AN INFORMED RESTAURANT RECOMMENDATION """
            for slot in REQUIRED_SLOTS:
                if not state.slots["specify"][slot]:
                    if not state.resultList and state.slots["inform"]:
                        inform_ask_acts.append(
                            DialogueAct(
                                "ask",
                                {
                                    "act_slot": slot,
                                    "template_value_list": None,
                                    "greeting": None,  # greet
                                    "any_new_negation_is_wildcard": False,  # wenn true, echte negation. Wenn false, keine negation
                                    "user_question": state.slots[
                                        "user_question"
                                    ],  # user_question
                                    "is_new_dont_care": False,  # dont_care
                                    "new_slot_select": False,  # new_select
                                },
                                history=state.history,
                            )
                        )
                        break
                    else:
                        # if any required slot is not specified or is specified negatively ask
                        state.previous_slot_type = slot
                        # all needed information from state for system act/generation
                        is_new_dont_care = state.new_dont_care
                        state.new_dont_care = False
                        new_slot_selected = state.new_slot_selected
                        state.new_slot_selected = False
                        any_new_negation_is_wildcard = (
                            state.any_new_negation_is_wildcard
                        )
                        state.any_new_negation_is_wildcard = False

                        inform_ask_acts.append(
                            DialogueAct(
                                "ask",
                                {
                                    "act_slot": slot,
                                    "template_value_list": None,
                                    "greeting": state.slots["greeting"],  # greet
                                    "any_new_negation_is_wildcard": any_new_negation_is_wildcard,  # wenn true, echte negation. Wenn false, keine negation
                                    "user_question": state.slots[
                                        "user_question"
                                    ],  # user_question
                                    "is_new_dont_care": is_new_dont_care,  # dont_care
                                    "new_slot_select": new_slot_selected,  # new_select
                                },
                                history=state.history,
                            )
                        )
                        break

            if inform_ask_acts:
                return inform_ask_acts

        """MAIN LOGIC - GIVE RESULT IF ALL REQUIRED SLOTS ARE FILLED TO GIVE A RESTAURANT RECOMMENDATION """

        if state.resultList:
            is_new_negated = state.new_negated_slot_values
            state.new_negated_slot_values = False
            # all needed information from state for system act/generation
            is_new_dont_care = state.new_dont_care
            state.new_dont_care = False
            new_slot_selected = state.new_slot_selected
            state.new_slot_selected = False
            any_new_negation_is_wildcard = state.any_new_negation_is_wildcard
            state.any_new_negation_is_wildcard = False

            first_result = state.resultList[0]
            results = {
                "food": state.found_params.get("food"),
                "pricerange": state.found_params.get("pricerange"),
                "area": state.found_params.get("area"),
                "name": first_result["name"],
                "address": first_result["addr"],
                "phone": first_result["phone"],
                "signature": first_result["signature"],
                "description": first_result["description"],
            }

            informed_result_response = self.get_informed_response(
                state, results, first_result
            )
            if informed_result_response:
                informed_result_response[0].slots["greeting"] = state.slots["greeting"]
                return informed_result_response

            act = DialogueAct(
                "inform",
                {
                    "act_slot": "result",
                    "template_value_list": results,
                    "greeting": state.slots["greeting"],  # greet
                    "is_new_negated": is_new_negated,
                    "any_new_negation_is_wildcard": any_new_negation_is_wildcard,  # wenn true, echte negation. Wenn false, keine negation
                    "user_question": state.slots["user_question"],  # user_question
                    "is_new_dont_care": is_new_dont_care,  # dont_care
                    "new_slot_select": new_slot_selected,  # new_select
                },
                history=state.history,
            )

            """ If there is not an exact result which matched user choice - clarify that it's an alternative recommendation """
            if state.slots.get("alternative_result", False) == True:
                act = DialogueAct(
                    "inform",
                    {
                        "act_slot": "alternative_result",
                        "template_value_list": results,
                        "greeting": state.slots["greeting"],  # greet
                        "is_new_negated": is_new_negated,
                        "any_new_negation_is_wildcard": any_new_negation_is_wildcard,  # wenn true, echte negation. Wenn false, keine negation
                        "user_question": state.slots["user_question"],  # user_question
                        "is_new_dont_care": is_new_dont_care,  # dont_care
                        "new_slot_select": new_slot_selected,  # new_select
                    },
                    history=state.history,
                )
            else:
                act = DialogueAct(
                    "inform",
                    {
                        "act_slot": "result",
                        "template_value_list": results,
                        "greeting": state.slots["greeting"],  # greet
                        "is_new_negated": is_new_negated,
                        "any_new_negation_is_wildcard": any_new_negation_is_wildcard,  # wenn true, echte negation. Wenn false, keine negation
                        "user_question": state.slots["user_question"],  # user_question
                        "is_new_dont_care": is_new_dont_care,  # dont_care
                        "new_slot_select": new_slot_selected,  # new_select
                    },
                    history=state.history,
                )

            """ If there aren't any matching results found - inform the user accordingly """
        else:
            is_new_negated = state.new_negated_slot_values
            state.new_negated_slot_values = False
            # all needed information from state for system act/generation
            is_new_dont_care = state.new_dont_care
            state.new_dont_care = False
            new_slot_selected = state.new_slot_selected
            state.new_slot_selected = False
            any_new_negation_is_wildcard = state.any_new_negation_is_wildcard
            state.any_new_negation_is_wildcard = False

            act = DialogueAct(
                "inform",
                {
                    "act_slot": "no_result",
                    "template_value_list": {
                        "food": (
                            (
                                "not "
                                if state.slots["specify"]["food"][0]["negated"]
                                else ""
                            )
                            + state.found_params.get("food", "")
                        ),
                        "pricerange": (
                            (
                                "not "
                                if state.slots["specify"]["pricerange"][0]["negated"]
                                else ""
                            )
                            + state.found_params.get("pricerange", "")
                        ),
                        "area": (
                            (
                                "not "
                                if state.slots["specify"]["area"][0]["negated"]
                                else ""
                            )
                            + state.found_params.get("area", "")
                        ),
                    },
                    "greeting": state.slots["greeting"],  # greet
                    "is_new_negated": is_new_negated,
                    "any_new_negation_is_wildcard": any_new_negation_is_wildcard,  # wenn true, echte negation. Wenn false, keine negation
                    "user_question": state.slots["user_question"],  # user_question
                    "is_new_dont_care": is_new_dont_care,  # dont_care
                    "new_slot_select": new_slot_selected,  # new_select
                },
                history=state.history,
            )

        if state.DEBUG:
            act.DEBUG = True
            print(f"DialogueDecider: {act}\n")
            print(f"new_negated_slot_values: {state.new_negated_slot_values}\n")

        return act
