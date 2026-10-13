import copy
import re
import json
import difflib
from typing import List, Union
import numpy as np
from scipy.spatial.distance import cosine
from datastructures.dialogueact import DialogueAct
from datastructures.dialoguestate import DialogueState, join_identical_predictions
from datastructures.defaults import get_greet_act
from dialoguemanagement.dialoguedecision import DialogueDecider
from dialoguemanagement.stateupdate import SimpleStateUpdater
from models import ner_pipeline, embedding_model
from config import (
    get_default_slots,
    NLU_RETURN_TOP_N_OPTIONS,
    NEXT_BEST_OPTIONS,
    CONFIDENCE_DROPOUT_THRESHOLD,
    POSSIBLE_USER_QUESTIONS,
    OPPOSITE_CHOICE,
)

updater = SimpleStateUpdater()
decider = DialogueDecider()

# this maps the name of classes from the pipeline model to our slot names
pipline_slot_name_mapping = {
    "Price": "pricerange",
    "Cuisine": "food",
    "Location": "area",
    "Amenity": "area",
    "Restaurant_Name": "name",
}


# import the rules configuration
with open("resources/CamRestaurants-rules.json", "r") as file:
    rules = json.load(file)

foodtypes_with_empty_space = [
    food for food in rules["slotvalues"]["food"] if " " in food
]

# these string indicate that the user does not care which option
# is choosen. e.g "I dont care about the price range"
dont_care_options = ["dont care", "any", "no preference", "surprise me"]


def clean_restaurant_name_for_lookup(word: str):
    for word_to_remove in ("the", "restaurant"):
        word = word.replace(word_to_remove, "")
        word = word.replace(word_to_remove.capitalize(), "")
    return word


embedded = {
    "food": embedding_model.encode(rules["slotvalues"]["food"] + dont_care_options),
    "pricerange": embedding_model.encode(
        rules["slotvalues"]["pricerange"] + dont_care_options
    ),
    "name": embedding_model.encode(
        [clean_restaurant_name_for_lookup(x) for x in rules["slotvalues"]["name"]]
        + dont_care_options
    ),
    "area": embedding_model.encode(rules["slotvalues"]["area"] + dont_care_options),
}

slots_options = ["area", "name", "pricerange", "pricerange", "food", "food"]
slots_options_embedded = embedding_model.encode(
    ["area", "name", "pricerange", "price", "food", "foodtype"]
)

questions_flattened = []
questions_keys = []
for key, questions in POSSIBLE_USER_QUESTIONS.items():
    for question in questions:
        questions_flattened.append(question)
        questions_keys.append(key)

all_questions_encoded = embedding_model.encode(questions_flattened)

dont_care_regex_pattern = r"\bdo\s*(?:not|n['’]?t|nt)\s+care\b"


def merge_entities(ner_output):
    """Merge consecutive named entities in the output of a Named Entity Recognition (NER) model.

    This function takes a list of entities, where each entity is represented as a dictionary
    containing information such as the entity group, word, start and end positions, and score.
    It merges entities that are part of the same group and are consecutive in the text, indicated
    by the presence of subword tokens (e.g., tokens starting with '##').

    Args:
        ner_output (list of dict): A list of dictionaries, where each dictionary represents an entity with the following keys:
            - 'entity_group' (str): The group or type of the entity (e.g., 'PERSON', 'ORG').
            - 'word' (str): The word or token representing the entity.
            - 'start' (int): The starting position of the entity in the text.
            - 'end' (int): The ending position of the entity in the text.
            - 'score' (float): The confidence score of the entity.

    Returns:
        list of dict: A list of merged entities, where consecutive subword tokens are combined into a single entity.
    """
    if not ner_output:
        return []

    merged = []
    current = ner_output[0].copy()

    for next_ent in ner_output[1:]:
        # Check if next is a subword of the same group and is adjacent
        if (
            next_ent["entity_group"] == current["entity_group"]
            # and next_ent["word"].startswith("##")
            and next_ent["start"] - current["end"] <= 1
        ):

            # Merge words (remove '##' from the next word)
            if next_ent["word"].startswith("##"):
                current["word"] += next_ent["word"].removeprefix("##")
            else:
                current["word"] += " " + next_ent["word"]
            current["end"] = next_ent["end"]
            # Combine scores (average)
            current["score"] = (current["score"] + next_ent["score"]) / 2
        else:
            merged.append(current)
            current = next_ent.copy()

    merged.append(current)
    return merged


