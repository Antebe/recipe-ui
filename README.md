# recipe-ui
Making recipes navigable
GitHub: https://github.com/Antebe/recipe-ui/tree/part2
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
# model name
gemini-2.5-flash

# llm prompt
Your role is to return recipe steps, ingredients, and answer questions of the user. You will scrape the HTML provided and extract steps, ingredients, and important rules. 
Separate the steps into atomic sentences to make clear singular steps for the user. Hold each step in a class. When prompted, return singular steps. 
Return ingredients when prompted. When prompted with questions outside of the recipe, guide the user to a youtube or google link for "how to" questions.


Here is the recipe context:

{recipe_text}

Wait for the next user question and answer based only on this recipe.