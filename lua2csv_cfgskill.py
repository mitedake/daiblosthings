import re
import csv
import json
import argparse
import datetime
import os

def extract_skill_entries(lua_data):
    """
    Extract individual skill entries from the Lua table using proper brace matching.
    """
    skills = []
    
    # Find all [id]={ patterns and extract complete entries with proper brace matching
    i = 0
    while i < len(lua_data):
        # Look for [id]={
        match = re.search(r'\[(\d+)\]\s*=\s*\{', lua_data[i:])
        if not match:
            break
            
        pos = i + match.start()
        skill_id = match.group(1)
        brace_pos = i + match.end() - 1  # Position of opening brace
        
        # Find matching closing brace
        depth = 1
        j = brace_pos + 1
        in_string = False
        escape = False
        
        while j < len(lua_data) and depth > 0:
            c = lua_data[j]
            
            if escape:
                escape = False
                j += 1
                continue
                
            if c == '\\':
                escape = True
                j += 1
                continue
                
            if c == '"' and not in_string:
                in_string = True
            elif c == '"' and in_string:
                in_string = False
            elif not in_string:
                if c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
            
            j += 1
        
        if depth == 0:
            # Extract the complete skill entry content (between braces)
            skill_content = lua_data[brace_pos+1:j-1]
            
            # Parse key-value pairs
            skill_data = {'id': skill_id}
            
            # Use regex to find all key=value pairs
            # Key can be: "key", [key], or just key
            # Value can be: string, number, boolean, or table
            
            kv_pattern = r'(\[?"([a-zA-Z_][a-zA-Z0-9_]*)"?\]|"([a-zA-Z_][a-zA-Z0-9_]*)"|([a-zA-Z_][a-zA-Z0-9_]*))\s*=\s*'
            
            for kv_match in re.finditer(kv_pattern, skill_content):
                # Determine which group captured the key
                key = kv_match.group(2) or kv_match.group(3) or kv_match.group(4)
                value_start = kv_match.end()
                
                # Extract value - find where it ends (comma at depth 0 or end of string)
                depth = 0
                in_string = False
                escape = False
                value_end = value_start
                
                for k in range(value_start, len(skill_content)):
                    c = skill_content[k]
                    
                    if escape:
                        escape = False
                        continue
                        
                    if c == '\\':
                        escape = True
                        continue
                        
                    if c == '"' and not in_string:
                        in_string = True
                    elif c == '"' and in_string:
                        in_string = False
                    elif not in_string:
                        if c in '{[':
                            depth += 1
                        elif c in '}]':
                            depth -= 1
                        elif c == ',' and depth == 0:
                            value_end = k
                            break
                else:
                    value_end = len(skill_content)
                
                value = skill_content[value_start:value_end].strip()
                
                # Parse the value
                if value.startswith('"') and value.endswith('"'):
                    # String value - unescape quotes
                    value = value[1:-1].replace('\\"', '"')
                elif value.lower() in ('true', 'false'):
                    # Boolean value
                    value = value.lower()
                elif value.startswith('{'):
                    # Table value - convert to JSON representation
                    try:
                        value = parse_lua_table(value)
                    except:
                        # If parsing fails, keep as string
                        pass
                
                skill_data[key] = value
            
            skills.append(skill_data)
            i = j
        else:
            i += 1
    
    return skills


def parse_lua_table(table_str):
    """
    Simple Lua table parser for extracting structure as JSON.
    Handles simple tables with {key=value, ...} structure.
    """
    table_str = table_str.strip()
    if not table_str.startswith('{') or not table_str.endswith('}'):
        return table_str
    
    # Remove outer braces
    content = table_str[1:-1].strip()
    
    result = {}
    
    # Extract key-value pairs
    i = 0
    while i < len(content):
        # Skip whitespace and commas
        if content[i] in ' \t\n\r,':
            i += 1
            continue
            
        # Look for key
        m = re.match(r'\[?([a-zA-Z_][a-zA-Z0-9_]*)\]?\s*=', content[i:])
        if not m:
            i += 1
            continue
            
        key = m.group(1)
        i += len(m.group(0))
        
        # Extract value
        depth = 0
        in_string = False
        value_start = i
        
        while i < len(content):
            c = content[i]
            if c == '"' and (i == 0 or content[i-1] != '\\'):
                in_string = not in_string
            elif not in_string:
                if c in '{[':
                    depth += 1
                elif c in '}]':
                    depth -= 1
                elif c == ',' and depth == 0:
                    break
            i += 1
        
        value = content[value_start:i].strip()
        
        # Try to parse value
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif re.match(r'^[0-9]', value):
            try:
                value = int(value) if '.' not in value else float(value)
            except:
                pass
        elif value in ('true', 'false'):
            value = value == 'true'
        elif value.startswith('{'):
            try:
                value = parse_lua_table(value)
            except:
                pass
        
        result[key] = value
    
    return json.dumps(result, ensure_ascii=False)


def process_cfgskill_lua_to_csv(input_file, output_file, header_file):
    """
    Convert cfgskill.lua.txt to CSV format using regex-based parsing.
    """
    
    # Read the header from the CSV file
    with open(header_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)

    # Read the Lua table from file
    with open(input_file, 'r', encoding='utf-8') as f:
        lua_data = f.read()

    # Extract skills using regex parsing
    skills = extract_skill_entries(lua_data)
    
    print(f"Extracted {len(skills)} skills from Lua file")

    rows = []
    for skill in skills:
        row = []
        for col in header:
            v = skill.get(col, '')
            
            # Format value for CSV
            if isinstance(v, bool):
                v = 'true' if v else 'false'
            elif isinstance(v, str):
                v = v.replace('"', '""')
            elif isinstance(v, dict) or isinstance(v, list):
                v = json.dumps(v, ensure_ascii=False)
            elif v is None:
                v = ''
            else:
                v = str(v)
            
            row.append(v)
        
        rows.append(row)

    # Write CSV file
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

    print(f'Wrote {len(rows)} skill entries to {output_file} and {txt_file}.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert cfgskill.lua.txt to CSV format.')
    parser.add_argument('-date', action='store_true', help='Include date (YYYYMMDD) in output filename')
    args = parser.parse_args()

    # date suffix only when requested
    date_str = f'_{datetime.datetime.now().strftime("%Y%m%d")}' if args.date else ''

    input_file = os.path.join('lua', 'cfgskill.lua.txt')
    header_file = os.path.join('format', 'cfgskill.csv')
    output_file = os.path.join('output', f'cfgskill{date_str}.csv')
    
    process_cfgskill_lua_to_csv(input_file, output_file, header_file)
