#!/bin/bash

DIR="$(dirname "${0}")"
GDRSYNC="${DIR}/../gdrsync.py"

function logAndRun() {
    echo "${@}" 1>&2

    eval "${@}"
}

logAndRun "${GDRSYNC}" -vv -n "${DIR}/local" /remote

logAndRun "${GDRSYNC}" -vv -u "${DIR}/local" /remote

logAndRun "${GDRSYNC}" -vv -dr "${DIR}/local" /remote
