# lua2csv.py

convert luas to readable format in csv or tsv

all files aside from halo and cfgskill use lua2csv.py

halo and cfgskill need specific script

## Installation

1. Install python 3.x
2. Install the required module:
   ```
   pip install slpp
   ```

### Folder Structure

- `lua/`: Contains the input Lua files (e.g., `cfgCardData.lua.txt`)
- `format/`: Contains the header CSV files (e.g., `cfgCardData.csv`)
- `output/`: Where the output files will be written

### Processing Details

For each specified base name (e.g., `cfgCardData`):

1. Reads the Lua table from `lua/{base}.lua.txt`
2. Reads the headers from `format/{base}.csv`
3. Parses and flattens the Lua data

### Usages

- Parse specific lua (separated by space for multiple files):
  ```
  python lua2csv.py -file cfgCardData
  ```

- Parse all luas:
  ```
  python lua2csv.py
  python lua2csv_halo.py
  python lua2csv_cfgskill.py
  ```
