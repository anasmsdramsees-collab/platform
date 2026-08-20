"""`python -m syltra_design_tokens` — report the contrast of every token pair.

A separate entry point rather than a `__main__` guard in `tokens.py`, because
the package imports that module: running it as `-m syltra_design_tokens.tokens`
loads it twice and Python warns about the duplicate.
"""

from syltra_design_tokens.tokens import main

main()
