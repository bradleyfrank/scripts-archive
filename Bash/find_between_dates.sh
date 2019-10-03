#!/bin/bash

set -euo pipefail

four_months_ago="$(date -d "4 months ago" "+%F")"
one_month_ago="$(date -d "1 month ago" "+%F")"

find /path/to/dir/ \
    -not -newermt "$one_month_ago" \
    -newermt "$four_months_ago" \
    -exec aws s3 mv {} s3://snapitcc \; \
    -exec rm -f {} \;

