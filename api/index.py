import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import the Flask app from backend
from backend import app

# Export the app for Vercel
# Vercel will call this as a serverless function
handler = app
