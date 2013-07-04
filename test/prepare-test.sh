#!/bin/bash

DIR="$(dirname "${0}")"
GDRSYNC="${DIR}/../gdrsync.py"

function logAndRun() {
    echo "${@}" 1>&2

    eval "${@}"
}

logAndRun "${GDRSYNC}" -vv -dr "${DIR}/remote/" /test

find "${DIR}/local" | xargs touch -h -t '197808030123.45'
touch -t '197001010000.00' "${DIR}/local/invalidDate"

cat <<-EOF
Rename using the web interface:
    duplicateFile2 -> duplicateFile
    duplicateFolder2 -> duplicateFolder
EOF
