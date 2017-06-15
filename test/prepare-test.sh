#!/bin/bash

set -x

DIR="$(dirname "${0}")"
GDRSYNC="${DIR}/../gdrsync.py"

"${GDRSYNC}" -vv -Lr --delete "${DIR}/remote/" gdrive:///test

find "${DIR}/local" | xargs touch -h -d '1978-03-08 01:23:45.6789987Z'
touch -d '1978-03-08 01:23:45.001234Z' "${DIR}/local/singleDigitMilliseconds"
touch -d '1970-01-01 00:00:00Z' "${DIR}/local/invalidDate"

cat <<-EOF
Rename using the web interface:
    duplicateFile2 -> duplicateFile
    duplicateFolder2 -> duplicateFolder
EOF
