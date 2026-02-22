import re
from slpp import slpp as lua
import csv

def extract_halo_data(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
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

    rows = []
    for entry in table_data.values():
        if isinstance(entry, dict) and 'id' in entry and 'percents' in entry:
            id_val = entry['id']
            percents = entry['percents']
            # Flatten percents: alternating key and value
            flat = []
            for k, v in percents.items():
                flat.extend([k, v])
            # Pad to 4 if less
            while len(flat) < 4:
                flat.append('')
            row = [id_val] + flat[:4]
            rows.append(row)

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'effect1', 'percent1', 'effect2', 'percent2'])
        writer.writerows(rows)

    # Also output a tab-separated .txt file
    txt_file = output_file.replace('.csv', '.txt')
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write('\t'.join(['id', 'effect1', 'percent1', 'effect2', 'percent2']) + '\n')
        for row in rows:
            f.write('\t'.join(str(cell) for cell in row) + '\n')
    
    print(f'Wrote {len(rows)} skill entries to {output_file} and {txt_file}.')

if __name__ == '__main__':
    extract_halo_data('lua/cfgcfgHalo.lua.txt', 'output/cfgcfgHalo.csv')