#!/bin/bash

PATH="$(dirname "${0}")"

"${PATH}/../gdrsync.py" "${PATH}/local" /remote

