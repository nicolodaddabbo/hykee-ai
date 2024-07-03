import ollama
import config
import os

ACCEPTED_MODELS = ["llama3", "command-r", "gpt-3.5-turbo-0125", "claude-3-haiku-20240307"]
COMMERCIAL_MODELS = ["gpt-3.5-turbo-0125", "claude-3-haiku-20240307"]
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
        if config.MODEL == "gpt-3.5-turbo-0125":
            from openai import OpenAI
            client_openai = OpenAI(api_key=config.OPENAI_API_KEY)
        elif config.MODEL == "claude-3-haiku-20240307":
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

def get_few_shot_prompt(context, inference_type=config.INFERENCE_TYPE):
    def zero_shot_full_prompt(context):
        system_prompt = config.SYSTEM_ZERO_SHOT
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
    system_prompt = ""
    user_prompt = ""
    if inference_type == "zero_shot":
        system_prompt, user_prompt = zero_shot_full_prompt(context)
    elif inference_type == "few_shot_with_balance":
        system_prompt, user_prompt = few_shot_full_prompt(context, with_balance=True)
    elif inference_type == "few_shot_without_balance":
        system_prompt, user_prompt = few_shot_full_prompt(context, with_balance=False)
    return system_prompt, user_prompt

def generate_financial_analysis_openai(context: str):
    global client_openai
    if (client_openai is None):
        from openai import OpenAI
        client_openai = OpenAI(api_key=config.OPENAI_API_KEY)
    system_prompt, user_prompt = get_few_shot_prompt(context)
    output = client_openai.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {
                "role": "system", "content": system_prompt
            },
            {
                "role": "user", "content": user_prompt
            }
        ]
    )
    return output.choices[0].message.content

def generate_financial_analysis_anthropic(context: str):
    global client_anthropic
    if (client_anthropic is None):
        import anthropic
        client_anthropic = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    system_prompt, user_prompt = get_few_shot_prompt(context)
    message = client_anthropic.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=2000,
        temperature=0.0,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )
    return message.content[0].text

def generate_financial_analysis_commercial(context: str):
    if config.MODEL == "gpt-3.5-turbo-0125":
        return generate_financial_analysis_openai(context)
    elif config.MODEL == "claude-3-haiku-20240307":
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
        analysis = generate_financial_analysis_commercial(context)
    else:
        analysis = generate_financial_analysis_ollama(context)
    if (not isinstance(analysis, str)) and "response" in analysis.keys():
        analysis = analysis["response"]
    return analysis
