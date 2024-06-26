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
import ast

HYKEE_API_URL = "https://staging.hykee.tech"

def batch_format_balances(balances):
  prompts = []
  for balance in balances:
    prompt = balance.copy()
    prompt = dm.get_context_from_request(prompt)
    prompts.append(dm.balance_json_to_text(prompt))
  return prompts

def get_balances():
  current_dir = os.path.dirname(__file__)
  file_path = os.path.join(current_dir, "../files/evaluation_balances.txt")
  if os.path.exists(file_path):
    input_file = 'files/evaluation_balances.txt'
    with open(input_file, 'r') as infile:
        data = infile.read()
    return ast.literal_eval(data)

  current_dir = os.path.dirname(__file__)
  file_path = os.path.join(current_dir, "../files/company_vats.txt")
  with open(file_path) as f:
      vats = f.read()

  balances = []
  for vat in vats.split("\n"):
    print(f"Request for {vat} balance sheet...")
    response = requests.get(f"{HYKEE_API_URL}/api/custom/generate-json-request?vatNumber={vat}")
    if response.status_code != 400:
      balances.append(response)

  # INIZIO TMP
  # current_dir = os.path.dirname(__file__)
  # file_path = os.path.join(current_dir, "../files/example_request_with_score.json")
  # with open(file_path) as f:
  #   balances.append(json.load(f))
  # balances.append(balances[0])
  # FINE TMP
  # print(balances)
  balances = [balance.json() for balance in balances]
  balances = [balance for balance in balances if not "status" in balance.keys()]
  formatted_balances = batch_format_balances(balances)

  current_dir = os.path.dirname(__file__)
  file_path = os.path.join(current_dir, "../files/evaluation_balances.txt")
  with open(file_path, "w") as f:
    json.dump(formatted_balances, f)


def batch_generate(llm, formatted_balances, llm_name, csv_name="dataset.csv"):
  dataset = []
  id = 0
  config.MODEL = llm
  with open(csv_name, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["id", "llm", "method_name", "prompt", "context", "answer", "human-score", "llm-score"])
    
    for balance in formatted_balances:
      print(f"Generating financial analysis for balance {id} with model {config.MODEL}...")
      config.INFERENCE_TYPE = "zero_shot"
      print(f"Generating {config.INFERENCE_TYPE} answer...")
      config.MODELFILE = f"ollama/{config.MODEL}/{config.INFERENCE_TYPE}_modelfile"
      zero_shot_answer = li.generate_financial_analysis(balance)["response"]
      print(f"Zero-shot answer: {zero_shot_answer}")
      
      config.INFERENCE_TYPE = "few_shot_without_balance"
      print(f"Generating {config.INFERENCE_TYPE} answer...")
      config.MODELFILE = f"ollama/{config.MODEL}/{config.INFERENCE_TYPE}_modelfile"
      few_shot_answer_without_balance = li.generate_financial_analysis(balance)["response"]
      print(f"Few-shot without balance answer: {few_shot_answer_without_balance}")
      
      config.INFERENCE_TYPE = "few_shot_with_balance"
      print(f"Generating {config.INFERENCE_TYPE} answer...")
      config.MODELFILE = f"ollama/{config.MODEL}/{config.INFERENCE_TYPE}_modelfile"
      few_shot_answer_with_balance = li.generate_financial_analysis(balance)["response"]
      print(f"Few-shot with balance answer: {few_shot_answer_with_balance}")

      data = {
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
      }
      dataset.append(data)
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
      id += 1
  return dataset

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
            
formatted_balances = get_balances()
llama_dataset = batch_generate("llama3", formatted_balances[:100], "Meta-Llama-3-8B", "llama_dataset.csv")
#generate_csv(llama_dataset, "llama_dataset.csv")