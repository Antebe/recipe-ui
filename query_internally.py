# import re
# from typing import Optional
# import spacy
from utils import *

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
                if ing.name and ingredient_name in ing.name.lower():
                    return format_ingredient_quantity(ing)
            
            return f"I couldn't find {ingredient_name} in the recipe."
        
        # Vague question - "How much of that do I need?"
        elif any(word in question_lower for word in ["that", "it", "this"]) and current_step is not None:
            if current_step.ingredients:
                # Return the last ingredient mentioned in the current step
                last_ing = current_step.ingredients[-1]
                return format_ingredient_quantity(last_ing)
            return "No ingredients mentioned in this step."
    
    return "I'm not sure how to answer that question."


def extract_ingredient_from_question(question_lower: str, doc) -> Optional[str]:
    """Extract ingredient name from question using NLP."""
    # Skip question words and common non-ingredient nouns
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
    
    print("\n" + "="*60)
    print("QUESTION ANSWERING EXAMPLES")
    print("="*60)
    
    # 1. General timing questions
    print("\n1. GENERAL QUESTIONS:")
    print("-" * 40)
    q1 = "How long does cooking take?"
    print(f"Q: {q1}")
    print(f"A: {answer_recipe_question(q1, R)}")
    
    q2 = "What is the total time?"
    print(f"\nQ: {q2}")
    print(f"A: {answer_recipe_question(q2, R)}")
    
    # 2. Step parameter queries (with step context)
    print("\n\n2. STEP PARAMETER QUERIES:")
    print("-" * 40)
    
    # Temperature question at step 3
    q3 = "What temperature should the oven be?"
    print(f"Q (at step 3): {q3}")
    print(f"A: {answer_recipe_question(q3, R, step_id=3)}")
    
    # Time question at step 2
    q4 = "How long do I bake it?"
    print(f"\nQ (at step 2): {q4}")
    print(f"A: {answer_recipe_question(q4, R, step_id=2)}")
    
    # When is it done
    q5 = "When is it done?"
    print(f"\nQ (at step 4): {q5}")
    print(f"A: {answer_recipe_question(q5, R, step_id=4)}")
    
    # Substitution question
    q6 = "What can I use instead of soy sauce?"
    print(f"\nQ (at step 5): {q6}")
    print(f"A: {answer_recipe_question(q6, R, step_id=5)}")
    
    # 3. Quantity questions
    print("\n\n3. QUANTITY QUESTIONS:")
    print("-" * 40)
    
    # Specific ingredient
    q7 = "How much garlic do I need?"
    print(f"Q: {q7}")
    print(f"A: {answer_recipe_question(q7, R)}")
    
    q8 = "How much soy sauce?"
    print(f"\nQ: {q8}")
    print(f"A: {answer_recipe_question(q8, R)}")
    
    q9 = "How many chicken breasts?"
    print(f"\nQ: {q9}")
    print(f"A: {answer_recipe_question(q9, R)}")
    
    # Vague reference (step-dependent)
    q10 = "How much of that do I need?"
    print(f"\nQ (at step 3 - vague): {q10}")
    print(f"A: {answer_recipe_question(q10, R, step_id=3)}")
    
    q11 = "How much of it?"
    print(f"\nQ (at step 1 - vague): {q11}")
    print(f"A: {answer_recipe_question(q11, R, step_id=1)}")
    
    # Mixed examples
    print("\n\n4. MIXED CONTEXT EXAMPLES:")
    print("-" * 40)
    
    q12 = "What temperature?"
    print(f"Q (at step 5): {q12}")
    print(f"A: {answer_recipe_question(q12, R, step_id=5)}")
    
    q13 = "How much salt do I need?"
    print(f"\nQ (at step 2): {q13}")
    print(f"A: {answer_recipe_question(q13, R, step_id=2)}")