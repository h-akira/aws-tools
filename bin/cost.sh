#!/bin/sh
#
# Created:      2024-07-28 21:28:19
set -eu

TOMORROW_UTC=$(date -d "tomorrow" -u +%Y-%m-%d)
ONE_WEEK_AGO_UTC=$(date -d "1 week ago" -u +%Y-%m-%d)
aws ce get-cost-and-usage --granularity DAILY --time-period Start=$ONE_WEEK_AGO_UTC,End=$TOMORROW_UTC --metrics AMORTIZED_COST
