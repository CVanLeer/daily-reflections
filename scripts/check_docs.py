#!/usr/bin/env python3
"""
DOC:START
Tiered documentation enforcement script.

Purpose:
- Ensures every folder has foldername.md or .nodoc
- Ensures qualifying Python files have DOC:START/DOC:END headers
- Auto-creates stubs when missing (warn-only, non-blocking)
- Validates Tier 2 docs have required sections with content

Side effects:
- Creates stub markdown files for missing folder docs
- Injects header templates into qualifying Python files

Run: python scripts/check_docs.py [paths...] [--strict] [--ignore dir1,dir2]
DOC:END
"""

import os
import sys
import re
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# === CONFIGURATION ===

DEFAULT_IGNORE = {
    '.git', '__pycache__', 'venv', '.venv', 'node_modules',
    'dist', 'build', '.next', '.pytest_cache', '.mypy_cache',
    'coverage', '.coverage', '.ruff_cache', '.tox',
    '.idea', '.vscode', 'site-packages', 'migrations',
    '.egg-info', 'eggs', '.eggs', 'htmlcov'
}

ENTRY_POINT_PATTERNS = {'main.py', 'index.py', 'app.py', 'cli.py', 'run_', '__main__.py'}

IO_KEYWORDS = [
    'requests.', 'httpx.', 'urllib', 'subprocess.', 'sqlite3', 'psycopg',
    'cursor.execute', 'open(', 'pathlib.Path(', 'boto3.', 'aiohttp.',
    'sqlalchemy', 'pymongo', 'redis.', 'socket.'
]

LINE_THRESHOLD = 50
DEFAULT_REVIEW_INTERVAL = 90

MINIMAL_TEMPLATE = '''---
important: false
status: prototype
last_reviewed: {today}
review_interval_days: 90
---

This folder contains ... so that ...

## Purpose
[What this folder exists to do]

## What's inside
- [file/subfolder]: [purpose]

## How it connects
- [Dependencies and dependents]
'''

HEADER_TEMPLATE = '''"""
DOC:START
[One-sentence descriptor]

Purpose:
- [What this file does]

Inputs/Outputs:
- [If applicable]

Side effects:
- [DB writes, network calls, file writes]

Run: [How to run/test]
See: [Pointer to folder doc]
DOC:END
"""

'''

# === HELPERS ===

def parse_frontmatter(content):
    """Extract YAML frontmatter from markdown."""
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not match:
        return {}
    fm = {}
    for line in match.group(1).split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            fm[key.strip()] = val.strip()
    return fm

def has_content_under_heading(content, heading):
    """Check if heading exists and has non-empty content before next heading."""
    pattern = rf'^##\s*{re.escape(heading)}\s*\n(.*?)(?=^##|\Z)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if not match:
        return False
    body = match.group(1).strip()
    # Remove placeholder brackets
    body = re.sub(r'\[.*?\]', '', body).strip()
    return len(body) > 0

def file_qualifies(filepath, content, lines, in_important_folder):
    """Determine if a Python file needs a header."""
    name = os.path.basename(filepath)
    
    # Entry point check
    if any(name.startswith(p) if p.endswith('_') else name == p for p in ENTRY_POINT_PATTERNS):
        return True, "entry point"
    
    # Line count check
    if lines > LINE_THRESHOLD:
        return True, f">{LINE_THRESHOLD} lines"
    
    # IO keyword check
    for kw in IO_KEYWORDS:
        if kw in content:
            return True, f"contains '{kw}'"
    
    # Important folder check
    if in_important_folder:
        return True, "in important folder"
    
    return False, None

def find_insertion_point(content):
    """Find where to insert DOC block in Python file."""
    lines = content.split('\n')
    insert_after = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Skip shebang
        if i == 0 and stripped.startswith('#!'):
            insert_after = i + 1
            continue
        # Skip encoding
        if stripped.startswith('# -*-') or stripped.startswith('# coding'):
            insert_after = i + 1
            continue
        # Skip __future__ imports
        if stripped.startswith('from __future__'):
            insert_after = i + 1
            continue
        # Skip existing module docstring
        if stripped.startswith('"""') or stripped.startswith("'''"):
            # Find end of docstring
            quote = stripped[:3]
            if stripped.count(quote) >= 2 and len(stripped) > 6:
                # Single-line docstring
                insert_after = i + 1
            else:
                # Multi-line docstring
                for j in range(i + 1, len(lines)):
                    if quote in lines[j]:
                        insert_after = j + 1
                        break
            break
        # Stop at first real code
        if stripped and not stripped.startswith('#'):
            break
    
    return insert_after

# === MAIN SCAN LOGIC ===

