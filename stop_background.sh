#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PID_FILE="$DIR/.jarvis_daemon.pid"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    kill -9 $PID 2>/dev/null || true
    rm -f "$PID_FILE"
    echo "J.A.R.V.I.S. background daemon (PID: $PID) stopped."
else
    pkill -f "python3.*daemon.py" 2>/dev/null || true
    echo "J.A.R.V.I.S. background daemon stopped."
fi
