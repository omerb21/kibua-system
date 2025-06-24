#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

# Install dependencies
pip install -r requirements.txt

# Run the application
exec gunicorn --worker-class sync --workers=4 --bind 0.0.0.0:$PORT wsgi:app
