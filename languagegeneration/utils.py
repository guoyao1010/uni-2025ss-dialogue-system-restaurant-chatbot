import random
import re
from database.database import Database
from languagegeneration.answer_templates import TEMPLATES


database = Database()

# picks three random food examples, that actually are contained in the database
def get_random_food_examples(n=3):
    food_examples = database.get_all_attribute_values("food") #ist das hier das richtige Argument?

    if len(food_examples) < n:
        return food_examples  # Return fewer if there aren't enough options

    return random.sample(tuple(food_examples), n)


# chooses random template answer from a list of options for specific act_type
def get_randomized_template(template_key: str) -> str:
    if template_key not in TEMPLATES:
        raise ValueError(f"Template key '{template_key}' not found in TEMPLATES.")
    templates_for_key = TEMPLATES[template_key]
    if not templates_for_key:
        raise ValueError(f"No templates available for key '{template_key}'.")
    return random.choice(list(templates_for_key.values()))


# randomizes template answers that share their act_type with other answer cases (i.e. "result", "no_result" are both of act_type "inform")
def randomize_by_index(base_key, max_index=2):
    index = random.randint(0, max_index)
    return f"{base_key}{index}"


# removes unnecessary whitespace
def _normalize_whitespace(input_string):
    return re.sub(r"\s+", " ", input_string).strip()
