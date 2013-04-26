#!/bin/bash

DIR="$(dirname "${0}")"
GDRSYNC="${DIR}/../gdrsync.py"

function logAndRun() {
    echo "${@}" 1>&2

    eval "${@}"
}

find "${DIR}/local" | xargs touch -d '1978-08-03 01:23:45.6789987Z'
logAndRun "${GDRSYNC}" -vv -dr "${DIR}/remote" /test

cat <<-EOF
Rename using the web interface:
    duplicateFile2 -> duplicateFile
    duplicateFolder2 -> duplicateFolder
EOF
