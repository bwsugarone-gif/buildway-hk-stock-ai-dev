"""
Compatibility entrypoint for Streamlit Cloud.

The canonical Streamlit implementation is app.py. Keep this file tiny so any
deployment still pointing at streamlit_app.py executes the same latest app.
"""

import app  # noqa: F401
