#!/bin/bash

set -x

DIR="$(dirname "${0}")"

PYTHON=("${DIR}/../venv/bin/python")
GDRSYNC="${DIR}/../gdrsync.py"

"${PYTHON[@]}" "${GDRSYNC}" -vv -Lr --delete "${DIR}/remote/" gdrive:///test

find "${DIR}/local" | xargs touch -h -d '1978-03-08 01:23:45.6789987Z'

cat <<-EOF
Rename using the web interface:
    duplicateFile2 -> duplicateFile
    duplicateFolder2 -> duplicateFolder
EOF
