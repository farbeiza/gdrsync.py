#!/bin/bash

set -x

DIR="$(dirname "${0}")"
DIR_URL="file://$(realpath "${DIR}")"
GDRSYNC="${DIR}/../gdrsync.py"

python "${GDRSYNC}" -vv -n "${DIR_URL}/local/" gdrive:///test

python "${GDRSYNC}" -vv -r -n "${DIR}/local/" gdrive://drive.google.com/test

python "${GDRSYNC}" -vv -u \
             --rexclude "excluded.*" \
             "${DIR_URL}/local/" gdrive:///test

python "${GDRSYNC}" -vv -Lr --delete --delete-excluded \
             --exclude="/excluded*" --exclude="/deleteExcluded*" \
             --include="includedFile" --exclude="includedFolder/*" \
             "${DIR}/local/" gdrive://drive.google.com/test
