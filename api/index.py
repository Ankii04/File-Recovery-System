import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import the Flask app from backend
from backend import app

# Vercel expects the Flask app to be named 'app' or exposed via a callable
# The app object itself is the WSGI application
