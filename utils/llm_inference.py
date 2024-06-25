import ollama
import config
import os

ACCEPTED_MODELS = ["llama3", "mistral", "gpt-3.5-turbo", "claude-3-haiku"]
COMMERCIAL_MODELS = ["gpt-3.5-turbo", "claude-3-haiku"]
model = config.MODEL + "_" + config.INFERENCE_TYPE + ":latest"
client_openai = None
client_anthropic = None

def load_model(recreate=False):
    """
    Load the LLM model, creating it if it does not exist.

    Args:
        recreate (bool, optional): Whether to recreate the model if it already exists. Defaults to True.
    """
    if config.MODEL not in ACCEPTED_MODELS:
        raise ValueError(f"Model {config.MODEL} not supported. Accepted models are {ACCEPTED_MODELS}.")
    if config.MODEL in COMMERCIAL_MODELS:
        print(f"Model {config.MODEL} is a commercial model. Please make sure you have the necessary permissions to use it.")
        if config.MODEL == "gpt-3.5-turbo":
            from openai import OpenAI
            client_openai = OpenAI(api_key=config.OPENAI_API_KEY)
        elif config.MODEL == "claude-3-haiku":
            import anthropic
            client_anthropic = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        return
    
    existing_models = ollama.list()
    model_exists = any(existing_model["name"] == model for existing_model in existing_models['models'])
    if model_exists and not recreate:
        print(f"Model {model} found, skipping model creation.")
        return
    elif model_exists and recreate:
        print(f"Model {model} found, deleting model...")
        ollama.delete(model)
        
    print(f"Creating model {model}...")
    current_dir = os.path.dirname(__file__)
    file_path = os.path.join(current_dir, '../' + config.MODELFILE)
    with open(file_path, "r") as f:
        modelfile = f.read()
    ollama.create(model=model, modelfile=modelfile)
    
def generate_financial_analysis_ollama(context: str):
    response = ollama.generate(
        model=model,
        prompt="Esegui un'analisi del bilancio e della salute dell'azienda dato il seguente bilancio:\n" + context
    )
    return response

def get_few_shot_prompt(context):
    def zero_shot_full_prompt(context):
        system_prompt = """
        Sei un analista finanziario. Rispondi in poche righe in italiano interpretando le voci presenti nel bilancio.
        Segui le seguenti regole:
            - Quando scrivi un numero arrotondalo a 2 cifre decimali"""
        user_prompt = """
        Esegui un'analisi del bilancio e della salute dell'azienda dato il seguente bilancio:

        """
        user_prompt += context
        return system_prompt, user_prompt
    def few_shot_full_prompt(context, with_balance):
        system_prompt = config.SYSTEM_FEW_SHOT_WITH_BALANCE if with_balance else config.SYSTEM_FEW_SHOT_WITHOUT_BALANCE
        user_prompt = """
        Esegui un'analisi del bilancio e della salute dell'azienda dato il seguente bilancio:
        """
        user_prompt += context
        return system_prompt, user_prompt
    system_prompt, user_prompt = ""
    if config.INFERENCE_TYPE == "zero_shot":
        system_prompt, user_prompt = zero_shot_full_prompt(context)
    elif config.INFERENCE_TYPE == "few_shot_with_balance":
        system_prompt, user_prompt = few_shot_full_prompt(context, with_balance=True)
    elif config.INFERENCE_TYPE == "few_shot_without_balance":
        system_prompt, user_prompt = few_shot_full_prompt(context, with_balance=False)
    return system_prompt, user_prompt

def generate_financial_analysis_openai(context: str):
    system_prompt, user_prompt = get_few_shot_prompt(context)
    output = client_openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system", "content": system_prompt
            },
            {
                "role": "user", "content": user_prompt
            }
        ]
    )
    return output.choices[0].messages

def generate_financial_analysis_anthropic(context: str):
    system_prompt, user_prompt = get_few_shot_prompt(context)
    message = client_anthropic.messages.create(
        model="claude-3-haiku-20240229",
        max_tokens=2000,
        temperature=0.0,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )
    return message.content

def generate_financial_analysis_commercial(context: str):
    if config.MODEL == "gpt-3.5-turbo":
        return generate_financial_analysis_openai(context)
    elif config.MODEL == "claude-3-haiku":
        return generate_financial_analysis_anthropic(context)
    else:
        return
    

def generate_financial_analysis(context: str):
    """
    Generate financial analysis using the LLM model.

    Args:
        context (str): The context to use for the financial analysis.

    Returns:
        dict: The generated financial analysis.
    """
    if config.MODEL in COMMERCIAL_MODELS:
        return generate_financial_analysis_commercial(context)
    else:
        return generate_financial_analysis_ollama(context)
    
