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

class Ingredient:
    """Represents an ingredient with a name and quantity."""
    def __init__(self, raw, name ,quantity=None, unit=None, descriptor=None, preparation=None):
        self.raw = raw
        self.name = name
        self.quantity = quantity
        self.unit = unit
        self.descriptor = descriptor
        self.preparation = preparation
        

def parse_url(url):
    """Parses the given URL and returns its components."""
    text = ""
    return text 

def sentence_to_step():
    """Converts a sentence into a step representation."""
    text = ""
    return text