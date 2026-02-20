import re
from slpp import slpp as lua

with open('lua/cfgskill.lua.txt', 'r', encoding='utf-8') as f:
    lua_data = f.read()

start = lua_data.find('=')
start = lua_data.find('{', start)
end = lua_data.rfind('}')
lua_table = lua_data[start:end+1]

# Clean up
lua_table = re.sub(r'--.*', '', lua_table)
lua_table = re.sub(r'\n', '', lua_table)
lua_table = re.sub(r',([}\]])', r'\1', lua_table)
lua_table = re.sub(r'([\[{])([0-9]+)=', r'\1"\2":', lua_table)
lua_table = re.sub(r'([\[{])([a-zA-Z_][a-zA-Z0-9_]*)=', r'\1"\2":', lua_table)

table_data = lua.decode(lua_table)

keys = []
seen = set()
for entry in table_data.values():
    for key in entry.keys():
        if key not in seen:
            seen.add(key)
            keys.append(key)

print(','.join(keys))