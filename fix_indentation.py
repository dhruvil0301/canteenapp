#!/usr/bin/env python3
"""
Script to fix indentation issues in Python files
"""

import re

def fix_indentation(filename):
    """Fix indentation issues in a Python file"""
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # Fix continuation line indentation
        if line.strip() and not line.strip().startswith('#'):
            # Check if this is a continuation line (starts with space but not enough)
            if line.startswith(' ') and len(line) - len(line.lstrip()) < 4:
                # Find the opening parenthesis or bracket in the previous line
                if i > 0:
                    prev_line = lines[i-1]
                    # Look for opening parenthesis, bracket, or brace
                    for char in ['(', '[', '{']:
                        if char in prev_line:
                            # Count spaces to the opening character
                            char_pos = prev_line.find(char)
                            indent_level = char_pos + 1
                            # Ensure minimum 4 spaces
                            indent_level = max(indent_level, 4)
                            # Fix the indentation
                            line = ' ' * indent_level + line.lstrip()
                            break
        
        fixed_lines.append(line)
    
    content = '\n'.join(fixed_lines)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed indentation in {filename}")

def main():
    """Main function"""
    fix_indentation('canteen_app.py')

if __name__ == '__main__':
    main() 