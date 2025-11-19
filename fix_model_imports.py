#!/usr/bin/env python3
"""
Script to find and document all model import mismatches across the operations modules.
"""
import os
import re
from pathlib import Path

operations_path = Path("floor_app/operations")

issues = []

for module_dir in operations_path.iterdir():
    if not module_dir.is_dir() or module_dir.name.startswith('_'):
        continue

    views_file = module_dir / "views.py"
    models_dir = module_dir / "models"
    models_init = models_dir / "__init__.py" if models_dir.exists() else None

    if not views_file.exists():
        continue

    # Read views.py to find model imports
    views_content = views_file.read_text()

    # Find imports from .models
    import_match = re.search(r'from \.models import \(([^)]+)\)', views_content, re.DOTALL)
    if not import_match:
        import_match = re.search(r'from \.models import (.+)', views_content)

    if import_match:
        imported_models = [m.strip().rstrip(',') for m in import_match.group(1).split('\n') if m.strip() and not m.strip().startswith('#')]

        # Check what models actually exist
        if models_init and models_init.exists():
            models_content = models_init.read_text()
            # Find all class definitions
            actual_classes = re.findall(r'^class (\w+)\(', models_content, re.MULTILINE)

            missing = set(imported_models) - set(actual_classes)
            if missing:
                issues.append({
                    'module': module_dir.name,
                    'views_file': str(views_file),
                    'models_file': str(models_init),
                    'imported': imported_models,
                    'actual': actual_classes,
                    'missing': list(missing)
                })

print("=== MODEL IMPORT ISSUES ===\n")
for issue in issues:
    print(f"Module: {issue['module']}")
    print(f"  Views imports: {issue['imported']}")
    print(f"  Actually defined: {issue['actual']}")
    print(f"  MISSING: {issue['missing']}")
    print()
