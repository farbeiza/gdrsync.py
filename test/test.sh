#!/bin/bash

set -x

DIR="$(dirname "${0}")"
DIR_URL="file://$(realpath "${DIR}")"
GDRSYNC="${DIR}/../gdrsync.py"

"${GDRSYNC}" -vv -n "${DIR_URL}/local/" gdrive:///test

"${GDRSYNC}" -vv -r -n "${DIR}/local/" gdrive://drive.google.com/test

"${GDRSYNC}" -vv -u \
             --rexclude ".*/excluded.*" \
             "${DIR_URL}/local/" gdrive:///test

"${GDRSYNC}" -vv -Lr --delete --delete-excluded \
             --rexclude=".*/excluded.*" --rexclude=".*/deleteExcluded.*" \
             --rinclude=".*/includedFolder/includedFile" --rexclude=".*/includedFolder/.*" \
             "${DIR}/local/" gdrive://drive.google.com/test
