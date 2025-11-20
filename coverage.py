import pandas as pd
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

#todo the template file after the main.py and bank_patterns.py output
template_dir = "/Users/chandan/Documents/VS Code/merged_sms_temps/debud temp"
#todo the truth data of banks
messages_file = "/Users/chandan/Documents/VS Code/merged_sms_temps/45 bank data.xlsx"

#todo this will be made on its own
summary_file = "/Users/chandan/Documents/VS Code/merged_sms_temps/coverage_summary.txt"
uncovered_file = "/Users/chandan/Documents/VS Code/merged_sms_temps/uncovered_messages.xlsx"

def normalize(text, is_template=False):
    # Basic cleanup: lower case, strip
    text = str(text).lower().strip()
    # Normalize whitespace to single space
    text = re.sub(r'\s+', ' ', text)
    
    if is_template:
        # Convert template to regex pattern
        # Split by placeholders <...>
        parts = re.split(r'(<.*?>)', text)
        pattern = ""
        for part in parts:
            if part.startswith('<') and part.endswith('>'):
                # It's a placeholder, match any sequence of characters (non-greedy)
                pattern += r'.*?'
            else:
                # It's literal text, escape it
                escaped = re.escape(part)
                # Allow flexible whitespace in literal text
                # Handle both escaped space '\ ' and literal space ' '
                # Use \s* to allow zero or more spaces (e.g. "rs. 100" matches "rs.100")
                escaped = escaped.replace(r'\ ', r'\s*')
                escaped = escaped.replace(' ', r'\s*')
                pattern += escaped
        # Anchor the pattern to match the whole string
        return f"^{pattern}$"
    else:
        # For messages, just return the cleaned text
        return text

messages_df = pd.read_excel(messages_file)
if 'casa_sender_name' in messages_df.columns:
    messages_df['casa_sender_name'] = messages_df['casa_sender_name'].str.upper().str.strip()

templates = {}
print("Loading and compiling templates...")
for file in os.listdir(template_dir):
    if file.endswith(".xlsx"):
        bank_name = file.replace(".xlsx", "").upper().replace("_", " ").strip()
        try:
            df = pd.read_excel(os.path.join(template_dir, file))
            df.columns = df.columns.str.strip()
            
            raw_templates = []
            if 'template' in df.columns:
                raw_templates = df['template'].tolist()
            else:
                cols = list(df.columns)
                raw_templates = cols if cols else []
            
            # Compile templates to regex objects
            compiled_templates = []
            for t in raw_templates:
                if pd.isna(t): continue
                pattern_str = normalize(t, is_template=True)
                try:
                    compiled_templates.append(re.compile(pattern_str))
                except re.error as e:
                    print(f"Error compiling regex for template '{t}': {e}")
            
            templates[bank_name] = compiled_templates
            
        except Exception as e:
            print(f"Error loading templates for {bank_name}: {e}")

def is_covered(message, templates_list):
    norm_msg = normalize(message, is_template=False)
    for tmpl_pattern in templates_list:
        # tmpl_pattern is already a compiled regex object
        if tmpl_pattern.fullmatch(norm_msg):
            return True
    return False

def check_row(row):
    bank = row.get('casa_sender_name')
    if bank in templates:
        return is_covered(row['message'], templates[bank])
    return False

if 'Message' in messages_df.columns:
    messages_df = messages_df.rename(columns={'Message':'message'})

rows = messages_df.to_dict('records')
results = [None] * len(rows)

print("Checking coverage...")
with ThreadPoolExecutor(max_workers=8) as ex:
    futures = {ex.submit(check_row, rows[i]): i for i in range(len(rows))}
    for fut in tqdm(as_completed(futures), total=len(rows)):
        idx = futures[fut]
        try:
            results[idx] = fut.result()
        except Exception as e:
            print(f"Error processing row {idx}: {e}")
            results[idx] = False

messages_df['covered'] = results

coverage_summary = messages_df.groupby('casa_sender_name')['covered'].agg(
    total='count',
    covered='sum'
)
coverage_summary['coverage_pct'] = 100 * coverage_summary['covered'] / coverage_summary['total']

with open(summary_file, 'w', encoding='utf-8') as f:
    f.write("=== coverage summary ===\n")
    f.write(coverage_summary.to_string())

uncovered_messages = messages_df[~messages_df['covered']]
uncovered_messages.to_excel(uncovered_file, index=False)
print("Done.")
