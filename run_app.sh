#-----------------------------------------------------------------------------
# run_app.sh
# Runs the testing app framework & suppresses output (writes to server.log)
# 
# Your virtual environment must be running for this to work!
# Usage: ./run_app.sh [port]
# Visit localhost:[port] to see the app
#-----------------------------------------------------------------------------

if [[ $# != 1 ]]
  then
    echo "usage: ./run_app.sh [port]"
    exit 1
fi

rm server.log
echo "Check server.log for server logs."
python testserver.py $1 2>&1 > server.log
