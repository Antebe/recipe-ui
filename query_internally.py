# query_internally.py
from utils import *
import re
import spacy
from typing import Optional

class RecipeState:
    """Tracks the user's position within a recipe."""
    def __init__(self, recipe: Recipe):
        self.recipe = recipe
        self.current_step = 1

    def total_steps(self):
        return len(self.recipe.steps)
    
nlp = spacy.load("en_core_web_sm")

def answer_recipe_question(question: str, recipe: Recipe, step_id: Optional[int] = None) -> str:
    """
    Answers questions about a recipe based on the question type and context.
    
    Args:
        question: The user's question
        recipe: Recipe object containing all recipe information
        step_id: Current step number (1-indexed), None if not in a specific step
    
    Returns:
        Answer string
    """
    question_lower = question.lower().strip()
    doc = nlp(question)
    
    # Get current step if step_id is provided
    current_step = None
    if step_id is not None and 0 < step_id <= len(recipe.steps):
        current_step = recipe.steps[step_id - 1]
    
    # 1. GENERAL TIMING QUESTIONS - "how long does cooking take?"
    if any(phrase in question_lower for phrase in ["how long", "cooking time", "total time"]):
        if recipe.total_time:
            return f"The total time is {recipe.total_time}."
        elif recipe.cook_time:
            return f"The cooking time is {recipe.cook_time}."
        elif recipe.prep_time:
            return f"The preparation time is {recipe.prep_time}."
        return "No timing information available."
    
    # 2. STEP PARAMETER QUERIES (only when step_id is provided)
    if current_step is not None:
        
        # Temperature questions - "What temperature should the oven be?"
        if any(word in question_lower for word in ["temperature", "temp", "degrees"]):
            if current_step.temperature:
                return f"{current_step.temperature}"
            return "No temperature specified for this step."
        
        # Time questions for current step - "How long do I bake it?"
        if any(phrase in question_lower for phrase in ["how long", "when is it done"]):
            if current_step.time:
                return f"{current_step.time}"
            return "No time specified for this step."
        
        # Substitution questions - "What can I use instead of butter?"
        if any(phrase in question_lower for phrase in ["instead of", "substitute", "replace"]):
            ingredient_name = extract_ingredient_from_question(question_lower, doc)
            if ingredient_name:
                # Check if ingredient is in current step
                for ing in current_step.ingredients:
                    if ing.name and ingredient_name in ing.name.lower():
                        return f"Common substitutes depend on context. For {ing.name}, consider checking a substitution guide."
                return f"I don't see {ingredient_name} in this step."
            return "Which ingredient would you like to substitute?"
    
    # 3. QUANTITY QUESTIONS - "How much salt do I need?" or "How much of that do I need?"
    if any(phrase in question_lower for phrase in ["how much", "how many"]):
        
        # Specific ingredient question
        ingredient_name = extract_ingredient_from_question(question_lower, doc)
        
        if ingredient_name:
            # If we have a current step, check step ingredients first
            if current_step is not None:
                for ing in current_step.ingredients:
                    if ing.name and ingredient_name in ing.name.lower():
                        return format_ingredient_quantity(ing)
            
            # Fall back to recipe-level ingredients
            for ing in recipe.ingredients:
                # Check both name and raw string for matches
                if ing.name and ingredient_name in ing.name.lower():
                    return format_ingredient_quantity(ing)
                if ing.raw and ingredient_name in ing.raw.lower():
                    return format_ingredient_quantity(ing)
            
            return f"I couldn't find {ingredient_name} in the recipe."
        
        # Vague question - "How much of that do I need?"
        elif any(word in question_lower for word in ["that", "it", "this"]) and current_step is not None:
            if current_step.ingredients:
                # Return the last ingredient mentioned in the current step
                last_ing = current_step.ingredients[-1]
                return format_ingredient_quantity(last_ing)
            return "No ingredients mentioned in this step."
        
        # 3b. STEP INGREDIENT LIST - "what do I need for this step?"
        if current_step is not None and any(phrase in question_lower for phrase in [
            "what do i need", "what do we need", "what's needed", "what is needed",
            "ingredients for this", "ingredients for the step", "for this step"
        ]):
            if current_step.ingredients:
                ing_list = ", ".join(format_ingredient_quantity(ing) for ing in current_step.ingredients)
                return f"For this step you need: {ing_list}"
            return "No specific ingredients mentioned for this step."
    
    # 4. INGREDIENT LIST QUESTIONS - "what are the ingredients?"
    if any(phrase in question_lower for phrase in ["what are the ingredients", "show ingredients", "list ingredients", "what ingredients"]):
        if recipe.ingredients:
            ing_list = ", ".join(ing.raw for ing in recipe.ingredients)
            return f"Ingredients: {ing_list}"
        return "No ingredients listed."
        
    
    
    return "I'm not sure how to answer that question."


