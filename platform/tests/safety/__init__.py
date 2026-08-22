"""Package marker: gives each test module a unique dotted path.

Without it, two directories can both contain `conftest.py`, and mypy resolves
them to the same module name.
"""