class Token:
    def __init__(self, text: str):
        self.original_text = text
        self.text = text.translate(str.maketrans("", "", ",.?")).strip()
        self.slot = None
        self.matched = False
        if self.text.lower() == "yes":
            self.answer = "yes"
        elif self.text.lower() == "no":
            self.answer = "no"
        elif re.findall(dont_care_regex_pattern, self.text.lower()) or (
            self.text.upper()
            in (
                "DONTCAREABOUT",
                "ANY",
            )
        ):
            self.answer = "*"
        else:
            self.answer = None

        if text.lower() in ("and", "or"):
            self.connecting = True
        else:
            self.connecting = False

        top_token_match = get_closest_matches(
            slots_options, slots_options_embedded, self.text, top_n=1
        )[0]
        slot = top_token_match["string"]
        assert slot in {"food", "pricerange", "name", "area"}
        confidence = top_token_match["confidence"]
        if confidence >= 0.95:
            self.slot = slot

    def correct_grammar(self):
        if self.text == "DONTCAREABOUT":
            return "don´t care"
        if self.text.lower() == "dish":
            # this will be recognized as danish
            return "dish"
        result_foodtype = difflib.get_close_matches(
            self.text.lower(),
            rules["slotvalues"]["food"],
            n=1,
            cutoff=0.8,
        )

        result_area = difflib.get_close_matches(
            self.text.lower(),
            rules["slotvalues"]["area"],
            n=1,
            cutoff=0.9,
        )
        if result_foodtype:
            return self.original_text.replace(self.text, result_foodtype[0] + " food")
        elif result_area:
            return self.original_text.replace(self.text, result_area[0] + " area")
        else:
            return self.original_text


def tokenize(text: str):
    ready_to_tokenize = ""
    end = 0

    for i, result in enumerate(re.finditer(dont_care_regex_pattern, text.lower())):
        start, end = result.span()
        if i == 0:
            ready_to_tokenize += text[:start]
        else:
            ready_to_tokenize += text[end:start]
        ready_to_tokenize += "DONTCAREABOUT"
    ready_to_tokenize += text[end:]
    ready_to_tokenize = ready_to_tokenize.replace("price range", "pricerange").replace(
        "food type", "foodtype"
    )
    for dont_care_option in dont_care_options:
        ready_to_tokenize = ready_to_tokenize.replace(dont_care_option, "ANY")

    for foodype_with_empty_space in foodtypes_with_empty_space:
        ready_to_tokenize = ready_to_tokenize.replace(
            foodype_with_empty_space, foodype_with_empty_space.replace(" ", "")
        )
    tokens = [Token(x) for x in ready_to_tokenize.split(" ")]
    return tokens


def get_closest_matches(
    valid_options: List[str],
    valid_options_embedded: np.array,
    word: str,
    top_n: int,
) -> List[dict]:
    """Get the closest matches for a given word from a list of valid options based
    on cosine similarity and fuzzy matching.

    Args:
        valid_options (List[str]): A list of valid string options to match against.
        valid_options_embedded (np.array): An array of embeddings corresponding to the valid options.
        word (str): The input word for which to find the closest matches.
        top_n (int): The number of top matches to return.

    Returns:
        List[dict]: A list of dictionaries containing the closest matches, each with the following keys:
            - "string" (str): The matched string.
            - "confidence" (float): The confidence score of the match.
            - "negated" (bool): A flag indicating if the match is negated.
    """
    if " not " in word:
        collect = []
        for i, w in enumerate(word.split(" not ")):
            collect += get_closest_matches(
                valid_options=valid_options,
                valid_options_embedded=valid_options_embedded,
                word="not " if i else "" + w,
                top_n=top_n,
            )
        return collect
    word_embedded = embedding_model.encode(word)

    # get the closest matches by cosine distance in latent space
    norm_array_options = valid_options_embedded / np.linalg.norm(
        valid_options_embedded, axis=1, keepdims=True
    )
    norm_array_query = word_embedded / np.linalg.norm(word_embedded)

    cosine_similarities = np.dot(norm_array_options, norm_array_query)

    top_n_indices = np.argsort(cosine_similarities)[-top_n:][::-1]

    def _get(i, list):
        try:
            return list[i]
        except IndexError:
            return "*"

    top_n_options = [
        {
            "string": _get(index, valid_options),
            "confidence": float(min(0.99999, cosine_similarities[index])),
            "negated": False,
            "backup_for": (
                None if not iteration else _get(top_n_indices[0], valid_options)
            ),
        }
        for iteration, index in enumerate(top_n_indices)
    ]

    # get the closest matches by string overlap
    word = " " + word.strip().lower() + " "
    for i, matched_string in enumerate(
        difflib.get_close_matches(word, valid_options + dont_care_options, n=top_n)
    ):
        top_n_options.append(
            {
                "string": (
                    "*"
                    if (
                        matched_string in dont_care_options
                        or re.findall(" (any|anything|anywhere) ", word)
                    )
                    else matched_string
                ),
                "confidence": (
                    min(
                        0.99999,
                        1
                        - cosine(embedding_model.encode(matched_string), word_embedded),
                    )
                ),
                "negated": False,
                "backup_for": None if not i else top_n_options[0]["string"],
            }
        )

    # check if the word is negated
    if re.findall(" (not) ", word):
        for option in top_n_options:
            option["negated"] = True
            # boost confidences due to low similarity of strings containing the negation words
            option["confidence"] = min(0.999, option["confidence"] * 1.3)
    return top_n_options


