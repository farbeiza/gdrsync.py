#!/bin/bash

set -x

DIR="$(dirname "${0}")"
GDRSYNC="${DIR}/../gdrsync.py"

"${GDRSYNC}" -vv -n "${DIR}/local/" /test

"${GDRSYNC}" -vv -r -n "${DIR}/local/" /test

"${GDRSYNC}" -vv -u "${DIR}/local/" /test

"${GDRSYNC}" -vv -dLr "${DIR}/local/" /test
