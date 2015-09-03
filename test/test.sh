#!/bin/bash

set -x

DIR="$(dirname "${0}")"
DIR_URL="file://$(realpath "${DIR}")"
GDRSYNC="${DIR}/../gdrsync.py"

"${GDRSYNC}" -vv -n "${DIR_URL}/local/" gdrive:///test

"${GDRSYNC}" -vv -r -n "${DIR}/local/" gdrive://drive.google.com/test

"${GDRSYNC}" -vv -u --exclude ".*/excluded.*" "${DIR_URL}/local/" gdrive:///test

"${GDRSYNC}" -vv -Lr --delete --delete-excluded --exclude=".*/excluded.*" --exclude=".*/deleteExcluded.*" "${DIR}/local/" gdrive://drive.google.com/test
