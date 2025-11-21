"""
HTML Template Checker

Checks all Django templates for common issues:
- Missing closing tags
- Broken template tags
- Missing {% load %} statements
- Hardcoded URLs (should use {% url %})
- Missing CSRF tokens in forms
- Template syntax errors
"""
import os
import re
from pathlib import Path
from collections import defaultdict


class TemplateChecker:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.issues = defaultdict(list)
        self.stats = {
            'total_templates': 0,
            'templates_with_issues': 0,
            'total_issues': 0
        }

    def find_templates(self):
        """Find all HTML templates."""
        templates = []
        for pattern in ['**/*.html', '**/templates/**/*.html']:
            templates.extend(self.base_dir.glob(pattern))
        return templates

    def check_template(self, template_path):
        """Check a single template for issues."""
        issues = []

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            return [f"Error reading file: {e}"]

        # Check 1: Unclosed Django template tags
        open_tags = re.findall(r'{%\s*(\w+)', content)
        close_tags = re.findall(r'{%\s*end(\w+)', content)

        for tag in ['if', 'for', 'block', 'with']:
            open_count = open_tags.count(tag)
            close_count = close_tags.count(tag)
            if open_count != close_count:
                issues.append(f"Mismatched {{% {tag} %}} tags: {open_count} opened, {close_count} closed")

        # Check 2: Missing {% load %} for common tags
        if 'static' in content and '{% load static %}' not in content and '{% load staticfiles %}' not in content:
            issues.append("Uses 'static' but missing {% load static %}")

        if any(tag in content for tag in ['|add:', '|date:', '|default:']) and '{% load' not in content:
            issues.append("Uses template filters but no {% load %} statement")

        # Check 3: Hardcoded URLs (should use {% url %})
        hardcoded_urls = re.findall(r'href=["\']/([\w/-]+)["\']', content)
        if hardcoded_urls and len(hardcoded_urls) > 2:  # Allow a few
            issues.append(f"Found {len(hardcoded_urls)} hardcoded URLs (should use {{% url %}})")

        # Check 4: Forms without CSRF token
        if '<form' in content and 'method="post"' in content.lower():
            if '{% csrf_token %}' not in content and 'csrfmiddlewaretoken' not in content:
                issues.append("POST form missing {% csrf_token %}")

        # Check 5: Unclosed HTML tags
        for tag in ['div', 'table', 'form', 'ul', 'ol']:
            open_html = len(re.findall(f'<{tag}[>\s]', content, re.IGNORECASE))
            close_html = len(re.findall(f'</{tag}>', content, re.IGNORECASE))
            if open_html != close_html:
                issues.append(f"Mismatched <{tag}> tags: {open_html} opened, {close_html} closed")

        # Check 6: Invalid Django template syntax
        invalid_syntax = [
            (r'{%\s*\w+\s*%[^}]', "Invalid template tag syntax (missing closing })"),
            (r'{{\s*\w+\s*}[^}]', "Invalid variable syntax (missing closing })"),
            (r'{%\s*end\w+\s+\w+', "Invalid endblock syntax (has extra content)"),
        ]

        for pattern, message in invalid_syntax:
            if re.search(pattern, content):
                issues.append(message)

        # Check 7: Missing extends/block structure
        if '{% extends' not in content and '<!DOCTYPE html>' not in content:
            if '{% block content %}' in content:
                issues.append("Has {% block content %} but no {% extends %}")

        # Check 8: Bootstrap class issues (if using Bootstrap)
        if 'class=' in content:
            # Check for common typos
            if 'col-md' in content and 'container' not in content and 'row' not in content:
                issues.append("Uses Bootstrap grid (col-md) without container/row")

        return issues

    def check_all_templates(self):
        """Check all templates and generate report."""
        templates = self.find_templates()
        self.stats['total_templates'] = len(templates)

        print(f"\n{'='*80}")
        print(f"HTML TEMPLATE CHECKER - Floor Management System")
        print(f"{'='*80}\n")
        print(f"Found {len(templates)} templates to check...\n")

        for template in sorted(templates):
            rel_path = template.relative_to(self.base_dir)
            issues = self.check_template(template)

            if issues:
                self.stats['templates_with_issues'] += 1
                self.stats['total_issues'] += len(issues)
                self.issues[str(rel_path)] = issues

        self.print_report()

    def print_report(self):
        """Print comprehensive report."""
        print(f"\n{'='*80}")
        print(f"RESULTS")
        print(f"{'='*80}\n")

        if not self.issues:
            print("✅ All templates passed checks! No issues found.\n")
        else:
            print(f"⚠️  Found issues in {self.stats['templates_with_issues']} templates:\n")

            for template_path, template_issues in sorted(self.issues.items()):
                print(f"\n📄 {template_path}")
                print(f"   {'-' * 60}")
                for i, issue in enumerate(template_issues, 1):
                    print(f"   {i}. {issue}")

        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}")
        print(f"Total templates checked: {self.stats['total_templates']}")
        print(f"Templates with issues:   {self.stats['templates_with_issues']}")
        print(f"Total issues found:      {self.stats['total_issues']}")
        print(f"{'='*80}\n")


def main():
    """Run template checker."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    checker = TemplateChecker(base_dir)
    checker.check_all_templates()


if __name__ == '__main__':
    main()
