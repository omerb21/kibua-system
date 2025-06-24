#!/bin/bash
exec gunicorn --worker-class sync --workers=4 --bind 0.0.0.0:$PORT wsgi:app
