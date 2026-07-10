from openai import OpenAI
import json

client = OpenAI()

def classify_grant_text(title:str, abstract:str, prompt:str):

    response = client.responses.create(
        model="gpt-5.4-mini",
        reasoning={"effort": "medium"},
        input=[{"role": "system", "content": prompt}, 
               {"role": "user", "content": f"Title: {title}\nAbstract: {abstract}"}]
                   )

    # Extract the model's output text
    output = response.output_text

    return json.loads(output)
