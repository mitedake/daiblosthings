# lua2csv.py

A Python script to convert Lua table files to CSV and tab-separated TXT formats.

## Installation

1. Ensure Python 3.x is installed.
2. Install the required module:
   ```
   pip install slpp
   ```

### Folder Structure

The script expects the following folder structure in the working directory:

- `lua/`: Contains the input Lua files (e.g., `cfgCardData.lua.txt`)
- `format/`: Contains the header CSV files (e.g., `cfgCardData.csv`)
- `output/`: Where the output files will be written

### Processing Details

For each specified base name (e.g., `cfgCardData`):

1. Reads the Lua table from `lua/{base}.lua.txt`
2. Reads the headers from `format/{base}.csv`
3. Parses and flattens the Lua data
4. Outputs:
   - `output/{base}_{YYYYMMDD}.csv` (comma-separated)
   - `output/{base}_{YYYYMMDD}.txt` (tab-separated)

### Examples

- Process a single file:
  ```
  python lua2csv.py -file cfgCardData
  ```

- Process multiple files:
  ```
  python lua2csv.py -file cfgCardData cfgCfgSkillDesc