import spacy
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
        
def sentence_to_step(sentence: str, step_number: int = 1) -> Step:
    """Converts a sentence into a structured Step representation using NLP parsing."""
    doc = nlp(sentence)

    # Extract main verb(s) as primary methods
    verbs = [token.lemma_ for token in doc if token.pos_ == "VERB"]
    methods_primary = verbs[:1]
    methods_secondary = verbs[1:]

    # Extract nouns and potential tools (simple heuristic)
    nouns = [token.text for token in doc if token.pos_ in {"NOUN", "PROPN"}]
    tools = [n for n in nouns if n.lower() in {"pan", "bowl", "oven", "knife", "pot", "spatula"}]
    
    # Extract time and temperature expressions
    time = None
    temperature = None
    for ent in doc.ents:
        if ent.label_ in {"TIME", "DATE"}:
            time = ent.text
        elif ent.label_ == "QUANTITY" or "°" in ent.text:
            temperature = ent.text

    # Heuristic ingredient recognition (could use a precompiled list)
    ingredients = []
    for token in doc:
        #print(token.text, token.dep_, token.pos_)
        if token.dep_ in {"dobj", "pobj", "conj"} and token.pos_ == "NOUN":
            ingredients.append(Ingredient(raw=token.text, name=token.lemma_))

    # Build the Step
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

if __name__ == "__main__":
    text = "Mix the flour and sugar in a bowl." 
    step_text = sentence_to_step(text)
    print(step_text)
    for ing in step_text.ingredients:
        print(ing)    