class SimpleNLU(object):
    def __init__(self):
        pass

    def _clean_text(self, text: str) -> str:
        """Cleans the input text by removing extra spaces and ensuring proper formatting.

        This method replaces multiple consecutive spaces with a single space and adds
        leading and trailing spaces to the text. This is done to ensure that subsequent
        regex operations work as expected.

        Args:
            text (str): The input string that needs to be cleaned.

        Returns:
            str: The cleaned string with extra spaces removed and leading/trailing spaces added.
        """
        if text.startswith("DEBUG"):
            debug = True
            text = text[len("DEBUG") :]
        else:
            debug = False
        text = text.replace(",", ", ")
        while "  " in text:
            text = text.replace("  ", " ").strip()
        text = " " + text + " "
        return text, debug

    def add_greeting(self, slots: dict, text: str) -> dict:
        """Find the greeting message based on regex logic

        Args:
            slots (dict): A dictionary containing intent information.
            text (str): The input text to analyze for keywords.

        Returns:
            dict: The updated slots dictionary with the added greeting slot.
        """
        for text in re.findall(
            r"\b(hi|hello|hey|moin|servus|grüß gott|grüss gott)\b",
            text[:40].lower(),
        ):
            slots["greeting"] = text.title().strip()
            break
        return slots

    def add_goodbye(self, slots: dict, text: str) -> dict:
        """Find the goodbye message based on regex logic

        Args:
            slots (dict): A dictionary containing intent information.
            text (str): The input text to analyze for keywords.

        Returns:
            dict: The updated slots dictionary with the added goodbye slot.
        """
        if re.findall(r"\b(bye|goodbye|good bye)\b", text.lower()):
            slots["goodbye"] = True
        return slots

    def add_dont_like_choice(self, slots: dict, text: str) -> dict:
        """Find the dont like choice message based on regex logic

        Args:
            slots (dict): A dictionary containing intent information.
            text (str): The input text to analyze for keywords.

        Returns:
            dict: The updated slots dictionary with the added dont like choice message.
        """
        if re.findall(
            r"\b(another|different|diferent) (one|restaurant|place|choice)\b",
            text.lower(),
        ):
            slots["dont_like_choice"] = True
        elif re.findall(
            r"\b(dont|do not|don't) (like|want)\s+.*\b(restaurant|restaurante|place|one|choice)\b",
            text.lower(),
        ):
            slots["dont_like_choice"] = True
        return slots

    def add_user_question_with_embedding(
        self,
        slots: dict,
        user_string: str,
        all_questions_encoded: np.ndarray,
        questions_keys: List[str],
        threshold: float = 0.8,
    ) -> dict:
        """Adds a user question to the slots dictionary based on cosine similarity with encoded questions.

        Args:
            slots (dict): A dictionary containing slots to which the user question may be added.
            user_string (str): The user's question as a string.
            all_questions_encoded (np.ndarray): A 2D numpy array containing encoded representations of all possible questions.
            questions_keys (List[str]): A list of keys corresponding to the questions in `all_questions_encoded`.
            threshold (float, optional): The minimum cosine similarity threshold for considering a match. Defaults to 0.8.

        Returns:
            dict: The updated slots dictionary, which may include the new user question if a match is found.
        """

        user_question_encoded = embedding_model.encode(user_string.strip())
        norm_array_options = all_questions_encoded / np.linalg.norm(
            all_questions_encoded, axis=1, keepdims=True
        )
        norm_array_query = user_question_encoded / np.linalg.norm(user_question_encoded)

        cosine_similarities = np.dot(norm_array_options, norm_array_query)

        if max(cosine_similarities) >= threshold:
            slots["user_question"] = questions_keys[np.argmax(cosine_similarities)]
        return slots

    def correct_misspelling(self, text: str) -> str:
        if difflib.get_close_matches(
            text.lower(),
            ["moderate"],
            n=1,
            cutoff=0.8,
        ):
            return "moderately priced"

        tokens = tokenize(text)
        text = " ".join([token.correct_grammar() for token in tokens])
        text = text.replace(" food food ", " food ")
        return text

    def add_user_question_with_substring(
        self,
        slots: dict,
        text: str,
        questions_flattened: List[str],
        questions_keys: List[str],
    ):
        """Adds a user question to the slots dictionary based on the presence of a substring in the provided text.

        Args:
            slots (dict): A dictionary to store user-related information, which will be updated with the user question.
            text (str): The text in which to search for user questions.
            questions_flattened (List[str]): A list of questions to search for in the text.
            questions_keys (List[str]): A list of keys corresponding to the questions in questions_flattened.

        Returns:
            dict: The updated slots dictionary containing the user question if a match is found.
        """
        for i, question in enumerate(questions_flattened):
            if question in text:
                slots["user_question"] = questions_keys[i]
                break
        return slots

    def add_specify_slots_with_ner(self, slots: dict, text: str) -> dict:
        """This function processes the input text using a named entity recognition pipeline,
        identifies relevant entities, and updates the slots dictionary accordingly. It
        also handles negation based on regex logic found in the text.

        Args:
            slots (dict): A dictionary containing intent slots to be updated.
            text (str): The input text from which entities will be extracted.

        Returns:
            dict: The updated slots dictionary with specified slots added based on the recognized entities.
        """
        prior_entity_end_index = 0

        entity_type_regex_mapping = {
            "pricerange": "(expensive|price)",
            "food": f'(exotic|foreign|casual|familiar|{"|".join(rules["slotvalues"]["food"])})',
            "area": "(far|close|long|faar)",
            "name": None,
        }
        entity_type_regex_mapping["name"] = entity_type_regex_mapping["food"]

        slots_builder = []
        text = self.correct_misspelling(text)
        for i, entity in enumerate(merge_entities(ner_pipeline(text))):
            if entity["entity_group"] == "Dish" and entity["word"].lower() in (
                "canapes",
                "light bites",
            ):
                entity["entity_group"] = "Cuisine"
            if entity["entity_group"] not in pipline_slot_name_mapping:
                # the pipeline is based on the MIT dataset which contains some classes
                # not needed for our purposes, we dont use these
                continue
            if difflib.get_close_matches(
                # this can get misidentified as an entity but should not
                entity["word"],
                ["too far", "too close"],
                n=1,
                cutoff=0.8,
            ):
                continue
            invalid_names = ["moi"]
            if entity["word"].strip().lower() in invalid_names:
                continue

            # obtain the entity type / slot name based on our naming scheme
            entity_type = pipline_slot_name_mapping[entity["entity_group"]]

            confidence = float(entity["score"])
            if entity_type == "name":
                confidence = min(0.98, confidence * 1.5)

            word = entity["word"]
            entity_start_index = entity["start"]
            text_since_last_entity = text[prior_entity_end_index:entity_start_index]
            prior_entity_end_index = entity["end"]

            top_n_options = NLU_RETURN_TOP_N_OPTIONS[entity_type]
            if entity_type in ("pricerange", "area"):
                top_n_options = 1

            # only get the first pricerange and area, the next likely choices
            #  will be set rule-based
            found = get_closest_matches(
                valid_options=rules["slotvalues"][entity_type],
                valid_options_embedded=embedded[entity_type],
                word=clean_restaurant_name_for_lookup(word),
                top_n=top_n_options,
            )

            # adjust the confidences by the confidence of the NER model in the prediction itself
            for idx, m in enumerate(found):
                m["confidence"] = float(m["confidence"]) * confidence
                # index == 0 represents the primary match, index >=1 represents all the backup options
                m["index"] = idx

            # add index to backup options: assign index bigger than the primary match
            if (entity_type in ("pricerange", "area")) and (
                m["string"] != "*"
            ):  # found has length one, thus this is the only m
                if entity_type == "area" and m["string"] == "centre":
                    number_of_backup_options_to_use = 3
                else:
                    number_of_backup_options_to_use = (
                        NLU_RETURN_TOP_N_OPTIONS[entity_type] - 1
                    )

                for i in range(number_of_backup_options_to_use):
                    backup_option_string, backup_option_confidence_factor = (
                        NEXT_BEST_OPTIONS[entity_type][m["string"]][i]
                    )
                    found.append(
                        {
                            "string": backup_option_string,
                            "confidence": backup_option_confidence_factor
                            * m["confidence"],  # reduce the base confidence by a factor
                            "negated": m["negated"],
                            "index": m["index"]
                            + 1,  # the index of backup options = index of primary match +1
                            "backup_for": m["string"],
                        }
                    )

            slots_builder.append(
                {
                    "type": entity_type,
                    "word": word,
                    "found": found,
                    "text_before": text_since_last_entity,
                    "text_after": None,
                    "prior_matched_text": None,
                    "subsequent_matched_text": None,
                }
            )
        if slots_builder:
            slots_builder[-1]["text_after"] = text[entity_start_index + len(word) :]

        # set the values of the prior/next matched text and text_after
        for index, slot in enumerate(slots_builder):
            if index > 0:
                slot["prior_matched_text"] = f' {slots_builder[index - 1]["word"]} '
            else:
                slot["prior_matched_text"] = ""

            if index < len(slots_builder) - 1:
                slot["subsequent_matched_text"] = (
                    f' {slots_builder[index + 1]["word"]} '
                )

                def _clean_text(t):
                    return (
                        t.replace("ä", "a").replace("ö", "o").replace("ü", "u").lower()
                    )

                try:
                    start = _clean_text(text).index(
                        slot["word"].removeprefix("##").lower()
                    ) + len(slot["word"])
                    end = _clean_text(text).index(
                        slots_builder[index + 1]["word"].removeprefix("##").lower()
                    )
                except ValueError:
                    # sometimes the substring is not present due to the error in the NER model
                    # rather than throw a ValueError, compromise on nlu accuracy here
                    start, end = 0, 0
                slot["text_after"] = text[start:end]
            else:
                slot["subsequent_matched_text"] = ""

        prior_entity_is_negated = False

        for slot in slots_builder:
            # check if this is a case of the or problem e.g "not german or austrian"
            # in that case, this entity is negated if the prior one is
            negation_regex_type_specific = (
                r"\s(too|dont|don't|don´t|not|not enough)\s"
                + entity_type_regex_mapping[slot["type"]]
            )

            if prior_entity_is_negated and (
                re.findall(" (or|and) ", slot["text_before"])
                or slot["text_before"].strip().replace("food", "") == ","
            ):
                for m in slot["found"]:
                    m["negated"] = True
                prior_entity_is_negated = True

            # if there are any negation indicators, check if they apply to this entity
            elif (
                re.findall(
                    "\s(do not|dont|don't|don´t|not)\s(?!care\s)", slot["text_before"]
                )
                or re.findall(
                    negation_regex_type_specific,
                    slot["text_after"],
                )
                or re.findall(
                    f"no {slot['word']} food",
                    slot["text_before"] + slot["word"] + slot["text_after"],
                )
            ):
                # the current entity is the first entity after a negation indicator
                for m in slot["found"]:
                    m["negated"] = True
                prior_entity_is_negated = True
            elif slot["found"] and slot["found"][0]["negated"]:
                prior_entity_is_negated = True
            else:
                prior_entity_is_negated = False

            for entity in slot["found"]:
                if (
                    slot["type"] in ["area", "pricerange"]
                    and entity["string"] in OPPOSITE_CHOICE[slot["type"]]
                    and entity["negated"] == False
                ):
                    slot["found"].append(
                        {
                            "string": OPPOSITE_CHOICE[slot["type"]][entity["string"]],
                            "confidence": entity["confidence"],
                            "negated": True,
                            "index": entity["index"] + 1,
                            "backup_for": None,
                        }
                    )

            # Conflict resolution: delete the conflicting entries with bigger index, keep the one with smaller index
            cleaned = {}
            for m in slot["found"]:
                key = m["string"]
                if key not in cleaned:
                    cleaned[key] = m
                else:
                    existing = cleaned[key]
                    if existing["negated"] != m["negated"]:
                        # dont overwrite with a backup choice
                        if m["backup_for"] and not existing["backup_for"]:
                            continue
                        # it means there exists conflict, we keep the one with the highher confidence
                        elif m["confidence"] > existing["confidence"]:
                            cleaned[key] = m
            # substitute slot["found"] with the value of cleaned(conflict-resolved entries)
            slot["found"] = list(cleaned.values())

            # add the found entities to the final slots list
            slots["specify"][slot["type"]] += slot["found"]

        return slots

    def add_specify_slots_with_regex(self, slots: dict, text: str) -> dict:
        """Adds specified slots to a given dictionary based on regex matches in the provided text.
        Also sets the answer to None if a dont care claim within the first 40 characters (beginning
        context) is used up for a specify intent.

        Args:
            slots (dict): A dictionary containing slots to be modified.
            text (str): The text in which to search for specific patterns.

        Returns:
            dict: The updated slots dictionary with added specified slots based on regex matches.
        """
        context_length = 50
        for m in re.finditer(dont_care_regex_pattern, text, re.IGNORECASE):
            context = text[m.end() : min(len(text), m.end() + context_length)]
            if re.findall(r"\b(food type)\b", context) or re.findall(
                r"\b(what|which|of) (food|dish|dinner|cuisine)\b", context
            ):
                slots["specify"]["food"].append(
                    {
                        "string": "*",
                        "confidence": 0.8,
                        "negated": False,
                        "backup_for": None,
                    }
                )
                if m.end() < 40:
                    slots["answer"] = None

            if re.findall(r"\b(what|which)area\b", context):
                slots["specify"]["area"].append(
                    {
                        "string": "*",
                        "confidence": 0.8,
                        "negated": False,
                        "backup_for": None,
                    }
                )
                if m.end() < 40:
                    slots["answer"] = None

            if re.findall(
                r"\b(how expensive|how cheap|price range|price level)\b",
                context,
            ):
                slots["specify"]["pricerange"].append(
                    {
                        "string": "*",
                        "confidence": 0.8,
                        "negated": False,
                        "backup_for": None,
                    }
                )
                if m.end() < 40:
                    slots["answer"] = None

        return slots

    def add_specify_slots_and_answer_with_tokenized_logic(
        self, slots: dict, text: str, last_action: DialogueAct
    ) -> dict:
        """Adds specified slots and answers to the provided dictionary using tokenized logic.

        This function processes a given text, tokenizes it, and updates the slots dictionary
        based on the tokens' properties. It identifies the first answer token and manages the c
        ounting of "don't care" tokens to appropriately append specified slots.

        Args:
            slots (dict): A dictionary containing slots to be updated.
            text (str): The input text to be tokenized and analyzed.

        Returns:
            dict: The updated slots dictionary with specified slots and answers.
        """
        tokens = tokenize(text)

        if "surprise me" in text.lower():
            slots["surprise_me"] = True

        first_answer_token = None
        last_dont_care_counting_index = -100
        for i, token in enumerate(tokens):
            if not token.answer is None:
                if first_answer_token is None:
                    first_answer_token = token
                if token.answer == "*":
                    last_dont_care_real_index = i
                    last_dont_care_counting_index = i
            elif token.connecting:
                # connecting words (e.g. and/or) dont  contribute towards the distance
                # to don´t care tokens
                last_dont_care_counting_index += 1

            elif isinstance(token.slot, str) and (
                (i - last_dont_care_counting_index) <= 4
            ):
                slots["specify"][token.slot].append(
                    {
                        "string": "*",
                        "confidence": round(
                            0.7 - (i - last_dont_care_real_index - 2) * 0.06, 4
                        ),
                        "negated": False,
                        "backup_for": None,
                    }
                )
                tokens[last_dont_care_real_index].matched = True
                # slots dont contribute towards the distance to don´t care tokens
                last_dont_care_counting_index += 1
        if not first_answer_token is None:
            if not first_answer_token.matched:
                slots["answer"] = first_answer_token.answer
                previos_slot_type = last_action.slots.get("act_slot", None)
                if (
                    slots["answer"] in ("*", "no")
                    and last_action.intent == "ask"
                    and previos_slot_type in ("food", "pricerange", "area")
                ):
                    slots["specify"][last_action.slots["act_slot"]].append(
                        {
                            "string": "*",
                            "negated": False,
                            "confidence": 0.9999,
                            "backup_for": None,
                        }
                    )
        return slots

    def negate_dont_like_choice_results(self, slots: dict, last_action):
        last_state = last_action.history[-1]
        if last_state.resultList and slots["dont_like_choice"]:
            result = last_state.resultList[0]["name"].lower()
            found = False
            for specification in slots["specify"]["name"]:
                if specification["string"] == result:
                    specification["negated"] = True
                    found = True
            if not found:
                slots["specify"]["name"].append(
                    {
                        "string": result,
                        "confidence": 0.9999,
                        "negated": True,
                        "backup_for": None,
                    }
                )

        return slots

    def drop_backups_for_negations(self, slots: dict) -> dict:
        for slot in slots["specify"]:
            builder = []
            for option in slots["specify"][slot]:
                if option["negated"] and option["backup_for"]:
                    pass
                else:
                    builder.append(option)
            slots["specify"][slot] = builder
        return slots

    def resolve_conflicts(self, slots):
        for slot_type, items in slots["specify"].items():
            by_string = {}
            for item in items:
                key = item["string"]
                if key not in by_string:
                    by_string[key] = item
                else:
                    existing = by_string[key]
                    # if there exists conflict: negated true and negated false appears for the same option
                    if existing["negated"] != item["negated"]:
                        # keep the option with higher confidence
                        if existing["confidence"] < item["confidence"]:
                            by_string[key] = item
            slots["specify"][slot_type] = list(by_string.values())
        return slots

    def add_inform_slots_with_regex(self, slots: dict, text: str) -> dict:
        """Adds inform slots to the provided slots dictionary based on regex logic.

        Args:
            slots (dict): The dictionary containing the slots
            text (str): The input text from which to extract inform slots.

        Returns:
            dict: The updated slots dictionary with new informative slots
        """
        text = text.lower()

        if re.findall(r"\b(phone|telephone|number)\b", text):
            slots["inform"].append("phone")

        if re.findall(r"\b(address|adress|location)\b", text):
            slots["inform"].append("addr")

        if re.findall(r"\bpostcode\b", text):
            slots["inform"].append("postcode")

        if (
            re.findall(r"\b(food type)\b", text)
            or re.findall(r"\b(what|which|of) (food|dish|dinner|cuisine)\b", text)
            and not slots["specify"]["food"]
        ):
            slots["inform"].append("food")

        if re.findall(r"\b(what|which)area\b", text) and not slots["specify"]["area"]:
            slots["inform"].append("area")

        if re.findall(
            r"\b(how expensive|how cheap|what price range|whats the price range|what is the price range|price level)\b",
            text,
        ):
            # remove the inform pricerange slots because the mention
            # of cheap/expensive was meant as part of the inform intent
            slots["specify"]["pricerange"] = []
            slots["inform"].append("pricerange")

        if re.findall(r"\b(signature|specialty)\b", text):
            slots["inform"].append("signature")

        if re.findall(r"\bname\b", text) and not slots["specify"]["name"]:
            slots["inform"].append("name")

        if (
            re.findall(r"\b(description|describe)\b", text)
            or re.findall(
                r"\b(tell me more|more information|tell more|what is special)", text
            )
            or re.findall(r"\b(about) (this|the) (place|restaurant|restaurente)", text)
        ):
            slots["inform"].append("description")

        slots["inform"] = sorted(slots["inform"])
        return slots

    def adjust_probabilities(self, slots: dict) -> dict:
        """Adjusts the confidence probabilities of the slots
        by applying a sharpening technique.

        This method modifies the confidence values of slots based on a specified
        alpha value for each slot. It ensures that the confidence values remain
        non-negative and normalizes them after sharpening.

        Args:
            slots (dict): A dictionary containing slots with
            their associated confidence values.

        Returns:
            dict: The updated slots dictionary with adjusted confidence values.

        Raises:
            ValueError: If any confidence value in the input is negative.
        """

        def _sharpen_confidences(confidences: list, alpha: Union[int | float]):
            """Sharpen the confidence values using a power transformation.

            This function takes a list  of confidence values and sharpens them by
            raising each confidence to the power of a specified alpha. The resulting
            values are then normalized to sum to the original total of the input
            confidences, with a cap of 0.999 applied to each value.

            Args:
                confidences (list or np.ndarray): A list of confidence values
                    that must be non-negative.
                alpha (float): The exponent to which each confidence value will be raised.

            Returns:
                list: A list of sharpened confidence values, each capped at 0.999.

            Raises:
                ValueError: If any confidence value is negative.
            """
            confidences = np.array(confidences)

            if np.any(confidences < 0):
                raise ValueError("Confidences must be non-negative.")

            sharpened = np.power(confidences, alpha)

            sharpened /= np.sum(sharpened)

            sharpened = sharpened * sum(confidences)

            return [min(x, 0.999) for x in sharpened]

        # adjust the probabilities
        for slot, alpha in [
            # area probabilities are always high because the similarities of areas are so close
            ("area", 2),
        ]:
            probabilities = [x["confidence"] for x in slots["specify"][slot]]
            sharpened_confidences = _sharpen_confidences(probabilities, alpha)
            for i, m in enumerate(slots["specify"][slot]):
                m["confidence"] = sharpened_confidences[i]
        return slots

    def filter_low_confidence_matches(self, slots: dict) -> dict:
        """Remove matches with confidence lower than the threshold for each slot.

        Args:
            slots (dict): The slots dictionary containing slot predictions.

        Returns:
            dict: The slots dictionary after low-confidence predictions have been removed.
        """
        for slot, threshold in CONFIDENCE_DROPOUT_THRESHOLD.items():
            filtered = [
                item
                for item in slots["specify"][slot]
                if item["confidence"] >= threshold
            ]
            slots["specify"][slot] = filtered
        return slots

    def increment_last_action(
        self,
        slots: dict,
        last_action,  # Union[DialogueState, None]
    ):

        last_state = last_action.history[-1]
        this_action = DialogueAct("find.restaurant", slots, last_action.history)
        next_state = updater.update(last_state, this_action)
        next_action = decider.actOn(next_state)

        if isinstance(next_action, list):
            next_action = next_action[0]

        last_user_prompt = f"{last_action.intent}\\{last_action.slots.get('act_slot')}"
        next_user_prompt = f"{next_action.intent}\\{next_action.slots.get('act_slot')}"
        slots["user_prompt"] = next_user_prompt

        if last_user_prompt == next_user_prompt:
            slots["n_failures"] = last_state.slots["n_failures"] + 1
        else:
            slots["n_failures"] = 0
        return slots

    def parse(
        self,
        text: str,
        last_action=None,  # DialogueState
    ) -> DialogueAct:
        """Parse the input text to extract dialogue slots and return a structured dialogue act.

        Args:
            text (str): The input text to be parsed for dialogue slots.

        Returns:
            DialogueAct: An object representing the parsed dialogue act, including identified slots and their associated data.
        """
        if last_action is None:
            last_action = get_greet_act()
        elif isinstance(last_action, list):
            last_action = last_action[0]

        text, debug = self._clean_text(text)

        slots = get_default_slots()

        slots = self.add_greeting(slots, text)
        slots = self.add_goodbye(slots, text)
        slots = self.add_dont_like_choice(slots, text)
        slots = self.add_user_question_with_embedding(
            slots, text, all_questions_encoded, questions_keys, threshold=0.8
        )
        slots = self.add_user_question_with_substring(
            slots, text, questions_flattened, questions_keys
        )
        slots = self.add_specify_slots_with_ner(slots, text)
        slots = self.add_specify_slots_with_regex(slots, text)
        slots = self.add_specify_slots_and_answer_with_tokenized_logic(
            slots, text, last_action
        )
        slots = self.negate_dont_like_choice_results(slots, last_action)
        slots = self.drop_backups_for_negations(slots)
        slots = join_identical_predictions(slots)
        slots = self.resolve_conflicts(slots)
        slots = self.add_inform_slots_with_regex(slots, text)
        slots = self.adjust_probabilities(slots)
        slots = self.filter_low_confidence_matches(slots)
        slots = self.increment_last_action(slots, last_action)

        act = DialogueAct(
            "find.restaurant", slots
        )  # always assume the find.restaurant intent for now

        # TODO: remove this for production
        if debug:
            act.DEBUG = True
            print(f"SimpleNLU: {act}\n")

        return act
