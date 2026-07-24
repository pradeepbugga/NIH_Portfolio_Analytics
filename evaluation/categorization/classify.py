from openai import OpenAI
import json

client = OpenAI()


def classify_grant_text(title: str, abstract: str, prompt: str):

    """
    Classifies the grant text (title and abstract) using the OpenAI API.

    Parameters:
    ----------
    title : str
        The title of the grant.
    abstract : str
        The abstract of the grant.
    prompt : str
        The prompt to guide the classification process.
    
    Returns:
    -------
    dict
        A dictionary containing the classification results from the model.
    """

    response = client.responses.create(
        model="gpt-5.4-mini",
        reasoning={"effort": "medium"},
        input=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Title: {title}\nAbstract: {abstract}"},
        ],
    )

    # Extract the model's output text
    output = response.output_text

    return json.loads(output)
