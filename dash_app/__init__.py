# Marks dash_app/ as a proper package (not a namespace package).
# Without this file, granian loads dash_app/dash_app.py as the
# top-level module "dash_app" (a file, not a package), which breaks
# all sub-package imports inside it.
# With this file, Python loads it as a package first, then
# dash_app.py is loaded as dash_app.dash_app — giving it
# the correct __package__ context for relative imports.
from .dash_app import app  # noqa: F401
