import copy
from config import get_default_slots


def format_slots(slots):
    builder = dict(copy.deepcopy(slots))
    if "specify" in slots:
        for slot in slots["specify"]:
            builder["specify"][slot] = ", ".join(
                [
                    f"{'not ' if x['negated'] else ''}{x['string']} ({round(x['confidence'], 6)})"
                    for x in slots["specify"][slot]
                ]
            )
    return builder


class DialogueAct(object):
    def __init__(self, intent: str, slots: dict = None, history: list = None):
        assert isinstance(intent, str)
        self.intent = intent
        if not slots:
            self.slots = get_default_slots()
        else:
            assert isinstance(slots, dict)
            self.slots = slots
        self.DEBUG = False
        self.history = history

    def __repr__(self):
        return f"DialogueAct: {self.intent} -> {format_slots(self.slots)}"
