#!/bin/bash
echo "✅ STARTING Gateway via shell CMD..."

unset FLASK_APP
unset FLASK_ENV
unset FLASK_DEBUG

python gateway/app.py
