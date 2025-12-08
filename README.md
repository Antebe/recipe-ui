# recipe-ui
Making recipes navigable PART 3
GitHub: https://github.com/Antebe/recipe-ui/tree/part2
# Main Changes

From 
Part 1 -- borrow rerouting to Google and YouTube; keep step navigation idea

Part 2 -- Use Gemini as a parser

# 3 capabilities
Flexible wording for navigation and ingredients clarification
Reduced hallucinations by rerouting to Google/Youtube to clarify an action
Breakdown steps per request 


# Set-up

```
pip install -r reqs.txt
python -m spacy download en_core_web_sm
```
Put your Gemini API key in .env file

# Run

For the CLI interface, please run this command: 

```
python main.py
```


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


# Examples
#https://www.allrecipes.com/recipe/219077/chef-johns-perfect-mashed-potatoes/
#https://www.allrecipes.com/recipe/236703/chef-johns-chicken-kiev/