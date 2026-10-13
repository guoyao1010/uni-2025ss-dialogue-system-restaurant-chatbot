TEMPLATES = {
    "ask": {
        # food
        "food0": "What foodtype are you looking for?",
        "food1": "Which type of food are you interested in?",
        "food2": "What kind of cuisine would you like?",
        # price range
        "pricerange0": "Do you have a preferred price range?",
        "pricerange1": "What price range are you aiming for?",
        "pricerange2": "Is there a price range you prefer?",
        # name
        "name0": "Is there a specific restaurant you're interested in?",
        "name1": "Do you already have a restaurant in mind?",
        "name2": "Are you looking for a particular restaurant?",
        # area
        "area0": "Which area are you looking in?",
        "area1": "What part of town are you interested in?",
        "area2": "Which city area would you like to search in?",
        # restaurant clarification
        "restaurant_clarification0": "I fear I didn't quite catch that. Could you rephrase how your prefered restaurant is named?",
        "restaurant_clarification1": "I'm sorry, I didn't understand the restaurant name. Could you repeat it?",
        "restaurant_clarification2": "Could you clarify the name of the restaurant you're referring to?",
        "restaurant_clarification2": "Could you clarify the name of the restaurant you're referring to?",
    },
    "inform": {
        # result
        "result0": "I found a {pricerange} restaurant in the {area} that serves {food} food. The restaurant '{name}' at {address} would be a fitting choice.",
        "result1": "There's a {pricerange} place in the {area} offering {food} food. It's called '{name}' and is located at {address}.",
        "result2": "You might like '{name}', a {pricerange} restaurant in the {area} that offers {food} cuisine. It’s at {address}.",
        # alternative result
        "alternative_result0": "Unfortunately I could not find a restaurant that exactly fits your preferences. However, I found a {pricerange} restaurant in the {area} that serves {food} food. The restaurant '{name}' ar {address} could be a fitting choice.",
        "alternative_result1": "I wasn't able to find a perfect match, but I did find a {pricerange} restaurant in the {area} serving {food} food. '{name}' at {address} might be suitable.",
        "alternative_result2": "No exact match was found, but there is a {pricerange} restaurant in the {area} that serves {food} food. You could check out '{name}' at {address}.",
        # result by name
        "result_by_name0": "I found the restaurant you wanted at the address {address}. '{name}' serves {food} food at a {pricerange} pricerange.",
        "result_by_name1": "The restaurant you're looking for is '{name}', located at {address}. It offers {food} food at a {pricerange} price level.",
        "result_by_name2": "'{name}' is the place you asked for. It's located at {address} and serves {food} cuisine with a {pricerange} price range.",
        # no result
        "no_result0": "I'm sorry, I couldn't find any {pricerange} restaurants in the {area} serving {food} food.",
        "no_result1": "Unfortunately, there are no {pricerange} places in the {area} that offer {food} food.",
        "no_result2": "I couldn't locate a {pricerange} restaurant in the {area} with {food} cuisine. Sorry!",
        # phone
        "phone0": "The phone number of {name} is {phone}.",
        "phone1": "You can reach {name} at {phone}.",
        "phone2": "{name} can be contacted at {phone}.",
        # not phone
        "no_phone0": "I'm sorry but {name} has no phone number listed.",
        "no_phone1": "Unfortunately, there’s no phone number available for {name}.",
        "no_phone2": "{name} doesn't seem to have a listed phone number.",
        # signature dish
        "signature0": "The signature dish of {name} is {signature}.",
        "signature1": "{name}'s signature dish is {signature}.",
        "signature2": "You should try the signature dish at {name}: {signature}.",
        # no signature dish
        "no_signature0": "Sorry, {name} has no signature dish listed.",
        "no_signature1": "Unfortunately, there’s no signature dish for {name}.",
        "no_signature2": "I couldn’t find a signature dish for {name}.",
        # description
        "description0": "Happy to tell you more! {description}.",
        "description1": "Sure! Here's some more info: {description}.",
        "description2": "Here's what I know: {description}.",
        # no description
        "no_description0": "I'm sorry to inform you that {name} has not provided more information about themselves.",
        "no_description1": "Unfortunately, there's no further description for {name}.",
        "no_description2": "I couldn’t find any additional information about {name}.",
    },
    "inform_before_result": {
        "no_result_to_inform0": "Sorry - first you have to tell me where you want to go or give me more information so I can search for a restaurant you might like.",
        "no_result_to_inform1": "Please tell me first where you want to eat or let me ask some further questions so I can help you.",
        "no_result_to_inform2": "At this moment I can't tell you this information. You first have to select a restaurant choice or provide more information.",
    },
    "user_question": {
        # food
        "WHAT_FOOD0": "There are over 20 possible food types. Three examples are: {}, {} or {}.",
        "WHAT_FOOD1": "More than 20 food types are available. For example: {}, {} or {}.",
        "WHAT_FOOD2": "You can choose from over 20 cuisines. Some include: {}, {} or {}.",
        # area
        "WHAT_AREA0": "The possible city areas are: north, west, south, east or centre.",
        "WHAT_AREA1": "You can choose from these areas: north, west, south, east, or centre.",
        "WHAT_AREA2": "Available city regions include: north, west, south, east and centre.",
        # price range
        "WHAT_PRICERANGE0": "The possible price ranges are: cheap, moderate or expensive.",
        "WHAT_PRICERANGE1": "Price options include: cheap, moderate, or expensive.",
        "WHAT_PRICERANGE2": "You can select from the following price ranges: cheap, moderate and expensive.",
        # can do
        "WHAT_CAN_YOU_DO0": "I am designed to assist you in finding restaurants in Cambridge, UK, based on criteria such as cuisine, price, and location. Feel free to tell me your preferences.",
        "WHAT_CAN_YOU_DO1": "I can help you find restaurants in Cambridge, UK, by filtering based on cuisine, price, and location. Just share your preferences with me.",
        "WHAT_CAN_YOU_DO2": "I’m here to assist you in discovering restaurants around Cambridge, UK, according to your desired cuisine, budget, and location. Let me know what you like.",
        # how use
        "HOW_TO_USE0": "I will guide you step by step. You can either answer my questions one by one, or tell me all your preferences in one sentence if you prefer. If you ever change your mind or want to correct something, just let me know – I can update your preferences.",
        "HOW_TO_USE1": "You can give me your preferences all at once or answer my questions step by step. I’ll use that to find the best restaurant match for you. If you change your mind, no worries – I can adjust things anytime.",
        "HOW_TO_USE2": "Just tell me what you're looking for – either all in one go or one step at a time. I’ll help you find the right place, and if your preferences change, I can update the search accordingly.",
        # out of scope
        "OUT_OF_SCOPE0": "Sorry, that's a bit outside what I can do right now, but I'd be happy to help you find a place to eat.",
        "OUT_OF_SCOPE1": "I'm afraid I can't help with that, but I can help you find a restaurant in Cambridge.",
        "OUT_OF_SCOPE2": "That's beyond my capabilities for now. But if you're hungry, I can definitely help with restaurant suggestions.",
        # restaurant number
        "RESTAURANT_NUMBER0": "There are 110 restaurants you could choose from.",
        "RESTAURANT_NUMBER1": "You have 110 restaurants to choose between.",
        "RESTAURANT_NUMBER2": "There are 110 restaurants available in the database.",
    },
    "confirm": {  # logik wieder ändern in generator
        "goodbye0": "Just to confirm, should I end our conversation and delete your info?",
        "goodbye1": "Would you like me to end our chat and clear your information?",
        "goodbye2": "Do you want me to close this chat and delete your details?",
    },
    "dont_care": {
        "0": "Got it. I will choose something for you.",
        "1": "Alright! I'll pick you something.",
        "2": "Okay, got it. I'll choose something for you.",
    },
    "deny": {
        "0": "Got it. I will choose something else for you.",
        "1": "Alright! I'll pick you something else.",
        "2": "Okay, got it. I'll choose something else for you.",
    },
    "confirm_select": {
        "0": "Got it.",
        "1": "Alright!",
        "2": "Okay, thanks.",
    },
    "greet": {
        "0": "Hello! How can I help you today?",
        "1": "Hi there! What can I do for you today?",
        "2": "Hello! Do you need any assistance?",
        "3": "Hey! How may I assist you?",
        "4": "Welcome! How can I support you today?",
        "5": "Good day! What can I help you with?",
    },
    "goodbye": {
        "0": "Thank you and goodbye!",
        "1": "Thank you! Wishing you a great day.",
        "2": "Bye! Let me know if you need anything else.",
        "3": "It's been a pleasure. Bye for now!",
        "4": "Thanks for your time. Take care!",
        "5": "Goodbye.",
    },
    "fallback": {
        "": "I'm sorry, I didn't understand that. Could you please rephrase?",
    },
    "impossible": {
        "0": "Sorry, there are no restaurants that could possible satisfy the conditions you have selected. Please update your preferences.",
        "1": "Unfortunately, there are no restaurants that could fit your selected conditions. Please update your preferences.",
        "2": "I'm sorry, but it appears there are no restaurants that could fullfill the criteria you've set. Please consider modifying your preferences.",
    },
}
