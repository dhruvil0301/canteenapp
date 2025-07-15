#!/usr/bin/env python3
"""
Script to fix common linter errors in Python files
"""

import re
import os

def fix_python_file(filename):
    """Fix common linter errors in a Python file"""
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix trailing whitespace
    content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)
    
    # Fix blank lines with whitespace
    content = re.sub(r'^[ \t]+$', '', content, flags=re.MULTILINE)
    
    # Fix missing blank lines between functions/classes
    # Add 2 blank lines before function/class definitions
    content = re.sub(r'(\n)(def |class )', r'\1\n\2', content)
    
    # Add 2 blank lines after class/function definitions
    content = re.sub(r'(\n)(\n)(def |class )', r'\1\n\2', content)
    
    # Fix indentation issues in multi-line statements
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # Fix continuation line indentation
        if line.strip().startswith('if ') and ':' in line:
            # Check next lines for proper indentation
            j = i + 1
            while j < len(lines) and lines[j].strip() and lines[j].startswith(' '):
                if len(lines[j]) - len(lines[j].lstrip()) < 4:
                    # Fix indentation
                    indent = ' ' * 4
                    lines[j] = indent + lines[j].lstrip()
                j += 1
        
        fixed_lines.append(line)
    
    content = '\n'.join(fixed_lines)
    
    # Ensure file ends with newline
    if not content.endswith('\n'):
        content += '\n'
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed linter errors in {filename}")

def main():
    """Main function to fix all Python files"""
    python_files = [
        'canteen_app.py',
        'email_config.py',
        'setup_auth.py',
        'test_email.py'
    ]
    
    for filename in python_files:
        if os.path.exists(filename):
            fix_python_file(filename)
        else:
            print(f"File {filename} not found")

if __name__ == '__main__':
    main() 