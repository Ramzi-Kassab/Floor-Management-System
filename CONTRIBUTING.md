# Contributing to Floor Management System

Thank you for considering contributing to the Floor Management System! This document provides guidelines and instructions for contributing to the project.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)

## Code of Conduct

### Our Pledge
We are committed to providing a welcoming and inspiring community for all. By participating in this project, you agree to abide by our code of conduct.

### Our Standards
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

## Getting Started

### Prerequisites
- Python 3.10 or higher
- PostgreSQL 13 or higher
- Git
- Virtual environment tool (venv)

### Setup Development Environment

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/Floor-Management-System.git
   cd Floor-Management-System
   ```

2. **Run Setup Script**
   ```bash
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   ```

3. **Activate Virtual Environment**
   ```bash
   source venv/bin/activate
   ```

4. **Install Development Dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

5. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

6. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

7. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   ```

8. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

## Development Workflow

### Branching Strategy

We use **Git Flow** branching model:

- `master` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Urgent production fixes

### Creating a Feature Branch

```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

### Making Changes

1. Make your changes
2. Write/update tests
3. Run tests locally
4. Commit with descriptive messages

### Commit Message Guidelines

Follow conventional commits:

```
type(scope): subject

body

footer
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Example:**
```
feat(hr): add employee QR code generation

- Implemented QR code generation for employees
- Added download and print functionality
- Integrated with existing qrcodes app

Closes #123
```

## Coding Standards

### Python Style Guide

We follow **PEP 8** with some modifications:

- **Line Length**: Maximum 127 characters
- **Quotes**: Double quotes for strings
- **Imports**: Organized with `isort`
- **Formatting**: Automated with `black`

### Code Formatting

Before committing, format your code:

```bash
# Format with Black
black .

# Sort imports
isort .

# Check with Flake8
flake8 .
```

### Django Best Practices

1. **Models**
   - Use descriptive model names
   - Add `__str__` methods
   - Include help_text for fields
   - Use `related_name` for relationships
   - Add model validation in `clean()` method

2. **Views**
   - Prefer class-based views
   - Use mixins for common functionality
   - Add permission checks
   - Include docstrings

3. **Templates**
   - Extend `base.html`
   - Use template inheritance
   - Keep logic minimal
   - Use template tags and filters

4. **URLs**
   - Use named URLs
   - Namespace URL patterns
   - Keep URLs RESTful

### Documentation

- Add docstrings to all modules, classes, and functions
- Use Google-style docstrings
- Update README when adding features
- Document complex logic with inline comments

**Example:**
```python
def calculate_leave_days(start_date, end_date):
    """
    Calculate the number of working days between two dates.

    Args:
        start_date (date): The start date of the leave
        end_date (date): The end date of the leave

    Returns:
        int: The number of working days

    Raises:
        ValueError: If end_date is before start_date
    """
    pass
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific module tests
pytest floor_app/operations/hr/tests/

# Run with coverage
pytest --cov=floor_app --cov-report=html

# Run specific test
pytest floor_app/operations/hr/tests/test_models.py::EmployeeModelTest::test_create_employee
```

### Writing Tests

1. **Test Organization**
   - Place tests in `tests/` directory within each app
   - Name test files `test_*.py`
   - Group related tests in test classes

2. **Test Coverage**
   - Aim for >80% code coverage
   - Test all critical paths
   - Include edge cases
   - Test error handling

3. **Test Quality**
   - Each test should test one thing
   - Use descriptive test names
   - Follow AAA pattern (Arrange, Act, Assert)
   - Use fixtures and factories
   - Mock external dependencies

**Example:**
```python
def test_employee_creation_with_valid_data(self):
    """Test creating an employee with valid data"""
    # Arrange
    person = Person.objects.create(first_name='John', last_name='Doe')
    department = Department.objects.create(code='IT', name='IT')

    # Act
    employee = Employee.objects.create(
        person=person,
        employee_code='EMP001',
        department=department,
        hire_date=date.today()
    )

    # Assert
    self.assertEqual(employee.employee_code, 'EMP001')
    self.assertEqual(employee.department, department)
```

## Pull Request Process

### Before Submitting

1. **Update your branch**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout your-branch
   git rebase develop
   ```

2. **Run all checks**
   ```bash
   # Format code
   black .
   isort .

   # Run linters
   flake8 .

   # Run tests
   pytest

   # Check deployment
   python manage.py check --deploy
   ```

3. **Update documentation**
   - Update README if needed
   - Add/update docstrings
   - Update CHANGELOG.md

### Submitting Pull Request

1. **Push your branch**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request on GitHub**
   - Use descriptive title
   - Fill out PR template
   - Link related issues
   - Add screenshots if UI changes
   - Request reviewers

3. **PR Template**
   ```markdown
   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update

   ## Testing
   - [ ] Tests added/updated
   - [ ] All tests pass
   - [ ] Code coverage maintained/improved

   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated
   - [ ] No new warnings
   - [ ] Tests added
   ```

### Review Process

- At least one approval required
- All CI checks must pass
- No merge conflicts
- Documentation updated
- CHANGELOG updated

## Reporting Bugs

### Before Reporting

1. Check existing issues
2. Verify it's reproducible
3. Test on latest version

### Bug Report Template

```markdown
**Describe the bug**
Clear description of the bug

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What you expected to happen

**Screenshots**
If applicable

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.10.12]
- Django: [e.g., 5.2.6]
- Browser: [e.g., Chrome 120]

**Additional context**
Any other information
```

## Suggesting Enhancements

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
Description of the problem

**Describe the solution you'd like**
Clear description of what you want

**Describe alternatives considered**
Other solutions you've considered

**Additional context**
Mockups, examples, etc.
```

## Development Tools

### Recommended IDE Setup

**VS Code Extensions:**
- Python
- Django
- Pylance
- Black Formatter
- isort

**PyCharm Configuration:**
- Enable Django support
- Configure Black as external tool
- Set up pytest as test runner

### Pre-commit Hooks

Install pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

Hooks will run automatically before each commit.

## Questions?

- **Documentation**: Check `/docs` directory
- **Discussions**: GitHub Discussions
- **Email**: dev@example.com

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.

---

**Thank you for contributing to Floor Management System!**
