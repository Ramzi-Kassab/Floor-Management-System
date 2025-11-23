#!/usr/bin/env python3
"""Audit all modules to find which ones need more templates."""

import os
from pathlib import Path
import re

ops_dir = Path('floor_app/operations')

print("Module Audit Report")
print("=" * 80)
print(f"{'Module':<30} {'Templates':<12} {'Views':<12} {'Status':<20}")
print("-" * 80)

modules = []

for module_dir in sorted(ops_dir.iterdir()):
    if not module_dir.is_dir():
        continue

    module_name = module_dir.name

    # Count templates
    templates_dir = module_dir / 'templates'
    template_count = 0
    if templates_dir.exists():
        template_count = len(list(templates_dir.rglob('*.html')))

    # Count views
    views_file = module_dir / 'views.py'
    view_count = 0
    if views_file.exists():
        content = views_file.read_text()
        # Count function and class-based views
        view_count = len(re.findall(r'^(def |class \w+.*View)', content, re.MULTILINE))

    # Determine status
    if template_count == 0:
        status = "❌ No templates"
    elif view_count == 0:
        status = "⚠️  No views file"
    elif template_count < view_count:
        status = f"⚠️  Missing {view_count - template_count} templates"
    elif template_count < 5:
        status = "🟡 Small module"
    else:
        status = "✅ Complete"

    modules.append({
        'name': module_name,
        'templates': template_count,
        'views': view_count,
        'status': status,
        'gap': max(0, view_count - template_count)
    })

    print(f"{module_name:<30} {template_count:<12} {view_count:<12} {status:<20}")

print("-" * 80)
print(f"\nTotal modules: {len(modules)}")
print(f"Total templates: {sum(m['templates'] for m in modules)}")
print(f"Total views: {sum(m['views'] for m in modules)}")

# Show modules that might need attention
print("\n" + "=" * 80)
print("MODULES NEEDING ATTENTION:")
print("=" * 80)

needs_attention = [m for m in modules if m['gap'] > 0 or (m['templates'] > 0 and m['templates'] < 5 and m['views'] > 0)]
if needs_attention:
    for m in sorted(needs_attention, key=lambda x: x['gap'], reverse=True):
        print(f"- {m['name']}: {m['templates']} templates, {m['views']} views ({m['status']})")
else:
    print("All modules complete! 🎉")
