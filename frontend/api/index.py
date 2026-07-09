import sys
import os

# Add root and backend directories to python path so imports resolve correctly
# Since this file is in frontend/api/, the project root is 2 levels up.
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
backend_dir = os.path.join(root_dir, 'backend')

sys.path.append(root_dir)
sys.path.append(backend_dir)

from backend.app.main import app
