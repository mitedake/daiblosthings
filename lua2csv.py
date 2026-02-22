import re
import json
import csv
from slpp import slpp as lua
import string
from collections.abc import Mapping, Sequence
import argparse
import datetime
import os
import glob

def clean_string(s):
    if isinstance(s, str):
        s = re.sub(r'<color=#[0-9A-Fa-f]{6}>', '', s)
        s = s.replace('</color>', '')
        return s
    return s

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
            val = clean_string(val)
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

    # Sort rows by id (first column)
    rows.sort(key=lambda x: int(x[0]) if x[0].isdigit() else 0)

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

def process_nested_array_lua_to_csv(input_file, output_file, headers, array_key, parent_fields, child_fields):
    """
    Generic flattener for Lua tables whose entries each contain a nested array.

    headers       - output column names, e.g. ['id', 'index', 'skill_id']
    array_key     - key of the nested list inside each entry, e.g. 'ids' or 'arr'
    parent_fields - lua keys to pull from the parent entry (in order), e.g. ['id']
    child_fields  - lua keys to pull from each child item (in order), e.g. ['index', 'id']

    The combined length of parent_fields + child_fields must equal len(headers).
    """
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
        if not isinstance(entry, dict):
            continue
        parent_vals = [clean_string(str(entry.get(f, ''))) for f in parent_fields]
        arr = entry.get(array_key, [])
        if isinstance(arr, dict):
            arr = list(arr.values())
        for item in arr:
            if not isinstance(item, dict):
                continue
            child_vals = [clean_string(str(item.get(f, ''))) for f in child_fields]
            rows.append(parent_vals + child_vals)

    rows.sort(key=lambda x: int(x[0]) if x[0].lstrip('-').isdigit() else 0)

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    txt_file = output_file.replace('.csv', '.txt')
    with open(txt_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(headers)
        writer.writerows(rows)

    print(f'Wrote {len(rows)} rows to {output_file} and {txt_file}.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert Lua table files to CSV.')
    parser.add_argument('-file', type=str, nargs='+', help='Base name(s) of the file(s) to process (e.g., cfgCardData cfgCfgSkillDesc). For each, looks for lua/{file}.lua.txt and format/{file}.csv. Use -date to include YYYYMMDD in output filename.')
    parser.add_argument('-date', action='store_true', help='Include date (YYYYMMDD) in output filename')
    args = parser.parse_args()

    # date suffix only when requested
    date_str = f'_{datetime.datetime.now().strftime("%Y%m%d")}' if args.date else ''

    # Bases that use the generic nested-array flattener.
    # Each value: (array_key, parent_fields, child_fields, headers)
    NESTED_CONFIGS = {
        'cfgCfgSubTalentSkillPool':  ('ids', ['id'],        ['index', 'id'],              ['id', 'index', 'skill_id']),
        'cfgCfgCardRoleAbilityPool': ('arr', ['id','icon'], ['index', 'remarks', 'desc'], ['id', 'icon','index', 'remarks', 'desc']),
    }

    if args.file:
        for base in args.file:
            input_file = os.path.join('lua', f'{base}.lua.txt')
            output_file = os.path.join('output', f'{base}{date_str}.csv')
            if base in NESTED_CONFIGS:
                array_key, parent_fields, child_fields, headers = NESTED_CONFIGS[base]
                process_nested_array_lua_to_csv(input_file, output_file, headers, array_key, parent_fields, child_fields)
            else:
                header_file = os.path.join('format', f'{base}.csv')
                process_lua_to_csv(input_file, output_file, header_file)
    else:
        # Nested configs don't need a format CSV; add them explicitly
        nested_bases = list(NESTED_CONFIGS.keys())
        # Flat configs are discovered from format/*.csv (excluding cfgskill and nested bases)
        files = glob.glob(os.path.join('format', '*.csv'))
        flat_bases = [os.path.splitext(os.path.basename(f))[0] for f in files]
        SKIP_BASES = {'cfgskill', 'cfgcfgHalo'}
        flat_bases = [b for b in flat_bases if b not in SKIP_BASES and b not in NESTED_CONFIGS]
        for base in nested_bases + flat_bases:
            input_file = os.path.join('lua', f'{base}.lua.txt')
            output_file = os.path.join('output', f'{base}{date_str}.csv')
            if base in NESTED_CONFIGS:
                array_key, parent_fields, child_fields, headers = NESTED_CONFIGS[base]
                process_nested_array_lua_to_csv(input_file, output_file, headers, array_key, parent_fields, child_fields)
            else:
                header_file = os.path.join('format', f'{base}.csv')
                process_lua_to_csv(input_file, output_file, header_file)

