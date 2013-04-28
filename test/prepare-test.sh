#!/bin/bash

DIR="$(dirname "${0}")"
GDRSYNC="${DIR}/../gdrsync.py"

function logAndRun() {
    echo "${@}" 1>&2

    eval "${@}"
}

logAndRun "${GDRSYNC}" -vv -dr "${DIR}/remote/" /test

find "${DIR}/local" | xargs touch -d '1978-08-03 01:23:45.6789987Z'
touch -d '1970-01-01 00:00:00Z' "${DIR}/local/invalidDate"

cat <<-EOF
Rename using the web interface:
    duplicateFile2 -> duplicateFile
    duplicateFolder2 -> duplicateFolder
EOF
