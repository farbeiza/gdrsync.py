#!/bin/bash

set -e

DIR="$(dirname "${0}")"
GDRSYNC="${DIR}/../gdrsync.py"

function logAndRun() {
    echo "${@}" 1>&2

    eval "${@}"
}

logAndRun "${GDRSYNC}" -vv -n "${DIR}/local/" gdrive:///test

logAndRun "${GDRSYNC}" -vv -r -n "${DIR}/local/" gdrive:///test

logAndRun "${GDRSYNC}" -vv -u "${DIR}/local/" gdrive:///test

logAndRun "${GDRSYNC}" -vv -dr "${DIR}/local/" gdrive:///test
