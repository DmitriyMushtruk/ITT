#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Start the server
exec uvicorn main:app --reload --reload-dir . --host 0.0.0.0 --port 8000
