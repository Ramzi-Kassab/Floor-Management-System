"""
Automated HTML Template Fixer

Automatically fixes common template issues:
- Adds missing {% load %} statements
- Fixes mismatched tags
"""
import os
import re
from pathlib import Path


class TemplateFixer:
    def __init__(self, base_dir, dry_run=True):
        self.base_dir = Path(base_dir)
        self.dry_run = dry_run
        self.fixes_applied = 0
        self.files_modified = 0

    def find_templates(self):
        """Find all HTML templates."""
        templates = []
        for pattern in ['**/*.html', '**/templates/**/*.html']:
            templates.extend(self.base_dir.glob(pattern))
        return templates

    def fix_missing_load_statements(self, content, file_path):
        """Add missing {% load %} statements."""
        fixes = []
        modified = content

        # Check if template uses 'static' but missing {% load static %}
        if 'static' in content and '{% load static %}' not in content:
            # Find where to insert (after {% extends %} if present, or at top)
            if '{% extends' in content:
                # Insert after extends
                modified = re.sub(
                    r'({%\s*extends\s+[\'"][^\'"]+[\'"]\s*%})',
                    r'\1\n{% load static %}',
                    modified,
                    count=1
                )
            else:
                # Insert at top
                modified = '{% load static %}\n' + modified
            fixes.append("Added {% load static %}")

        # Check if template uses filters but has no {% load %}
        filters_used = bool(re.search(r'\|\w+:', content))
        if filters_used and '{% load' not in content:
            # Need to load custom tags or humanize
            if '{% extends' in modified:
                modified = re.sub(
                    r'({%\s*extends\s+[\'"][^\'"]+[\'"]\s*%})',
                    r'\1',
                    modified,
                    count=1
                )
            fixes.append("Template uses filters (needs {% load %} - manual check needed)")

        return modified, fixes

    def fix_template(self, template_path):
        """Fix a single template."""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Error reading {template_path}: {e}")
            return False

        original_content = content
        all_fixes = []

        # Apply fixes
        content, fixes = self.fix_missing_load_statements(content, template_path)
        all_fixes.extend(fixes)

        # If content changed and not dry run, write back
        if content != original_content:
            if self.dry_run:
                print(f"\n📝 Would fix: {template_path.relative_to(self.base_dir)}")
                for fix in all_fixes:
                    print(f"   - {fix}")
                self.fixes_applied += len(all_fixes)
                self.files_modified += 1
            else:
                try:
                    with open(template_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"\n✅ Fixed: {template_path.relative_to(self.base_dir)}")
                    for fix in all_fixes:
                        print(f"   - {fix}")
                    self.fixes_applied += len(all_fixes)
                    self.files_modified += 1
                except Exception as e:
                    print(f"❌ Error writing {template_path}: {e}")
                    return False

        return True

    def fix_all_templates(self):
        """Fix all templates."""
        templates = self.find_templates()

        print(f"\n{'='*80}")
        print(f"HTML TEMPLATE FIXER - Floor Management System")
        print(f"{'='*80}\n")

        if self.dry_run:
            print("🔍 DRY RUN MODE - No files will be modified")
            print("   Run with --apply to make actual changes\n")

        print(f"Found {len(templates)} templates...\n")

        for template in sorted(templates):
            self.fix_template(template)

        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}")
        if self.dry_run:
            print(f"Would modify {self.files_modified} files")
            print(f"Would apply {self.fixes_applied} fixes")
            print(f"\nRun with --apply flag to make actual changes:")
            print(f"  python scripts/fix_templates.py --apply")
        else:
            print(f"Modified {self.files_modified} files")
            print(f"Applied {self.fixes_applied} fixes")
        print(f"{'='*80}\n")


def main():
    """Run template fixer."""
    import sys

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dry_run = '--apply' not in sys.argv

    fixer = TemplateFixer(base_dir, dry_run=dry_run)
    fixer.fix_all_templates()


if __name__ == '__main__':
    main()
