from collections import defaultdict
from copy import deepcopy
import numpy as np
from datastructures.dialogueact import format_slots, DialogueAct
from config import get_default_slots


def _join_predictions_single_list(lst: list):
    def _get_joint_confidence(confidences: list) -> float:
        """Calculates the joint confidence from a list of individual confidences.

        Args:
            confidences (list): A list of confidence values, where each value is expected to be a float between 0 and 1.

        Returns:
            float: The joint confidence calculated from the input list. Returns 0 if the list is empty,
            returns the minimum of the single confidence value if the list contains one element,
            and returns the sum of confidences minus the product of confidences, capped at 0.9999,
            if the list contains multiple elements.
        """
        if not confidences:
            return 0
        if len(confidences) == 1:
            return min(confidences[0], 1)
        else:
            return min(float(np.sum(confidences) - np.prod(confidences)), 0.9999)

    # Grouping identical predictions
    aggregated = defaultdict(list)
    for item in lst:
        key = (item["string"], item["negated"], item["backup_for"])
        aggregated[key].append(item["confidence"])

    builder = []
    for (string, negated, backup_for), confidences in aggregated.items():
        builder.append(
            {
                "string": string,
                "confidence": _get_joint_confidence(confidences),
                "negated": negated,
                "backup_for": backup_for,
            }
        )

    # sort the predictions
    return sorted(builder, key=lambda x: x["confidence"], reverse=True)


def join_identical_predictions(slots: dict) -> dict:
    """Join identical predictions in the slots dictionary by aggregating their confidence scores.

    Args:
        slots (dict): A dictionary containing intent data, specifically under the "specify" key,
                        which holds slot information with associated predictions.

    Returns:
        dict: The updated slots dictionary with aggregated predictions for each slot, sorted by confidence.
    """

    for slot, lst in slots["specify"].items():
        slots["specify"][slot] = _join_predictions_single_list(lst)

    return slots


class DialogueState:
    def __init__(self, slots: dict, history: list = None):
        self.resultList = []
        self.found_params = {}
        self.DEBUG = False
        if slots is None:
            self.slots = get_default_slots()
        else:
            self.slots = deepcopy(slots)
        self.negated_slot_values = set()  # not needed anymore
        self.previous_slot_type = None
        self.new_negated_slot_values = False
        self.any_new_negation_is_wildcard = False
        self.is_first_turn = False
        self.user_request = {}
        self.new_slot_selected = False
        self.new_dont_care = False
        self.all_combinations = []
        self.history = history

    def update(self, act: DialogueAct, behaviour: str) -> "DialogueState":
        assert behaviour in ("replace", "add")

        if behaviour == "replace":
            new_slots = self._update_slots_replace(act)
        else:
            new_slots = self._update_slots_add(act)
            new_slots = self._negate_backups_of_negations(new_slots, act)

        new_slots["user_question"] = act.slots["user_question"]
        new_slots["inform"] = act.slots["inform"]
        new_slots["answer"] = act.slots["answer"]
        new_slots["greeting"] = act.slots["greeting"]
        new_slots["goodbye"] = act.slots["goodbye"]
        new_slots["dont_like_choice"] = act.slots["dont_like_choice"]
        new_slots["user_prompt"] = act.slots["user_prompt"]
        new_slots["n_failures"] = act.slots["n_failures"]

        new_state = DialogueState(slots=new_slots, history=self.history)

        # history can be reconstructed from list, no need to waste space
        self.history = []

        new_state.resultList = deepcopy(self.resultList)
        new_state.found_params = deepcopy(self.found_params)
        new_state.DEBUG = self.DEBUG
        new_state.negated_slot_values = deepcopy(self.negated_slot_values)
        new_state.new_negated_slot_values = self.new_negated_slot_values
        new_state.new_slot_selected = self.new_slot_selected
        new_state.new_dont_care = self.new_dont_care
        new_state.previous_slot_type = self.previous_slot_type
        new_state.user_request = deepcopy(self.user_request)
        new_state.all_combinations = deepcopy(self.all_combinations)

        return new_state

    def _negate_backups_of_negations(self, new_slots: dict, act: DialogueAct):
        new_negations = {}
        for slot_type, slot_value in act.slots["specify"].items():
            new_negations[slot_type] = [x["string"] for x in slot_value if x["negated"]]

        for slot_type, slot_value in new_slots["specify"].items():
            new_slots["specify"][slot_type] = []
            for specification in slot_value:
                if specification["backup_for"] not in new_negations[slot_type]:
                    new_slots["specify"][slot_type].append(specification)
        return new_slots

    def _update_slots_replace(self, act):
        new_slots = deepcopy(self.slots)

        for slot_type, slot_value in act.slots["specify"].items():
            if slot_value:
                new_slots["specify"][slot_type] = deepcopy(slot_value)
        return new_slots

    def _update_slots_add(self, act):
        new_slots = deepcopy(self.slots)

        for slot_type, slot_value in act.slots["specify"].items():
            assert isinstance(slot_type, str)
            assert isinstance(slot_value, list)
            for new_item in slot_value:
                updated = False
                for i, saved_item in enumerate(new_slots["specify"][slot_type]):
                    if saved_item["string"] == new_item["string"]:
                        new_slots["specify"][slot_type][i]["confidence"] = new_item[
                            "confidence"
                        ]
                        new_slots["specify"][slot_type][i]["negated"] = new_item[
                            "negated"
                        ]
                        updated = True
                    elif new_item == slot_value[0]:
                        # Adjust the probabilities of specifications that were set but not updated downwards.
                        # The new specifications are assumed to be more relevant
                        # Only do this in the first iteration so its not adjusted multiple times
                        new_slots["specify"][slot_type][i]["confidence"] *= 0.8

                if not updated:
                    new_slots["specify"][slot_type].append(new_item)

        new_slots = join_identical_predictions(new_slots)
        return new_slots

    # def __repr__(self):
    # return f"DialogueState: slots -> {format_slots(self.slots)}\nfound_params -> {self.found_params}\nresultList -> {self.resultList}"

    def __repr__(self):
        return (
            "DialogueState: "
            + f"\nslots -> {format_slots(self.slots)}"
            + f"\nfound_params ->{self.found_params}"
            + f"\nresultList -> {self.resultList}"
            + f"\nnegated_slot_values -> {self.negated_slot_values}"
            + f"\nprevious_slot_type -> {self.previous_slot_type}"
        )
