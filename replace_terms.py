import os

def replace_in_file(filepath, replacements):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        modified = False
        for old, new in replacements.items():
            if old in content:
                content = content.replace(old, new)
                modified = True
                
        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'Modified {filepath}')
    except Exception as e:
        print(f'Error processing {filepath}: {e}')

replacements = {
    'PETROLQ PLATFORM': 'PETROLQ PLATFORM',
    'PetrolQ Autonomous AI': 'PetrolQ Autonomous AI',
    'Official PetrolQ Decision Support Document.': 'Official PetrolQ Decision Support Document.',
    'PETROLQ': 'PETROLQ',
    'PetrolQ decision suite': 'PetrolQ decision suite',
    'title PetrolQ Launcher': 'title PetrolQ Launcher',
    'Starting PetrolQ': 'Starting PetrolQ',
    'getLogger("PetrolQ")': 'getLogger("PetrolQ")',
    'Setting up PetrolQ': 'Setting up PetrolQ',
    'PetrolQ - SIH 2026 Solution': 'PetrolQ - SIH 2026 Solution',
    '# PetrolQ (Nearby Wells Intelligence System)': '# PetrolQ (Nearby Wells Intelligence System)',
    'PetrolQ Nearby Wells Intelligence System': 'PetrolQ Nearby Wells Intelligence System',
    'PetrolQ <span': 'PetrolQ <span',
    'title="PetrolQ API"': 'title="PetrolQ API"',
    'PETROLQ-DOSSIER-2026': 'PETROLQ-DOSSIER-2026',
    'PETROLQ-DOSSIER-': 'PETROLQ-DOSSIER-',
    '': '',
    'PetrolQ': 'PetrolQ'
}

for root, _, files in os.walk('.'):
    if 'node_modules' in root or '.git' in root or 'venv' in root or 'fresh_venv' in root or '.gemini' in root or '__pycache__' in root:
        continue
    for file in files:
        if file.endswith(('.js', '.jsx', '.py', '.json', '.md', '.bat', '.txt')):
            replace_in_file(os.path.join(root, file), replacements)