def scan_folders(root, ignore_set, paths_filter=None):
    """Scan folders for missing/stale docs."""
    warnings = []
    
    for dirpath, dirnames, filenames in os.walk(root):
        # Filter ignored directories
        dirnames[:] = [d for d in dirnames if d not in ignore_set]
        
        # Skip if paths filter and not in scope
        if paths_filter and not any(dirpath.startswith(p) or p.startswith(dirpath) for p in paths_filter):
            continue
        
        rel_path = os.path.relpath(dirpath, root)
        if rel_path == '.':
            continue
        
        folder_name = os.path.basename(dirpath)
        
        # Check for skip markers
        if '.nodoc' in filenames or '.generated' in filenames:
            continue
        
        doc_name = f"{folder_name}.md"
        doc_path = os.path.join(dirpath, doc_name)
        
        if doc_name not in filenames:
            # Create stub
            today = datetime.now().strftime('%Y-%m-%d')
            stub = MINIMAL_TEMPLATE.format(today=today)
            with open(doc_path, 'w') as f:
                f.write(stub)
            warnings.append(f"Created stub: {rel_path}/{doc_name}")
        else:
            # Validate existing doc
            with open(doc_path, 'r') as f:
                content = f.read()
            
            fm = parse_frontmatter(content)
            
            # Check staleness
            if 'last_reviewed' in fm:
                try:
                    last = datetime.strptime(fm['last_reviewed'], '%Y-%m-%d')
                    interval = int(fm.get('review_interval_days', DEFAULT_REVIEW_INTERVAL))
                    if datetime.now() - last > timedelta(days=interval):
                        warnings.append(f"Stale doc (>{interval} days): {rel_path}/{doc_name}")
                except ValueError:
                    warnings.append(f"Invalid last_reviewed date: {rel_path}/{doc_name}")
            else:
                warnings.append(f"Missing last_reviewed: {rel_path}/{doc_name}")
            
            # Check Tier 2 if important
            if fm.get('important', '').lower() == 'true':
                required = ['Purpose', "What's inside", 'How it connects', 'Key workflows', 'Verification']
                for heading in required:
                    if not has_content_under_heading(content, heading):
                        warnings.append(f"Tier 2 missing/empty '{heading}': {rel_path}/{doc_name}")
    
    return warnings

def scan_files(root, ignore_set, important_folders, paths_filter=None):
    """Scan Python files for missing headers."""
    warnings = []
    
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ignore_set]
        
        rel_dir = os.path.relpath(dirpath, root)
        in_important = rel_dir in important_folders or any(rel_dir.startswith(f + os.sep) for f in important_folders)
        
        for fname in filenames:
            if not fname.endswith('.py'):
                continue
            
            filepath = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(filepath, root)
            
            # Skip if paths filter and not in scope
            if paths_filter and not any(rel_path.startswith(p) for p in paths_filter):
                continue
            
            with open(filepath, 'r') as f:
                content = f.read()
            
            lines = content.count('\n') + 1
            
            # Check for opt-out
            first_20 = '\n'.join(content.split('\n')[:20])
            if '@nodoc' in first_20 or 'NODOC' in first_20:
                continue
            
            # Check if already has DOC block
            if 'DOC:START' in content:
                continue
            
            # Check if qualifies
            qualifies, reason = file_qualifies(filepath, content, lines, in_important)
            if not qualifies:
                continue
            
            # Inject header
            insert_at = find_insertion_point(content)
            lines_list = content.split('\n')
            new_content = '\n'.join(lines_list[:insert_at]) + '\n' + HEADER_TEMPLATE + '\n'.join(lines_list[insert_at:])
            
            with open(filepath, 'w') as f:
                f.write(new_content)
            
            warnings.append(f"Injected header ({reason}): {rel_path}")
    
    return warnings

def get_important_folders(root, ignore_set):
    """Find folders marked as important in their docs."""
    important = set()
    
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ignore_set]
        
        folder_name = os.path.basename(dirpath)
        doc_name = f"{folder_name}.md"
        
        if doc_name in filenames:
            doc_path = os.path.join(dirpath, doc_name)
            with open(doc_path, 'r') as f:
                content = f.read()
            fm = parse_frontmatter(content)
            if fm.get('important', '').lower() == 'true':
                important.add(os.path.relpath(dirpath, root))
    
    return important

# === CLI ===

def main():
    parser = argparse.ArgumentParser(description='Check and enforce documentation standards')
    parser.add_argument('paths', nargs='*', help='Specific paths to check (default: full scan)')
    parser.add_argument('--strict', action='store_true', help='Exit 1 if any warnings')
    parser.add_argument('--ignore', type=str, help='Comma-separated additional dirs to ignore')
    parser.add_argument('--ext', type=str, default='py', help='File extensions to check (future: py,js,ts)')
    args = parser.parse_args()
    
    root = os.getcwd()
    ignore_set = DEFAULT_IGNORE.copy()
    
    if args.ignore:
        ignore_set.update(args.ignore.split(','))
    
    paths_filter = args.paths if args.paths else None
    
    print("=== Documentation Check ===\n")
    
    # First pass: scan folders
    folder_warnings = scan_folders(root, ignore_set, paths_filter)
    
    # Get important folders (after stubs created)
    important_folders = get_important_folders(root, ignore_set)
    
    # Second pass: scan files
    file_warnings = scan_files(root, ignore_set, important_folders, paths_filter)
    
    all_warnings = folder_warnings + file_warnings
    
    if all_warnings:
        print("Warnings:")
        for w in all_warnings:
            print(f"  ⚠️  {w}")
        print(f"\nTotal: {len(all_warnings)} warnings")
    else:
        print("✅ All docs in order.")
    
    if args.strict and all_warnings:
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    main()