def extract_ingredient_from_question(question_lower: str, doc) -> Optional[str]:
    skip_words = {
        "much", "many", "step", "recipe", "question", "amount", "quantity",
        "time", "temperature", "minutes", "hours", "degrees", "oven", "it",
        "that", "this", "instead", "substitute", "use"
    }
    
    # Extract nouns that might be ingredients
    for token in doc:
        if token.pos_ in {"NOUN", "PROPN"} and token.text.lower() not in skip_words:
            return token.text.lower()
    
    return None


def format_ingredient_quantity(ingredient: Ingredient) -> str:
    """Format an ingredient's quantity information into a readable answer."""
    parts = []
    
    if ingredient.quantity:
        parts.append(ingredient.quantity)
    
    if ingredient.unit:
        parts.append(ingredient.unit)
    
    if ingredient.descriptor:
        parts.append(ingredient.descriptor)
    
    parts.append(ingredient.name if ingredient.name else "ingredient")
    
    if parts:
        return " ".join(parts)
    else:
        return ingredient.raw if ingredient.raw else "Amount not specified"


########## navigation questions #############

ORDINAL_MAP = {
    "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
    "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10
}

def answer_navigation_question(q: str, state):
    """
    Handles navigation-only questions using RecipeState.
    q = user question (string)
    state = RecipeState object
    Returns: (response, new_step_id)
    """

    text = q.lower().strip()
    total = state.total_steps()

    # A1 — Step Navigation
    # absolute: "step 5" / "go to the third step"
    m = re.search(r"step\s+(\d+)", text)
    if m:
        target = int(m.group(1))
        if 1 <= target <= total:
            state.current_step = target
            return f"Step {target}: {state.recipe.steps[target-1].text}", target
        return f"Step {target} is out of range (1-{total}).", state.current_step

    # ordinal version: "go to the third step"
    for word, num in ORDINAL_MAP.items():
        if word in text:
            if 1 <= num <= total:
                state.current_step = num
                return f"Step {num}: {state.recipe.steps[num-1].text}", num

    # next
    if "next" in text:
        if state.current_step < total:
            state.current_step += 1
        return f"Step {state.current_step}: {state.recipe.steps[state.current_step-1].text}", state.current_step

    # previous / back
    if "previous" in text or "back" in text:
        if state.current_step > 1:
            state.current_step -= 1
        return f"Step {state.current_step}: {state.recipe.steps[state.current_step-1].text}", state.current_step

    # repeat
    if "repeat" in text or "again" in text:
        return f"Step {state.current_step}: {state.recipe.steps[state.current_step-1].text}", state.current_step

    # A3 — Progress/Context
    if "where am i" in text or "what step" in text:
        return f"You are on step {state.current_step} of {total}.", state.current_step

    if "how many steps" in text or "how many total" in text:
        return f"This recipe has {total} steps.", state.current_step

    if "what's left" in text or "what is left" in text:
        remaining = total - state.current_step
        return f"There are {remaining} steps left.", state.current_step

    return "I can’t tell how to navigate from that.", state.current_step


# ORDINAL_MAP = {
#     "first": 1, "1st": 1,
#     "second": 2, "2nd": 2,
#     "third": 3, "3rd": 3,
#     "fourth": 4, "4th": 4,
#     "fifth": 5,  "5th": 5,
#     "sixth": 6,  "6th": 6,
#     "seventh": 7, "7th": 7,
#     "eighth": 8,  "8th": 8,
#     "ninth": 9,  "9th": 9,
#     "tenth": 10, "10th": 10
# }


