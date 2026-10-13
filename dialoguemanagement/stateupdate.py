from copy import deepcopy
from datastructures.dialoguestate import DialogueState
from datastructures.dialogueact import DialogueAct
from datastructures.defaults import get_root_state, get_greet_act
from database.database import Database
from config import get_default_slots, REQUIRED_SLOTS, ALL_SLOTS
from typing import Union
from datastructures.dialogueact import format_slots
import random
from collections import Counter
from collections import Counter


class SimpleStateUpdater:
    # database = None
    def __init__(self):
        self.database = Database()
        self.threshold = 0.5

    def print_debug(self, state: DialogueState, act: DialogueAct):
        if act.DEBUG:
            state.DEBUG = True
            print(f"SimpleStateUpdater: {state}\n")
            print(f"negated_slot_values: {state.negated_slot_values}\n")
            print(f"previous_slot_type: {state.previous_slot_type}\n")
            print(f"answer: {state.slots['answer']}\n")
            print(f"new_slot_selected: {state.new_slot_selected}\n")
            print(f"new_dont_care: {state.new_dont_care}\n")
            print(f"results:{state.all_combinations}\n")
            # print(f"combinations: {state.all_combinations}\n")

    def __get_all_specify_slots_without_confidence(self, slots: dict):
        return deepcopy(
            [
                (x["string"], x["negated"], x["backup_for"])
                for x in slots["specify"]["food"]
                + slots["specify"]["pricerange"]
                + slots["specify"]["area"]
                + slots["specify"]["name"]
            ]
        )

    def update(
        self, state: DialogueState, act: DialogueAct
    ) -> (
        DialogueState
    ):  # function should be called state_controller because it handles serveral cases instead of just updating the state
        """Update the dialogue state and handle special cases based on the provided dialogue act and previous state information"

        This method updates the current dialogue state by processing the given dialogue act.
        If the state is None, it initializes a new state with default slots. It asserts that
        the intent of the dialogue act is to find a restaurant and updates the state with
        the specified slots. If all required slots are filled, it populates the result list
        with the top restaurant based on the specified criteria. Furthermore, it calls multiple
        methods to handle special cases such as negated slots, wildcard values, surprise me requests,
        goodbye handling, alternative results, restaurant name handling, reset state, and more.

        Args:
            state (DialogueState): The current state of the dialogue. If None, a new state
                will be created with default slots.
            act (DialogueAct): The dialogue act containing the intent and slots to be processed.

        Returns:
            DialogueState: The updated dialogue state after processing the act and special
            handling and tracking cases.
        """

        assert isinstance(state, DialogueState)
        assert isinstance(act, DialogueAct)

        self.handle_surprise_me(state, act)

        # see if goodbye intent is present > start conformation process
        goodbye_result = self.handle_goodbye(state, act)
        if goodbye_result is not None:
            return goodbye_result

        # update state and keep track of old slots
        old_state_slots = deepcopy(
            state.slots["specify"]["food"]
            + state.slots["specify"]["pricerange"]
            + state.slots["specify"]["area"]
        )
        all_old_slots = self.__get_all_specify_slots_without_confidence(state.slots)

        # update the state with the new act
        state = state.update(act, behaviour="add")

        # only look for new restaurants if some changes were made
        changes_in_specification = (
            self.__get_all_specify_slots_without_confidence(state.slots)
            != all_old_slots
        )

        # FIRST: See if name or new name is present > handle name preferential for search if it isn't negated
        name_change = self.handle_name(state, act, changes_in_specification)
        if name_change:
            state.history.append(deepcopy(state))
            self.print_debug(state, act)
            return state

        self.track_negated_slots_and_wildcard_values(state)
        self.track_new_selected_slot_and_new_dont_care(state, act, old_state_slots)

        ###IF ALL REQUIRED SLOTS ARE FILLED, SEARCH FOR RESTAURANTS###
        if (
            all(
                [
                    bool(state.slots["specify"][slot_type])
                    for slot_type in REQUIRED_SLOTS
                ]
            )
            and changes_in_specification
        ):
            # Slots aus state für Datenbankabfrage:
            slots = {
                slot_type: state.slots["specify"][slot_type]
                for slot_type in REQUIRED_SLOTS
            }

            # Search for matching restaurants in the database
            state.resultList, state.found_params, confidence = self.find_top_restaurant(
                slots, state
            )

            self.check_if_alternative_result_was_chosen(
                state, act
            )  # much easier and shorter approach would be with the function count_matching_slots

        state.is_first_turn = False

        state.history.append(deepcopy(state))
        self.print_debug(state, act)
        return state

    def handle_surprise_me(self, state: DialogueState, act: DialogueAct):
        """Check if the user wants to be surprised and set the slots accordingly."""
        # if the user wants to be surprised, set the slots to wildcard values so that later the database can return a random restaurant
        if state.is_first_turn and act.slots["surprise_me"]:
            act.slots["specify"] = {
                "food": [
                    {
                        "string": "*",
                        "confidence": 0.9999,
                        "negated": False,
                        "backup_for": None,
                    }
                ],
                "pricerange": [
                    {
                        "string": "*",
                        "confidence": 0.9999,
                        "negated": False,
                        "backup_for": None,
                    }
                ],
                "name": [],
                "area": [
                    {
                        "string": "*",
                        "confidence": 0.999,
                        "negated": False,
                        "backup_for": None,
                    }
                ],
            }

    def handle_goodbye(
        self, state: DialogueState, act: DialogueAct
    ) -> Union[DialogueState, None]:
        """Handle goodbye logic including confirmation and state reset.
        After user says goodbye the confirmation logic is inacted
        user has to say yes or no to end this state"""

        # stage 2: goodbye confirmed, reset state
        if state.slots["goodbye_stage"] == 2:
            state.slots["confirm_goodbye"] = False
            state.slots["goodbye_stage"] = 0
            state.slots["goodbye"] = False
            state.slots["intent"] = None

        # stage 1: goodbye recognized, but not confirmed yet
        if act.slots.get("goodbye") is True:
            state.slots["goodbye_stage"] = 1
            state.slots["confirm_goodbye"] = False
            state.history.append(deepcopy(state))
            return state

        # get answer from the act
        answer = act.slots.get("answer")
        # use answer to check if goodbye is confirmed
        if answer is not None:
            answer_lower = answer.lower()

            if state.slots.get("goodbye_stage") == 1:
                if answer_lower == "yes":
                    state = get_root_state()
                    state.slots["confirm_goodbye"] = True
                    state.slots["goodbye"] = True
                    state.is_first_turn = True
                    state.slots["intent"] = "bye"
                    state.slots["goodbye_stage"] = 2

                    return state

                else:
                    # Bestätigung abgelehnt -> Goodbye zurücksetzen
                    state.slots["confirm_goodbye"] = False
                    state.slots["goodbye_stage"] = 0
                    state.slots["goodbye"] = False
                    return state

            return None  # weitermachen wie normal

    def handle_name(
        self, state: DialogueState, act: DialogueAct, changes_in_specification: bool
    ):
        """
        If a valid restaurant name is present, this method searches the database
        using only the name and updates the result list. Name overrides all other slots.
        Returns the updated state if name was handled.
        Resets name value after user asks for required slots after previous name search.
        """
        new_names = act.slots.get("specify", {}).get("name", [])
        new_inform = act.slots.get("inform", {})

        # user specified a slot (if no name was specified, and the user doesnt ask for information) -> reset if name saved
        if (
            not new_names
            and not new_inform
            and state.slots["specify"]["name"]
            and (
                act.slots["specify"]["pricerange"]
                or act.slots["specify"]["area"]
                or act.slots["specify"]["food"]
            )
        ):
            state.slots["specify"]["name"] = []
            state.resultList = []
            state.found_params = {}

        # handling the case where the user specifies a name
        if new_names:
            # for case: user specifies a name, negates it, without this the resultList would still contain the previous name search results
            state.resultList = []
            state.found_params = {}
            # only the new names are safed so that NO new search is done with the previous mentioned names
            state.slots["specify"]["name"] = new_names

        if state.slots["specify"]["name"]:
            for slot_value in state.slots["specify"]["name"]:
                if (
                    slot_value["negated"] == False
                    and slot_value["string"] in state.negated_slot_values
                ):
                    state.negated_slot_values.remove(slot_value["string"])
                if slot_value["negated"]:
                    state.negated_slot_values.add(slot_value["string"])
                    continue
                slots = {
                    "name": [slot_value],
                    "area": state.slots["specify"]["area"],
                    "pricerange": state.slots["specify"]["pricerange"],
                    "food": state.slots["specify"]["food"],
                }

                if (
                    slot_value["confidence"] >= 0.7
                    or (slot_value["confidence"] >= 0.45 and slot_value["negated"])
                ) and changes_in_specification:
                    # dont show results unless we are sure that the
                    # user wants this restauran, but still return so
                    # we can ask the user if he could clarify the name
                    state.resultList, state.found_params, confidence = (
                        self.find_top_restaurant(slots, state)
                    )
                if state.resultList:
                    state.history.append(deepcopy(state))
                    return True
                else:
                    return False

        return False

    def track_negated_slots_and_wildcard_values(self, state: DialogueState):
        """Handle negated slots and wildcard values in the dialogue state"""
        for slot_type in REQUIRED_SLOTS:
            # slot_types = state.slots["specify"][slot]

            # add negated slots to the negated_slot_values set
            for slot_value in state.slots["specify"][slot_type]:
                if slot_value["negated"]:
                    if slot_value["string"] not in state.negated_slot_values:
                        state.negated_slot_values.add(slot_value["string"])
                        state.new_negated_slot_values = True
                        if all(
                            [
                                x["negated"] or x["string"] == "*"
                                for x in state.slots["specify"][slot_type]
                            ]
                        ):
                            state.any_new_negation_is_wildcard = True
                elif (
                    not slot_value["negated"]
                    and slot_value["string"] in state.negated_slot_values
                ):
                    state.negated_slot_values.remove(slot_value["string"])

    def track_new_selected_slot_and_new_dont_care(
        self, state: DialogueState, act: DialogueAct, old_state_slots: list
    ):
        # keep track of the new slots after the update and negations
        new_state_slots = (
            state.slots["specify"]["food"]
            + state.slots["specify"]["pricerange"]
            + state.slots["specify"]["area"]
        )

        # check if the user selected a new slot
        if old_state_slots != new_state_slots:
            state.new_slot_selected = True

        # check if the user expressed a "don't care"
        check_dont_care = self.check_wildcard_increase(old_state_slots, new_state_slots)
        # if new dont care was expressed, set the new_dont_care flag
        if check_dont_care:
            state.new_dont_care = True

    def check_if_alternative_result_was_chosen(
        self, state: DialogueState, act: DialogueAct
    ):
        """Check if the user wants an alternative result."""
        # much easier and shorter approach with count_matching_slots would be better

        # copy the current state to check against found_params later
        state.user_request = {
            slot_type: [dict(x) for x in state.slots["specify"][slot_type]]
            for slot_type in REQUIRED_SLOTS
        }

        state.slots["alternative_result"] = (
            False  # default value for alternative result
        )

        # check if the found params are different from the user request
        for slot_type in REQUIRED_SLOTS:
            wanted = state.user_request[slot_type]
            if not wanted:
                continue

            # check if the user does not care about the slot
            if any([x["string"] == "*" and not x["negated"] for x in wanted]):
                continue

            # filter the wanted slots to only include non-negated and non-"*" values
            wanted = [x for x in wanted if not x["negated"] and x["string"] != "*"]

            # second check if wanted is empty after filtering negated values und "*"
            if not wanted:
                continue

            top_choice = sorted(wanted, key=lambda x: x["confidence"], reverse=True)[0][
                "string"
            ]

            found = state.found_params.get(slot_type, None)

            if found and found != top_choice:
                state.slots["alternative_result"] = True
                break

        # if the user doesn't like the choice, we set the dont_like_choice to False
        state.slots["dont_like_choice"] = False

    def check_wildcard_increase(self, old_slots, new_slots) -> bool:
        """Count the number of wildcard increases in the slot values."""
        old = Counter(
            slot["string"]
            for slot in old_slots
            if not isinstance(slot["backup_for"], str)
        )
        new = Counter(
            slot["string"]
            for slot in new_slots
            if not isinstance(slot["backup_for"], str)
        )
        if old["*"] < new["*"]:
            return True
        return False

    ##### HERE IS THE MAIN LOGIC FOR FINDING THE TOP RESTAURANT BASED ON SLOTS AND NAME #####

    def state_contains_none_negated_values(self, slot_type) -> bool:
        """Check if there are non-negated values in the slot values."""
        none_negated_values = False
        for slot_value in slot_type:
            if not slot_value["negated"]:
                none_negated_values = True
        return none_negated_values

    def get_slot_options(self, slot_type, slots, state) -> list:
        # options if the slot is negated/wildcard for a list or "normal" slot
        options = []
        for slot_value in slots[slot_type]:
            if slot_value[
                "string"
            ] == "*" or not self.state_contains_none_negated_values(slots[slot_type]):
                values = list(
                    self.database.get_all_attribute_values(slot_type)
                    - state.negated_slot_values
                )
                random.shuffle(values)
                for value in values:
                    options.append(
                        {
                            "string": value,
                            "negated": False,
                            "confidence": slot_value["confidence"],
                            "backup_for": "*",
                        }
                    )
            elif slot_value["negated"]:
                continue
            else:
                options.append(slot_value)
        return options

    def find_all_slot_combinations(self, slots, state, database):
        """Find all combination of slot values for each combination and sort them by confidence."""

        area_options = self.get_slot_options("area", slots, state)
        pricerange_options = self.get_slot_options("pricerange", slots, state)
        food_options = self.get_slot_options("food", slots, state)

        all_combinations = []
        for area in area_options:
            for pricerange in pricerange_options:
                for food in food_options:
                    result, found_params = database.find_restaurants_multiple_option(
                        {
                            "area": [area["string"]],
                            "pricerange": [pricerange["string"]],
                            "food": [food["string"]],
                        },
                        state.negated_slot_values,
                    )
                    if (
                        result
                        and result[0]["name"].lower() not in state.negated_slot_values
                    ):
                        n_matching_slots = self.count_matching_slots(
                            {
                                "area": [area],
                                "pricerange": [pricerange],
                                "food": [food],
                            },
                            state,
                        )

                        all_combinations.append(
                            (
                                # the result from the database query
                                result,
                                # the found parameters to update the dialogue state
                                {
                                    "area": found_params["area"],
                                    "pricerange": found_params["pricerange"],
                                    "food": found_params["food"],
                                },
                                # the confidence of the combination
                                (
                                    area["confidence"]
                                    + pricerange["confidence"]
                                    + food["confidence"]
                                )
                                / 3,
                                # the number of matching slots
                                n_matching_slots,
                            )
                        )
        if all_combinations:
            # Sorting combinations by confidence (x[2]) in descending order
            all_combinations.sort(key=lambda x: x[2], reverse=True)
            return all_combinations
        else:
            return []

    def count_matching_slots(self, slots: dict, state: DialogueState) -> int:
        """Find what slots match between the used slots and the told slots (state)."""
        matching_slots = 0
        for slot_type in REQUIRED_SLOTS:
            for slot_value in slots[slot_type]:
                if slot_value["backup_for"] == "*":
                    matching_slots += 1
                    continue
                if slot_value["negated"]:
                    continue
                if any(
                    slot_value["string"] == state_slot_value["string"]
                    for state_slot_value in state.slots["specify"][slot_type]
                ):
                    matching_slots += 1
        return matching_slots

    def find_top_restaurant(
        self, slots: dict, state: DialogueState
    ) -> Union[list, dict, float]:
        """Find the top restaurant based on name or slot combinations with highest confidence."""

        if slots.get("name"):
            for name in slots["name"]:
                if name["negated"]:
                    continue
                name_options = [name["string"]]
                result, found_params = self.database.find_restaurant_by_name(
                    name_options
                )
                if result:
                    return (
                        result,
                        {
                            "name": found_params.get("name", ""),
                            "area": found_params.get("area", ""),
                            "pricerange": found_params.get("pricerange", ""),
                            "food": found_params.get("food", ""),
                            "signature": found_params.get("signature", ""),
                            "phone": found_params.get("phone", ""),
                            "description": found_params.get("description", ""),
                        },
                        name["confidence"],
                    )

                return (
                    [],
                    {key: slots[key][0]["string"] for key in ("name")},
                    0,
                )

        # get all slot combinations with confidence
        state.all_combinations = self.find_all_slot_combinations(
            slots, state, self.database
        )
        # get the top combination by confidence
        if state.all_combinations:
            top_combination = state.all_combinations[0]
            result, found_params, combination_confidence, n_matching_slots = (
                top_combination
            )

            # check if the number of matching slots is greater than 2 and the confidence is above the threshold for a valid result of the best matching restaurant
            if n_matching_slots >= 2 and combination_confidence >= self.threshold:
                return (
                    result,
                    {
                        "area": found_params["area"],
                        "pricerange": found_params["pricerange"],
                        "food": found_params["food"],
                    },
                    combination_confidence,
                )
        return (
            [],
            {key: slots[key][0]["string"] for key in ("area", "pricerange", "food")},
            0,
        )
