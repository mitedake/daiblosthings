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
import glob

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
    # table_data may be a dict (mapping) or a list; handle both
    if isinstance(table_data, dict):
        entries = table_data.values()
    else:
        entries = table_data

    for entry in entries:
        # skip non-dict/list entries
        if not isinstance(entry, dict):
            continue
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

def process_nested_lua_to_csv(input_file, output_file):
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

    rows = []
    for entry in table_data.values():
        parent_id = entry.get('id', '')
        ids_array = entry.get('ids', [])
        
        # Iterate through each skill in the ids array
        for skill in ids_array:
            skill_index = skill.get('index', '')
            skill_id = skill.get('id', '')
            rows.append([parent_id, skill_index, skill_id])

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'index', 'skill_id'])
        writer.writerows(rows)

    # Also output a tab-separated .txt file
    txt_file = output_file.replace('.csv', '.txt')
    with open(txt_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['id', 'index', 'skill_id'])
        writer.writerows(rows)

    print(f'Wrote {len(rows)} rows to {output_file} and {txt_file}.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert Lua table files to CSV.')
    parser.add_argument('-file', type=str, nargs='+', help='Base name(s) of the file(s) to process (e.g., cfgCardData cfgCfgSkillDesc). For each, looks for lua/{file}.lua.txt and format/{file}.csv. Use -date to include YYYYMMDD in output filename.')
    parser.add_argument('-date', action='store_true', help='Include date (YYYYMMDD) in output filename')
    args = parser.parse_args()

    # date suffix only when requested
    date_str = f'_{datetime.datetime.now().strftime("%Y%m%d")}' if args.date else ''

    if args.file:
        for base in args.file:
            input_file = os.path.join('lua', f'{base}.lua.txt')
            if base == 'cfgCfgSubTalentSkillPool':
                output_file = os.path.join('output', f'{base}{date_str}.csv')
                process_nested_lua_to_csv(input_file, output_file)
            else:
                header_file = os.path.join('format', f'{base}.csv')
                output_file = os.path.join('output', f'{base}{date_str}.csv')
                process_lua_to_csv(input_file, output_file, header_file)
    else:
        files = glob.glob(os.path.join('format', '*.csv'))
        bases = [os.path.splitext(os.path.basename(f))[0] for f in files]
        # exclude cfgskill from bulk processing
        bases = [b for b in bases if b != 'cfgskill']
        for base in bases:
            input_file = os.path.join('lua', f'{base}.lua.txt')
            if base == 'cfgCfgSubTalentSkillPool':
                output_file = os.path.join('output', f'{base}{date_str}.csv')
                process_nested_lua_to_csv(input_file, output_file)
            else:
                header_file = os.path.join('format', f'{base}.csv')
                output_file = os.path.join('output', f'{base}{date_str}.csv')
                process_lua_to_csv(input_file, output_file, header_file)