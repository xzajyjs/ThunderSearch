#!/bin/sh
#
# This is the default apptemplate error script
#

echo "Launch error"
if [ -n "$2" ]; then
    echo "An unexpected error has occurred during execution of the main script"
    echo ""
    echo "$2: $3"
    echo ""
fi

echo "See the py2app website for debugging launch issues"
echo ""
echo "ERRORURL: https://py2app.readthedocs.io/en/latest/debugging.html"
exit


