import requests
import csv
import os

import sys
current_dir = os.path.dirname(__file__)
sys.path.insert(1, current_dir + "/../")

from utils import data_management as dm
from utils import llm_inference as li
import config
import json

HYKEE_API_URL = "https://staging.hykee.tech"

def batch_format_balances(balances):
  prompts = []
  for balance in balances:
    prompt = balance.copy()
    prompt = dm.get_context_from_request(prompt)
    prompts.append(dm.balance_json_to_text(prompt))
  return prompts

current_dir = os.path.dirname(__file__)
file_path = os.path.join(current_dir, "../files/company_vats.txt")
with open(file_path) as f:
    vats = f.read()

balances = []
# for vat in vats.split("\n"):
#   print(f"Request for {vat} balance sheet...")
#   response = requests.get(f"{HYKEE_API_URL}/api/custom/generate-json-request?vatNumber={vat}")
#   if response.status_code != 400:
#     balances.append(response)

# INIZIO TMP
current_dir = os.path.dirname(__file__)
file_path = os.path.join(current_dir, "../files/example_request_with_score.json")
with open(file_path) as f:
  balances.append(json.load(f))
balances.append(balances[0])
# FINE TMP
# print(balances)
# balances = [balance.json() for balance in balances]
# balances = [balance for balance in balances if not "status" in balance.keys()]
formatted_balances = batch_format_balances(balances)

print(li.get_few_shot_prompt(formatted_balances[0], "zero_shot"))

def batch_generate(llm, formatted_balances, llm_name):
  dataset = []
  id = 0
  config.MODEL = llm
  
  for balance in formatted_balances:
    print(f"Generating financial analysis for balance {id} with model {config.MODEL}...")
    config.INFERENCE_TYPE = "zero_shot"
    config.MODELFILE = f"ollama/{config.MODEL}/{config.INFERENCE_TYPE}_modelfile"
    zero_shot_answer = li.generate_financial_analysis(balance)
    print(f"Zero-shot answer: {zero_shot_answer}")
    
    config.INFERENCE_TYPE = "few_shot_without_balance"
    config.MODELFILE = f"ollama/{config.MODEL}/{config.INFERENCE_TYPE}_modelfile"
    few_shot_answer_without_balance = li.generate_financial_analysis(balance)
    print(f"Few-shot without balance answer: {few_shot_answer_without_balance}")
    
    config.INFERENCE_TYPE = "few_shot_with_balance"
    config.MODELFILE = f"ollama/{config.MODEL}/{config.INFERENCE_TYPE}_modelfile"
    few_shot_answer_with_balance = li.generate_financial_analysis(balance)
    print(f"Few-shot with balance answer: {few_shot_answer_with_balance}")

    dataset.append({
        "id": id,
        "llm": llm_name,
        "methods": [
            {
              "name": "zero-shot",
              "prompt": li.get_few_shot_prompt(balance, "zero_shot"),
              "context": balance,
              "answer": zero_shot_answer
            },
            {
              "name": "few-shot-without-balance",
              "prompt": li.get_few_shot_prompt(balance, "few_shot_without_balance"),
              "context": balance,
              "answer": few_shot_answer_without_balance
            },
            {
              "name": "few-shot-with-balance",
              "prompt": li.get_few_shot_prompt(balance, "few_shot_with_balance"),
              "context": balance,
              "answer": few_shot_answer_with_balance
            }
        ],
        "human-score": "",
        "llm-score": ""
    })
    id += 1
  return dataset

llama_dataset = batch_generate("llama3", formatted_balances, "Meta-Llama-3-8B")

def generate_csv(dataset, csv_name="dataset.csv"):
  with open(csv_name, mode="w", newline="") as file:
    writer = csv.writer(file)
    # Scrittura dell"intestazione
    writer.writerow(["id", "llm", "method_name", "prompt", "context", "answer", "human-score", "llm-score"])

    # Scrittura delle righe
    for data in dataset:
        for method in data["methods"]:
            writer.writerow([
                data["id"],
                data["llm"],
                method["name"],
                method["prompt"],
                method["context"],
                method["answer"],
                data["human-score"],
                data["llm-score"]
            ])
            
generate_csv(llama_dataset, "llama_dataset.csv")