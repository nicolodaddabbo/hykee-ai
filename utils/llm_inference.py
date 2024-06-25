import ollama
import config
import os

ACCEPTED_MODELS = ["llama3", "mistral", "gpt-3.5-turbo", "claude-3-haiku"]
COMMERCIAL_MODELS = ["gpt-3.5-turbo", "claude-3-haiku"]
model = config.MODEL + "_" + config.INFERENCE_TYPE + ":latest"

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
    
def generate_financial_analysis(context: dict):
    """
    Generate financial analysis using the LLM model.

    Args:
        context (dict): The context to use for the financial analysis.

    Returns:
        dict: The generated financial analysis.
    """
    if config.MODEL in COMMERCIAL_MODELS:
        return {"message": f"Model {config.MODEL} is a commercial model. Please make sure you have the necessary permissions to use it."}
    response = ollama.generate(
        model=model,
        prompt="Esegui un'analisi del bilancio e della salute dell'azienda dato il seguente bilancio:\n" + context
    )
    return response