# lua2csv.py

A Python script to convert Lua table files to CSV and tab-separated TXT formats.

## Requirements

- Python 3.x
- Required Python modules:
  - `slpp` (install via `pip install slpp`)
  - Standard library modules: `re`, `json`, `csv`, `unicodedata`, `string`, `collections.abc`, `argparse`, `datetime`, `os`, `sys`

## Installation

1. Ensure Python 3.x is installed.
2. Install the required module:
   ```
   pip install slpp
   ```

## Usage

The script processes Lua table files and converts them to CSV (comma-separated) and TXT (tab-separated) formats.

### Command Line Arguments

- `-file <base_name> [base_name2 ...]`: Specify one or more base names of files to process. Required.

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
  ```

- If no `-file` is provided, the script will display an error and exit.

### Output

- CSV files: Standard comma-separated values with headers.
- TXT files: Tab-separated values (TSV) with the same data, useful for applications that prefer tab delimiters.

### Notes

- The script handles full-width punctuation conversion and Lua syntax adjustments for parsing.
- Ensure input files exist in the correct folders before running.
- Output files include the current date in the filename to avoid overwrites.