# def answer_navigation_question(
#     question: str,
#     recipe: Recipe,
#     step_id: Optional[int]
# ) -> tuple[str, Optional[int]]:
#     """
#     Handles navigation / progression questions:
#         - show recipe / show ingredients / show steps
#         - next / previous / repeat
#         - go to step N / jump to the third step
#         - where am I / what step / how many steps
    
#     Returns:
#         (answer_string, updated_step_id)
#     """
    
#     q = question.lower().strip()

#     # load, show commands
#     if any(phrase in q for phrase in [
#         "show recipe", "show me the recipe",
#         "display recipe", "load recipe",
#         "what's the title", "what is the title", "show title"
#     ]):
#         return (f"The recipe title is: {recipe.title}", step_id)

#     if "show ingredients" in q or "list ingredients" in q:
#         ing_list = ", ".join(ing.raw for ing in recipe.ingredients)
#         return (f"Ingredients: {ing_list}", step_id)

#     if ("show steps" in q or "list steps" in q):
#         out = []
#         for s in recipe.steps:
#             out.append(f"{s.step_number}. {s.text}")
#         return ("\n".join(out), 1)

#     if re.search(r"(read|show) step \d+", q):
#         m = re.search(r"step (\d+)", q)
#         if m:
#             n = int(m.group(1))
#             if 1 <= n <= len(recipe.steps):
#                 step_id = n
#                 return (f"Step {n}: {recipe.steps[n-1].text}", step_id)
#             return ("That step number is out of range.", step_id)

#     # NEXT / PREVIOUS / REPEAT / GOTO N
#     # NEXT
#     if q in {"next", "next step"}:
#         if step_id is None:
#             step_id = 1
#         elif step_id < len(recipe.steps):
#             step_id += 1
#         return (f"Step {step_id}: {recipe.steps[step_id-1].text}", step_id)

#     # PREVIOUS / BACK
#     if q in {"previous", "back", "go back"}:
#         if step_id is None or step_id <= 1:
#             step_id = 1
#         else:
#             step_id -= 1
#         return (f"Step {step_id}: {recipe.steps[step_id-1].text}", step_id)

#     # REPEAT
#     if q in {"repeat", "again"}:
#         if step_id is None:
#             return ("We are not on a step yet.", None)
#         return (f"Repeating Step {step_id}: {recipe.steps[step_id-1].text}", step_id)

#     # "jump to the third step"
#     for word, num in ORDINAL_MAP.items():
#         if word in q:
#             if 1 <= num <= len(recipe.steps):
#                 step_id = num
#                 return (f"Step {num}: {recipe.steps[num-1].text}", step_id)
#             return ("That step number is out of range.", step_id)

#     # "step 5"
#     m = re.search(r"step (\d+)", q)
#     if m:
#         num = int(m.group(1))
#         if 1 <= num <= len(recipe.steps):
#             step_id = num
#             return (f"Step {num}: {recipe.steps[num-1].text}", step_id)
#         return ("That step number is out of range.", step_id)

#     # PROGRESS / CONTEXT QUERIES
#     if any(phrase in q for phrase in ["where am i", "what step", "current step"]):
#         if step_id is None:
#             return ("You haven't started the recipe yet.", None)
#         return (f"You are on step {step_id}.", step_id)

#     if "how many steps" in q or "steps total" in q:
#         total = len(recipe.steps)
#         return (f"The recipe has {total} steps.", step_id)

#     if "what's left" in q or "what is left" in q:
#         if step_id is None:
#             return (f"All {len(recipe.steps)} steps are left.", None)
#         remaining = recipe.steps[step_id:]
#         summary = ", ".join(f"Step {s.step_number}" for s in remaining)
#         return (f"Remaining steps: {summary}", step_id)

#     # If not recognized:
#     return ("I'm not sure how to navigate based on that question.", step_id)



if __name__ == "__main__":
    recipe_url = "https://www.allrecipes.com/recipe/236703/chef-johns-chicken-kiev/"
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
    
    
