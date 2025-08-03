#!/usr/bin/env python3
"""
Generate backup summary for GitHub Actions
"""

import json
import os

def generate_summary():
    """Generate backup summary for GitHub Actions"""
    try:
        with open('backup_info.json', 'r') as f:
            backup_info = json.load(f)
        
        print(f'**Backup Timestamp:** {backup_info["timestamp"]}')
        print(f'**Total Papers:** {backup_info["total_papers"]}')
        print(f'**Description:** {backup_info["description"]}')
        print()
        print('### Papers by Journal')
        print('| Journal | Found | Saved | Status |')
        print('|---------|-------|-------|--------|')
        
        for journal, result in backup_info['results'].items():
            if 'error' in result:
                print(f'| {journal} | - | - | ❌ Error |')
            else:
                found = result.get('found', 0)
                saved = result.get('saved', 0)
                status = '✅ Success' if saved > 0 else '⚠️ No papers'
                print(f'| {journal} | {found} | {saved} | {status} |')
        
        print()
        print(f'🗄️ **Artifact Name:** database-backup-{os.environ.get("GITHUB_RUN_ID", "unknown")}')
        
    except Exception as e:
        print(f'❌ Error generating summary: {e}')
        return False
    
    return True

if __name__ == "__main__":
    generate_summary()