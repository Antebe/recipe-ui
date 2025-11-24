# recipe-ui
Making recipes navigable

# Set-up

```
pip install -r reqs.txt
```

# Run

For the CLI interface, please run this command: 

```
python main.py
```

# Recipe Retrieval and Display

  [1] Show ingredients

  [2] Walk through steps

  [3] Show a recipe summary

# Navigation

next

previous/back

repeat/again

what step/where am i 

how many steps

what's left

exit

# Step Parameter Queries

How much X is needed? 

How many X do I need? 

How long will it take?

What temperature should it be?  

# External clarification

What is X?

How to X?

what can i use instead of X?

What is the safe temperature for X?

Conversion: e.g., what is 2 cups in ml?

# Full credit requirements

We are also parsing for descriptor and preparation
```
class Ingredient:
    """Represents an ingredient with a name and quantity."""
    def __init__(self, raw, name ,quantity=None, unit=None, descriptor=None, preparation=None):
        ....
        self.descriptor = descriptor
        self.preparation = preparation
```

# Examples
#https://www.allrecipes.com/recipe/219077/chef-johns-perfect-mashed-potatoes/
#https://www.allrecipes.com/recipe/236703/chef-johns-chicken-kiev/