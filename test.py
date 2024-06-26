import ast

# Define the input file name
input_file = 'files/evaluation_balances.txt'

# Open the input file and read its contents
with open(input_file, 'r') as infile:
    data = infile.read()

# Parse the string content into a Python list using ast.literal_eval
strings_list = ast.literal_eval(data)

# Print the list to verify
print(len(strings_list))
