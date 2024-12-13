from req_agent import *
from coder_agent import *
from debugger_agent import *

query = input("Enter your query: ")
file = web_search(query)
with open(file, 'r') as f:
    data = json.load(f)
last_entry = data[-1]
last_entry = json.dumps(last_entry, indent=4)  # Pretty string format
print("-"*100)
code = coder(last_entry)
print("-"*100)
debug = debugger(code)
print(debug)