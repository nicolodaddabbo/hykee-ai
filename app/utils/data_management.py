import json
import os

REDUCED_DATA_KEYS = [
    'companyName',
    'Revenue',
    'Production value',
    'Raw Materials',
    'Services',
    'Personnel',
    'Other Operating Expenses',
    'EBITDA',
    'EBITDA %',
    'Depreciation & Amortization',
    'EBIT',
    'EBT',
    'Inventories',
    'Taxes',
    'Net Income',
    'Tangible Assets',
    'Financial Assets',
    'Intangible Assets',
    'Fixed Assets',
    'Other Current Assets',
    'Total Assets',
    'Total debts to social security institutions',
    'Total tax debts',
    'Total Liabilities',
    'Total Production Costs',
    'Total depreciation and write-downs',
    'Total interest and other financial charges',
    'Net Profit (Loss) for the Year',
    'Other Current Liabilities',
    'Net Invested Capital (NIC)',
    'Shareholders Equity',
    'Financial Liabilities',
    'Cash and Cash Equivalents',
    'Net Financial Position (NFP)',
    'Funds from Operation (FFO)',
    'Cash From Operation (CFO)',
    'Free Cash Flow from Operation (FCFO)',
    'Free Cash Flow to Equity (FCFE)',
    'Free Cash Flow (∆ Cash and Cash Equivalents)',
    'Year over Year Revenue %',
    'EBIT %',
    'Adjusted EBITDA %',
    'Adjusted EBIT %',
    'Net Income %',
    'Return on Capital Employed (ROCE) %',
    'NFP / EBITDA',
    'NFP / Adjusted EBITDA',
    'Gross Debt / Shareholders Equity',
    '1) Sales Revenues and Performance',
    '6) Costs of raw materials, subsidiary materials, and goods consumed',
    'Financial Score %',
    'Outlook',
    'HYKEE score %'
]

def standardize_voice_name(name: str) -> str:
    """
    This function standardizes a voice name by converting it from snake_case to CamelCase.

    Args:
        name (str): The voice name in snake_case format.

    Returns:
        str: The standardized voice name in CamelCase format.
    """
    new_string = ''
    is_underscore = False
    for char in name:
        if char == '_':
            is_underscore = True
        else:
            new_string += char.upper() if is_underscore else char
            is_underscore = False
    return new_string

def translate(balance_json: dict) -> dict:
    """
    This function translates the keys of the balance_json dictionary to the corresponding values in the translations.json file.

    Args:
        balance_json (dict): The dictionary containing the balance information.

    Returns:
        dict: The translated dictionary with updated keys.
    """
    current_dir = os.path.dirname(__file__)
    file_path = os.path.join(current_dir, '../files/translations.json')
    with open(file_path) as f:
        translations = json.load(f)
    translated_json = balance_json.copy()
    for voice in balance_json:
        key = voice
        if translated_json[voice] == translated_json['max_reference']:
            translated_json[voice] = 'MAX'
        if translated_json[voice] == translated_json['cash_reference']:
            translated_json[voice] = 'CASH'
        if translated_json[voice] == translated_json['pos_reference']:
            translated_json[voice] = 'POS'
        if translated_json[voice] == translated_json['neg_reference']:
            translated_json[voice] = 'NEG'
        if voice in translations:
            key = translations[voice]
        translated_json[key] = translated_json.pop(voice)
    translated_json.pop('max_reference')
    translated_json.pop('cash_reference')
    translated_json.pop('pos_reference')
    translated_json.pop('neg_reference')
    return translated_json

def balance_json_to_text(data: dict) -> str:
    """
    Converts a balance JSON object to a human-readable text format.

    Args:
        data (dict): The balance JSON object.

    Returns:
        str: The human-readable text representation of the balance data.
    """
    def format_dict(d, indent=0):
        formatted_str = ""
        for key, value in d.items():
            if isinstance(value, dict):
                formatted_str += '  ' * indent + f"{key}:\n" + format_dict(value, indent + 1)
            elif isinstance(value, list):
                formatted_str += '  ' * indent + f"{key}:\n" + format_list(value, indent + 1)
            else:
                formatted_str += '  ' * indent + f"- {key}: {value}\n"
        return formatted_str

    def format_list(lst, indent=0):
        formatted_str = ""
        for item in lst:
            if isinstance(item, dict):
                formatted_str += '  ' * indent + "- \n" + format_dict(item, indent + 1)
            else:
                formatted_str += '  ' * indent + f"- {item}\n"
        return formatted_str

    return format_dict(data)

def extract_desired_data(data: dict, desired_keys: list) -> str:
  """
  Extracts a subset of key-value pairs from a nested data structure and returns them as a JSON string.

  Args:
      data (dict): The input data structure, potentially containing nested dictionaries.
      desired_keys (list): A list of strings representing the desired keys to include in the output JSON.

  Returns:
      str: The resulting JSON string containing the extracted data.
  """

  # Initialize an empty dictionary to store the desired data
  extracted_data = {}

  # Loop through the desired keys
  for key in desired_keys:
    # Check if the key exists at the top level
    if key in data:
      extracted_data[key] = data[key]
    # If not, check for nested dictionaries using a recursive helper function
    else:
      extracted_data = combine_nested_data(data, key, extracted_data)

  # Convert the extracted data dictionary to JSON
  return extracted_data

def combine_nested_data(data: dict, target_key: str, extracted_data: dict) -> dict:
  """
  Recursive helper function to navigate nested dictionaries and extract desired data.

  Args:
      data (dict): The current level of the nested data structure.
      target_key (str): The key we're searching for within the nested structure.
      extracted_data (dict): The dictionary accumulating the extracted data.

  Returns:
      dict: The updated dictionary with extracted data from nested structures (if found).
  """

  # If data is not a dictionary, it's not relevant for nested key search
  if not isinstance(data, dict):
    return extracted_data

  # Iterate through key-value pairs in the current level
  for key, value in data.items():
    # Check for exact match or key containing the target key (e.g., "ce_Hykee__")
    if key == target_key or target_key in key:
      extracted_data[target_key] = value
      break  # Stop iterating once the target key is found
    # If not found at the current level, explore nested dictionaries recursively
    elif isinstance(value, dict):
      extracted_data = combine_nested_data(value, target_key, extracted_data)

  return extracted_data

def get_context_from_request(request: dict) -> dict:
    """
    Extracts the desired data from the request and returns it as a JSON string.

    Args:
        request (dict): The request data containing the balance and score information.

    Returns:
        dict: The extracted data in JSON format.
    """
    return translate(request)