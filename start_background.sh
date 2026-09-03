#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PID_FILE="$DIR/.jarvis_daemon.pid"
if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
    echo "J.A.R.V.I.S. is already running in background (PID: $(cat $PID_FILE))."
    exit 0
fi
nohup python3 "$DIR/daemon.py" > "$DIR/jarvis_daemon.log" 2>&1 &
echo $! > "$PID_FILE"
echo "========================================================"
echo "  J.A.R.V.I.S. Background Mac Service Started!"
echo "  Listening 24/7 in background for: Hey Jarvis"
echo "========================================================"
