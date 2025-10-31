#!/bin/bash
# Helper script to run the Instagram scraper with the virtual environment

cd "$(dirname "$0")"
.venv/bin/python scrapper.py "$@"
