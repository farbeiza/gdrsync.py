#!/bin/bash

set -x

DIR="$(dirname "${0}")"
DIR_URL="file://$(realpath "${DIR}")"

PYTHON=("${DIR}/../venv/bin/python")
GDRSYNC="${DIR}/../gdrsync.py"

"${PYTHON[@]}" "${GDRSYNC}" -vv -n "${DIR_URL}/local/" gdrive:///test

"${PYTHON[@]}" "${GDRSYNC}" -vv -r -n "${DIR}/local/" gdrive://drive.google.com/test

"${PYTHON[@]}" "${GDRSYNC}" -vv -u \
             --rexclude "excluded.*" \
             "${DIR_URL}/local/" gdrive:///test

"${PYTHON[@]}" "${GDRSYNC}" -vv -Lr --delete --delete-excluded \
             --exclude="/excluded*" --exclude="/deleteExcluded*" \
             --include="includedFile" --exclude="includedFolder/*" \
             "${DIR}/local/" gdrive://drive.google.com/test
