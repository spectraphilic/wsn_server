import re
import unicodedata

def clean_column_name(name: str) -> str:
    """
    Convert a string into a valid, unquoted SQL identifier (e.g., for ClickHouse).
    
    Examples:
        "H2O dry(mmol/mol)" → "h2o_dry_mmol_mol"
        "Temp. (°C)"         → "temp_c"
        "1st col!"           → "_1st_col"
        "  ?!  "             → "_"
    
    Args:
        name: Original column name (may contain spaces, symbols, etc.)
    
    Returns:
        A normalized, lowercase snake_case identifier safe for SQL without quotes.
    """
    if not isinstance(name, str):
        name = str(name)

    # Normalize unicode (e.g., é → e, ° → degree symbol handling)
    name = unicodedata.normalize('NFKD', name)
    
    # Replace known problematic characters with semantic equivalents (optional but helpful)
    replacements = {
        '°': 'deg',
        '%': 'pct',
        '#': 'num',
        '&': 'and',
        '@': 'at',
        '+': 'plus',
        '-': '_',
        '.': '_',
    }
    for old, new in replacements.items():
        name = name.replace(old, new)

    # Replace any non-alphanumeric (except space/underscore) with space
    name = re.sub(r'[^a-zA-Z0-9_ ]', ' ', name)

    # Replace whitespace and underscores with single underscores
    name = re.sub(r'[\s_]+', '_', name)

    # Strip leading/trailing underscores
    name = name.strip('_')

    # Ensure it starts with a letter or underscore (SQL identifiers can't start with digit)
    if not name:
        return "_"
    if name[0].isdigit():
        name = "_" + name

    return name
