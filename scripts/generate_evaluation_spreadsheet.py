import requests
import csv
import os

import sys
current_dir = os.path.dirname(__file__)
sys.path.insert(1, current_dir + "/../")

from app.utils import data_management as dm
from app.utils import llm_inference as li
import app.config as config
import json
import ast

import mysql.connector
from mysql.connector import Error

def insert_data(connection, cursor, data):
    try:
        # Prepare the SQL insert query
        insert_query = """
        INSERT INTO hykee_ai_evaluation (id, llm, method_name, prompt, context, answer)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        # Execute the query with the provided data
        cursor.execute(insert_query, data)
        
        # Commit the transaction
        connection.commit()
        
        print("Data inserted successfully")

    except mysql.connector.Error as error:
        print(f"Failed to insert data into MySQL table: {error}")
        connection.rollback()

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
  file_path = os.path.join(current_dir, "../app/files/evaluation_balances.txt")
  if os.path.exists(file_path):
    with open(file_path, 'r') as infile:
        data = infile.read()
    return ast.literal_eval(data)

  current_dir = os.path.dirname(__file__)
  file_path = os.path.join(current_dir, "../app/files/company_vats.txt")
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
  file_path = os.path.join(current_dir, "../app/files/evaluation_balances.txt")
  with open(file_path, "w") as f:
    json.dump(formatted_balances, f)


def batch_generate(llm, formatted_balances, llm_name, csv_name="dataset.csv"):
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

def batch_generate_db(llm, formatted_balances, llm_name, connection, cursor, starting_id=0):
  id = starting_id
  config.MODEL = llm
  for balance in formatted_balances:
    try:
      print(f"Generating financial analysis for balance {id} with model {config.MODEL}...")
      config.INFERENCE_TYPE = "zero_shot"
      print(f"Generating {config.INFERENCE_TYPE} answer...")
      config.MODELFILE = f"ollama/{config.MODEL}/{config.INFERENCE_TYPE}_modelfile"
      zero_shot_answer = li.generate_financial_analysis(balance)
      if (not isinstance(zero_shot_answer, str)) and "response" in zero_shot_answer.keys():
        zero_shot_answer = zero_shot_answer["response"]
      print(f"Zero-shot answer: {zero_shot_answer}")
      
      config.INFERENCE_TYPE = "few_shot_without_balance"
      print(f"Generating {config.INFERENCE_TYPE} answer...")
      config.MODELFILE = f"ollama/{config.MODEL}/{config.INFERENCE_TYPE}_modelfile"
      few_shot_answer_without_balance = li.generate_financial_analysis(balance)
      if (not isinstance(zero_shot_answer, str)) and "response" in few_shot_answer_without_balance.keys():
        few_shot_answer_without_balance = few_shot_answer_without_balance["response"]
      print(f"Few-shot without balance answer: {few_shot_answer_without_balance}")
      
      config.INFERENCE_TYPE = "few_shot_with_balance"
      print(f"Generating {config.INFERENCE_TYPE} answer...")
      config.MODELFILE = f"ollama/{config.MODEL}/{config.INFERENCE_TYPE}_modelfile"
      few_shot_answer_with_balance = li.generate_financial_analysis(balance)
      if (not isinstance(zero_shot_answer, str)) and "response" in few_shot_answer_with_balance.keys():
        few_shot_answer_with_balance = few_shot_answer_with_balance["response"]
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
          ]
      }
      
      for method in data["methods"]:
        insert_data(connection, cursor, [
            data["id"],
            data["llm"],
            method["name"],
            "".join(method["prompt"]),
            method["context"],
            method["answer"]
        ])
      id += 1
    except Exception as e:
      print(f"An error occurred: {e}")
      continue

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
            
def main():
    try:
        formatted_balances = get_balances()

        # Establish a database connection
        connection = mysql.connector.connect(
            host='localhost',  # Update with your host if needed
            database='hykee_ai',  # Update with your database name
            user='root',  # Update with your username
            password='password'  # Update with your password
        )

        if connection.is_connected():
            cursor = connection.cursor()
            batch_generate_db("gpt-3.5-turbo-0125", formatted_balances[:21], "gpt-3.5-turbo-0125", connection, cursor, 0)
            
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
    
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")

if __name__ == "__main__":
    main()            

# formatted_balances = get_balances()
# batch_generate("llama3", formatted_balances[6:100], "Meta-Llama-3-8B", "llama_dataset.csv")
# generate_csv(llama_dataset, "llama_dataset.csv")
