import yaml

from pathlib import Path
import shutil

# Read YAML file
with open("../../test_vectors/transactions.yml", 'r') as stream:
    data_loaded = yaml.safe_load(stream)

output = "std::string payloads[] = \n{\n"

idx=0
for elem in data_loaded:
    payload = elem["payload"]
    builder = elem["builder"]
    output += f'// ({idx}) | {builder}\n'
    output += f'"{payload}",\n\n'
    idx += 1

output += "};"

f = open( "payloads.h", "w" )
f.write( output )
f.close()

print( "\nTest vector generated!\n")


