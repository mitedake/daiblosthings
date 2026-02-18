import re
import json
import csv
from slpp import slpp as lua
import unicodedata
import string
from collections.abc import Mapping, Sequence
import argparse
import datetime
import os
import sys

def process_lua_to_csv(input_file, output_file, header_file):
    # Read the header from the CSV file
    with open(header_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)

    # Read the Lua table from file
    with open(input_file, 'r', encoding='utf-8') as f:
        lua_data = f.read()

    # Extract the table (find the first { after =, and the last })
    start = lua_data.find('=')
    if start == -1:
        raise Exception('Could not find = in file')
    start = lua_data.find('{', start)
    end = lua_data.rfind('}')
    if start == -1 or end == -1:
        raise Exception('Could not find table braces')
    lua_table = lua_data[start:end+1]

    # Replace common full-width punctuation with ASCII equivalents
    fw_map = {
        '：': ':', '，': ',', '？': '?', '！': '!', '（': '(', '）': ')',
        '［': '[', '］': ']', '｛': '{', '｝': '}', '“': '"', '”': '"',
        '‘': "'", '’': "'", '…': '...', '—': '-', '–': '-', '、': ',',
        '。': '.', '《': '"', '》': '"', '〈': '"', '〉': '"', '·': '.',
        '「': '"', '」': '"', '『': '"', '』': '"', '【': '[', '】': ']',
        '％': '%', '＃': '#', '＆': '&', '＊': '*', '／': '/', '＼': '\\',
        '＂': '"', '＇': "'", '＄': '$', '＠': '@', '＾': '^', '＿': '_',
        '＋': '+', '＝': '=', '｜': '|', '；': ';', '：': ':', '，': ',',
        '　': ' ',  # full-width space
    }
    for k, v in fw_map.items():
        lua_table = lua_table.replace(k, v)
    lua_table = ''.join(c if c in string.printable or ord(c) >= 128 and c not in '\r\n\t' else ' ' for c in lua_table)
    lua_table = lua_table.replace('true', 'True').replace('false', 'False')
    lua_table = re.sub(r'\["([a-zA-Z0-9_]+)"\]', r'"\1"', lua_table)  # ["key"] to "key"
    lua_table = re.sub(r'--.*', '', lua_table)  # Remove comments
    lua_table = re.sub(r'\n', '', lua_table)  # Remove newlines
    lua_table = re.sub(r',([}\]])', r'\1', lua_table)  # Remove trailing commas
    lua_table = re.sub(r'([\[{])([0-9]+)=', r'\1"\2":', lua_table)  # [123]= to "123":
    lua_table = re.sub(r'([\[{])([a-zA-Z_][a-zA-Z0-9_]*)=', r'\1"\2":', lua_table)  # key= to "key":

    # Convert Lua tables to Python dicts/lists using slpp
    try:
        table_data = lua.decode(lua_table)
    except Exception as e:
        raise Exception('Failed to parse Lua table with slpp: ' + str(e))

    def flatten_value(val):
        if isinstance(val, bool):
            return 'true' if val else 'false'
        elif isinstance(val, str):
            return val.replace('"', '""')
        elif isinstance(val, Mapping):
            return json.dumps(val, ensure_ascii=False)
        elif isinstance(val, Sequence) and not isinstance(val, str):
            return ';'.join(str(flatten_value(v)) for v in val)
        elif val is None:
            return ''
        else:
            return str(val)

    rows = []
    for entry in table_data.values():
        row = []
        for col in header:
            v = entry.get(col, '')
            row.append(flatten_value(v))
        rows.append(row)

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    # Also output a tab-separated .txt file
    txt_file = output_file.replace('.csv', '.txt')
    with open(txt_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(header)
        writer.writerows(rows)

    print(f'Wrote {len(rows)} rows to {output_file} and {txt_file}.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert Lua table files to CSV.')
    parser.add_argument('-file', type=str, nargs='+', help='Base name(s) of the file(s) to process (e.g., cfgCardData cfgCfgSkillDesc). For each, looks for lua/{file}.lua.txt, format/{file}.csv, outputs to output/{file}_{datetime}.csv')
    args = parser.parse_args()

    if args.file:
        for base in args.file:
            input_file = os.path.join('lua', f'{base}.lua.txt')
            header_file = os.path.join('format', f'{base}.csv')
            date_str = datetime.datetime.now().strftime('%Y%m%d')
            output_file = os.path.join('output', f'{base}_{date_str}.csv')
            process_lua_to_csv(input_file, output_file, header_file)
    else:
        # Require -file argument
        print("Error: Please specify a file using the -file argument.")
        sys.exit(1)