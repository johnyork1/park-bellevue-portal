import os
import sys

# Change to scripts directory so relative paths work correctly
os.chdir(os.path.join(os.path.dirname(__file__), 'scripts'))
sys.path.insert(0, os.path.dirname(__file__))

# Now run the actual app
exec(open("app.py").read())
