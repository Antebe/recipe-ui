import spacy
from steps_parsing import *
from typing import List, Optional

nlp = spacy.load("en_core_web_sm")

class Step:
    """Represents a single step in a process."""
    def __init__(self, step_number, text, ingredients=None, tools=None, methods_primary=None, methods_secondary=None, time=None, temperature=None, context=None):
        self.step_number = step_number
        self.text = text
        self.ingredients = ingredients if ingredients is not None else []
        self.tools = tools if tools is not None else []
        self.methods_primary = methods_primary if methods_primary is not None else []
        self.methods_secondary = methods_secondary if methods_secondary is not None else []
        self.time = time
        self.temperature = temperature
        self.context = context
    
    def __str__(self):
        return """
                Step {step_number}:
                Text: {text} 
                Ingredients: {ingredients}
                Tools: {tools}
                Methods Primary: {methods_primary}
                Methods Secondary: {methods_secondary}
                Time: {time}
                Temperature: {temperature}
                Context: {context}""".format(
                            step_number=self.step_number, text=self.text, ingredients=self.ingredients, tools=self.tools, methods_primary=self.methods_primary, methods_secondary=self.methods_secondary, time=self.time, temperature=self.temperature, context=self.context)
                        
                        
class Ingredient:
    """Represents an ingredient with a name and quantity."""
    def __init__(self, raw, name ,quantity=None, unit=None, descriptor=None, preparation=None):
        self.raw = raw
        self.name = name
        self.quantity = quantity
        self.unit = unit
        self.descriptor = descriptor
        self.preparation = preparation
    
    def __str__(self):
        return f"Ingredient(raw={self.raw}, name={self.name}, quantity={self.quantity}, unit={self.unit}, descriptor={self.descriptor}, preparation={self.preparation})"

class Recipe:
    """Represents a complete recipe."""
    def __init__(self, title: Optional[str] = None, ingredients: Optional[List[Ingredient]] = [], steps: Optional[List[Step]] = [], servings=None, prep_time=None, cook_time=None, total_time=None):
        self.title = title
        self.ingredients = ingredients
        self.steps = steps
        self.servings = servings
        self.prep_time = prep_time
        self.cook_time = cook_time
        self.total_time = total_time
    
    def __str__(self):
        return f"Recipe(title={self.title}, ingredients={self.ingredients}, steps={self.steps}, servings={self.servings}, prep_time={self.prep_time}, cook_time={self.cook_time}, total_time={self.total_time})"
     
def sentence_to_step(sentence: str, step_number: int = 1) -> Step:
    """Converts a sentence into a structured Step representation using NLP parsing."""
    doc = nlp(sentence)

    # Extract main verb as primary methods
    verbs = [token.lemma_ for token in doc if token.pos_ == "VERB"]
    methods_primary = verbs[:1]
    methods_secondary = verbs[1:]

    # Extract nouns and potential tools
    nouns = [token.text for token in doc if token.pos_ in {"NOUN", "PROPN"}]
    tools = [n for n in nouns if n.lower() in {"pan", "bowl", "oven", "knife", "pot", "spatula"}]
    
    #  time and temperature expressions
    time = None
    temperature = None
    for ent in doc.ents:
        if ent.label_ in {"TIME", "DATE"}:
            time = ent.text
        elif ent.label_ == "QUANTITY" or "°" in ent.text:
            temperature = ent.text

    # Heuristic ingredient recognition (we will use a precompiled list later)
    ingredients = []
    # for token in doc:
    #     #print(token.text, token.dep_, token.pos_)
    #     if token.dep_ in {"dobj", "pobj", "conj"} and token.pos_ == "NOUN":
    #         ingredients.append(Ingredient(raw=token.text, name=token.lemma_))

    step = Step(
        step_number=step_number,
        text=sentence,
        ingredients=ingredients,
        tools=tools,
        methods_primary=methods_primary,
        methods_secondary=methods_secondary,
        time=time,
        temperature=temperature,
        context=None
    )
    return step
