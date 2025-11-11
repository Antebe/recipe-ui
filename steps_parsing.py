# steps_parsing.py

import re
from utils import Step 
from extract import extract_recipe  


# cooking
COOKING_VERBS = [
    "mix","combine","stir","add","bake","cook","heat","saute","marinate",
    "whisk","chop","cut","slice","pour","boil","simmer","grill","season",
    "coat","rub","transfer","let","serve", "place"
]


# spliting "steps" into singular steps
def split_into_atomic_steps(text: str):
    text = text.replace(";", ". ")
    chunks = re.split(r"[.]\s*", text)
    atomic = []

    for chunk in chunks:
        if not chunk.strip():
            continue

        words = chunk.split()
        current = []
        seen_verb = False

        for i, w in enumerate(words):
            lw = w.lower().strip(",")

            current.append(w)

            # If we hit a cooking verb
            if lw in COOKING_VERBS:

                # If we haven't seen one yet, mark it
                if not seen_verb:
                    seen_verb = True
                    continue

                # Otherwise, decide whether to split or not
                # Dont split if it's the same verb reused
                prev_lw = words[i - 1].lower().strip(",") if i > 0 else ""
                if lw == words[0].lower():
                    # same verb as the start of the sentence
                    continue

                # dont split if preceded by prepositions like "over", "under", "in", "on"
                if prev_lw in ["over", "under", "in", "on", "with", "to", "from", "into", "onto", "at"]:
                    continue

                # OW, split
                before = " ".join(current[:-1]).strip(", ")
                if before:
                    atomic.append(before)
                current = [w]
                seen_verb = True

        final = " ".join(current).strip(", ")
        if final:
            atomic.append(final)

    # Clean up leading "and", "then"
    clean = []
    for a in atomic:
        a = re.sub(r"^(and|then|and then)\s+", "", a.strip(), flags=re.I)
        clean.append(a)

    return clean



# we want to normalize before we fix coreference
def normalize_ing(ing):
    words = re.findall(r"[a-z]+", ing.lower())
    return words[-1] if words else ing.lower()

def fix_coreference(sentences, ingredients):
    # Replace pronouns (they, it, them) with last mentioned ingredient.

    normalized = [normalize_ing(i) for i in ingredients]
    last = None
    output = []

    for s in sentences:
        low = s.lower()

        # update last ingredient mentioned
        for core in normalized:
            if core in low:
                last = core

        # replace pronouns using last ingredient
        if last:
            for p in ["they", "them", "it", "these", "those"]:
                pattern = r"\b" + p + r"\b"
                repl = last.capitalize() if low.startswith(p) else last
                s = re.sub(pattern, repl, s, flags=re.I)

        output.append(s)

    return output

def merge_headers_and_broken_phrases(steps):
    # Merge section headers like 'To make the marinade:' with the following step,
    # and also merge broken lines like
        # 'Cover and'
        # 'marinate for 4 hours'
    
    merged = []
    header_buffer = ""
    phrase_buffer = ""

    for s in steps:
        s = s.strip()

        # 1. If it's a header-like sentence then we buffer it.
        if s.endswith(":") and not any(verb in s.lower() for verb in COOKING_VERBS):
            header_buffer = s
            continue

        # 2. If previous phrase ends with "and" / "to" / "," then merge
        if phrase_buffer:
            s = phrase_buffer + " " + s
            phrase_buffer = ""

        # If this sentence ends with "and" or "to", keep buffering
        if s.lower().endswith(("and", "and then", "to", ",")):
            phrase_buffer = s
            continue

        # 3. Attach any pending header
        if header_buffer:
            s = header_buffer + " " + s
            header_buffer = ""

        merged.append(s)

    # Catch final buffers
    if phrase_buffer:
        merged.append(phrase_buffer)
    if header_buffer:
        merged.append(header_buffer)

    return merged



# this returns the sentences
def get_atomic_sentences(recipe_dict):
    ingredients = recipe_dict["ingredients"]
    raw_steps = recipe_dict["steps"]

    atomic_sentences = []
    for s in raw_steps:
        atomic_sentences.extend(split_into_atomic_steps(s))

    atomic_sentences = fix_coreference(atomic_sentences, ingredients)

    # merge headers and broken phrases
    atomic_sentences = merge_headers_and_broken_phrases(atomic_sentences)

    return atomic_sentences


################## this puts our steps as class step ##################
# def extract_time(text):
#     m = re.search(r"(\d+)\s*(seconds?|minutes?|hours?)", text, re.I)
#     return m.group(0) if m else None

# def extract_temp(text):
#     m = re.search(r"(\d+)\s*(°?F|°?C)", text, re.I)
#     return m.group(0) if m else None

# def extract_methods(text):
#     words = text.lower().split()
#     primary = [w for w in words if w in COOKING_VERBS]
#     secondary = []  # optional extension
#     return primary, secondary

# TOOLS = ["bowl","pan","pot","skillet","knife","oven","sheet","whisk","spatula"]

# def extract_tools(text):
#     return [t for t in TOOLS if t in text.lower()]

# def match_ingredients(text, ingredients):
#     result = []
#     for ing in ingredients:
#         core = normalize_ing(ing)
#         if core in text.lower():
#             result.append(ing)
#     return result


# # here we actually build the step objects
# def build_step_objects(recipe_dict):
#     ingredients = recipe_dict["ingredients"]
#     atomic = get_atomic_sentences(recipe_dict)

#     steps = []
#     for i, text in enumerate(atomic, start=1):
#         primary, secondary = extract_methods(text)
#         time = extract_time(text)
#         temp = extract_temp(text)
#         tools = extract_tools(text)
#         ings = match_ingredients(text, ingredients)

#         steps.append(
#             Step(
#                 step_number=i,
#                 text=text,
#                 ingredients=ings,
#                 tools=tools,
#                 methods_primary=primary,
#                 methods_secondary=secondary,
#                 time=time,
#                 temperature=temp,
#                 context=None
#             )
#         )

#     return steps


# testing
if __name__ == "__main__":
    

    url = input("Enter recipe URL: ")
    recipe = extract_recipe(url)

    atomic = get_atomic_sentences(recipe)
    print("\nATOMIC SENTENCES:")
    print(atomic)

    # print("\nSTEP OBJECTS:")
    # objs = build_step_objects(recipe)
    # for obj in objs:
    #     print(obj.step_number, obj.text, obj.ingredients, obj.methods_primary)
