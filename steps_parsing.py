# steps_parsing.py

import re
from extract import * 
import spacy 
nlp = spacy.load("en_core_web_sm")


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
# def normalize_ing(ing):
#     words = re.findall(r"[a-z]+", ing.lower())
#     return words[-1] if words else ing.lower()
def normalize_ing(ing):
    doc = nlp(ing.lower())
    # extract nouns and proper nouns
    nouns = [tok.lemma_ for tok in doc if tok.pos_ in ("NOUN", "PROPN")]
    return nouns[-1] if nouns else ing.lower()


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

def is_non_step(line: str):
    """
    Returns True if the line is clearly NOT a real cooking step.
    We filter:
        - author credits like "Recipe by ..."
        - "Recipe developed by ..."
    """
    low = line.lower()

    # remove obvious metadata lines
    if low.startswith("recipe by"):
        return True
    if low.startswith("recipe developed by"):
        return True
    if low.startswith("author:"):
        return True

    return False



################## we can use this to get atomic sentences ##################
def get_atomic_sentences(recipe_dict):
    ingredients = recipe_dict["ingredients"]
    raw_steps = recipe_dict["steps"]

    atomic_sentences = []
    for s in raw_steps:
        atomic_sentences.extend(split_into_atomic_steps(s))

    atomic_sentences = fix_coreference(atomic_sentences, ingredients)

    # merge headers and broken phrases
    atomic_sentences = merge_headers_and_broken_phrases(atomic_sentences)

    # --- NEW FILTER HERE ---
    atomic_sentences = [
        s for s in atomic_sentences 
        if not is_non_step(s)
    ]

    return atomic_sentences

## start normalizing ingredients
def normalize_ingredient(ing):
    # Extract the core ingredient name from the full ingredient string.
    doc = nlp(ing.lower())
    nouns = [tok.lemma_ for tok in doc if tok.pos_ in ("NOUN", "PROPN")]
    return nouns[-1] if nouns else ing.lower()


def sentence_lemmas(text):
    # Convert step sentence into a set of lemma tokens.
    doc = nlp(text.lower())
    return {tok.lemma_ for tok in doc if tok.is_alpha}

# helps normalize ingredients
def clean_ingredient_name(ing: str):
    # Remove trailing preparation notes like ', divided' but keep ingredient name.
    # split off after comma
    base = ing.split(",")[0].strip()
    return base


# this helps collect ingredients
def match_ingredients(text, ingredients):
    result = []
    for ing in ingredients:
        core = normalize_ing(ing)
        if core in text.lower():
            clean = clean_ingredient_name(ing)
            result.append(clean)
    return result



################## we can use this to get ingredients in each step ##################
def get_ingredients_by_step(recipe_dict):
    atomic_steps = get_atomic_sentences(recipe_dict)
    ingredients = recipe_dict["ingredients"]

    final = []
    for _, step_text in enumerate(atomic_steps, start=1):
        final.append(match_ingredients(step_text, ingredients))

    return final

################## this puts all ingredients into one list ##################
def collect_all_ingredients(matches_per_step):
    seen = set()
    final = []

    for step_list in matches_per_step:
        for ing in step_list:
            if ing not in seen:
                seen.add(ing)
                final.append(ing)

    return final



def parse_iso8601_time(iso_str):
    """
    Convert ISO 8601 duration strings (e.g., 'PT55M', 'PT1H30M')
    into a human-readable format.
    """
    if not iso_str or not isinstance(iso_str, str):
        return None
    
    # ISO-8601 pattern
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso_str)
    if not match:
        return iso_str  # fallback, return raw string

    hours = match.group(1)
    minutes = match.group(2)
    seconds = match.group(3)

    parts = []
    if hours:
        parts.append(f"{int(hours)} hour" + ("s" if int(hours) != 1 else ""))
    if minutes:
        parts.append(f"{int(minutes)} minute" + ("s" if int(minutes) != 1 else ""))
    if seconds:
        parts.append(f"{int(seconds)} second" + ("s" if int(seconds) != 1 else ""))

    return " ".join(parts) if parts else None



################## recipe times and servings ##################
def get_recipe_times(recipe_dict):
    """
    Return a dictionary with recipe-level metadata:
    - total time (clean, human readable)
    - number of servings
    """

    total_time = recipe_dict.get("total_time")
    servings   = recipe_dict.get("servings")

    # Handle servings stored as list
    if isinstance(servings, list):
        servings = servings[0] if servings else None

    # Parse total time into human-readable form
    total_time = parse_iso8601_time(total_time)

    return {
        "total_time": total_time,
        "servings": servings
    }



# testing
if __name__ == "__main__":
    

    url = input("Enter recipe URL: ")
    recipe = extract_recipe(url)
    
    atomic = get_atomic_sentences(recipe)
    print("\nATOMIC SENTENCES:")
    for i, s in enumerate(atomic, 1):
        print(f"{i}: {s}")

    matches = get_ingredients_by_step(recipe)

    print(collect_all_ingredients(matches))
    meta = get_recipe_times(recipe)

    print("\nRECIPE METADATA:")
    print("Total Time:", meta["total_time"])
    print("Servings:", meta["servings"])