UNITS = {
    "teaspoon", "teaspoons",
    "tablespoon", "tablespoons",
    "cup", "cups",
    "clove", "cloves",
    "bunch", "bunches",
    "pound", "pounds",
    "ounce", "ounces",
    "gram", "grams",
    "kilogram", "kilograms",
}

def text_to_ingredient(text):
    """Converts an ingredient phrase into an Ingredient object using simple NLP cues."""
    doc = nlp(text)

    quantity = None
    unit = None
    tokens_left = []

    # pass 1: quantity + unit extraction
    for token in doc:
        if token.like_num and quantity is None:
            quantity = token.text
        elif token.lemma_.lower() in UNITS and unit is None:
            unit = token.lemma_.lower()
        else:
            tokens_left.append(token)

    # pass 2: from the remaining tokens, pick last NOUN as name
    name = None
    descriptors = []

    for token in tokens_left:
        if token.pos_ == "NOUN":
            name = token.lemma_
        else:
            descriptors.append(token.text)

    # if no noun found, fall back to all text
    if name is None and tokens_left:
        name = tokens_left[-1].lemma_
        descriptors = [t.text for t in tokens_left[:-1]]

    descriptor = " ".join(descriptors) if descriptors else None

    return Ingredient(
        raw=text,
        name=name,
        quantity=quantity,
        unit=unit,
        descriptor=descriptor,
        preparation=None,
    )


import re

def url_to_recipe(url: str) -> Recipe:
    R = Recipe()
    recipe_url = url
    recipe = extract_recipe(recipe_url)
    atomic = get_atomic_sentences(recipe)
    print("\nATOMIC SENTENCES:")
    for i, s in enumerate(atomic, 1):
        print(f"{i}: {s}")

    matches = get_ingredients_by_step(recipe)
    ingredients = collect_all_ingredients(matches)
    for ing in ingredients:
        R.ingredients.append(text_to_ingredient(ing))
    for i, step_text in enumerate(atomic, 1):
        R.steps.append(sentence_to_step(step_text, step_number=i))

    # Match ingredients to steps with partial quantity extraction
    for step in R.steps:
        step_text_lower = step.text.lower()
        step_doc = nlp(step.text)
        matched_ingredients = []
        
        for ingredient in R.ingredients:
            if not ingredient.name:
                continue
                
            ing_name_lower = ingredient.name.lower()
            pattern = r'\b' + re.escape(ing_name_lower) + r'\b'
            
            if re.search(pattern, step_text_lower):
                # Check if there's a partial quantity mentioned in the step
                partial_quantity = None
                partial_unit = None
                
                # Look for numbers and units near the ingredient name in the step
                for i, token in enumerate(step_doc):
                    if token.text.lower() == ing_name_lower or token.lemma_.lower() == ing_name_lower:
                        # Look backwards for quantity and unit
                        for j in range(max(0, i-5), i):
                            if step_doc[j].like_num:
                                partial_quantity = step_doc[j].text
                            if step_doc[j].lemma_.lower() in UNITS:
                                partial_unit = step_doc[j].lemma_.lower()
                        break
                
                # Create a new Ingredient object with partial quantity if found
                if partial_quantity or partial_unit:
                    partial_ing = Ingredient(
                        raw=f"{partial_quantity or ''} {partial_unit or ''} {ingredient.name}".strip(),
                        name=ingredient.name,
                        quantity=partial_quantity,
                        unit=partial_unit or ingredient.unit,
                        descriptor=ingredient.descriptor,
                        preparation=ingredient.preparation
                    )
                    matched_ingredients.append(partial_ing)
                else:
                    # No partial quantity found, use the full ingredient
                    matched_ingredients.append(ingredient)
        
        step.ingredients = matched_ingredients
    
    return R

if __name__ == "__main__":
    recipe_url = "https://www.allrecipes.com/recipe/8934/garlic-chicken-stir-fry/"
    R = url_to_recipe(recipe_url)

    print("\nSTRUCTURED RECIPE:")
    
    for ing in R.ingredients:
        print(ing)
    for step in R.steps:
        print(40*"-")
        print(step.step_number)
        print(step.text)
        for ing in step.ingredients:
            print(f"Ingredient: {ing}")
