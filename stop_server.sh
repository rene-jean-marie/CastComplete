#!/bin/bash
# Script to stop a running CastComplete server remotely

# Default server address
HOST="127.0.0.1"
PORT="5001"
SECRET="castcomplete"

# Process command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --host=*)
      HOST="${1#*=}"
      ;;
    --port=*)
      PORT="${1#*=}"
      ;;
    --secret=*)
      SECRET="${1#*=}"
      ;;
    --help)
      echo "Usage: $0 [--host=HOST] [--port=PORT] [--secret=SECRET]"
      echo ""
      echo "Options:"
      echo "  --host=HOST    Server hostname or IP (default: 127.0.0.1)"
      echo "  --port=PORT    Server port (default: 5001)"
      echo "  --secret=SECRET Authentication secret (default: castcomplete)"
      echo ""
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
  shift
done

echo "Stopping CastComplete server at $HOST:$PORT..."

# Use curl to send the stop command
curl -s -X POST "http://$HOST:$PORT/api/admin/server/control" \
  -H "Content-Type: application/json" \
  -d "{\"action\": \"stop\", \"secret\": \"$SECRET\"}"

STATUS=$?

if [ $STATUS -eq 0 ]; then
  echo -e "\nStop command sent successfully. Server should shut down momentarily."
else
  echo -e "\nFailed to send stop command. Make sure the server is running and accessible."
fi
