import os
import sys

# Ensure parent directory is in path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import StandaloneRequestHandler

class handler(StandaloneRequestHandler):
    pass
