#!/bin/bash

set -x

DIR="$(dirname "${0}")"
GDRSYNC="${DIR}/../gdrsync.py"

"${GDRSYNC}" -vv -n "${DIR}/local/" /test

"${GDRSYNC}" -vv -r -n "${DIR}/local/" /test

"${GDRSYNC}" -vv -u -e ".*/excluded.*" "${DIR}/local/" /test

"${GDRSYNC}" -vv -dDLr -e ".*/excluded.*" -e ".*/deleteExcluded.*" "${DIR}/local/" /test
