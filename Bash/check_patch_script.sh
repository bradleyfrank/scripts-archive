#!/bin/bash

function usage () {
  echo "Usage: check_patch_script.sh <md5> [dev|test|stage|prod]"
}

if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
  usage
  exit 0
elif [[ "$1" == "" ]] || [[ "$2" == "" ]]; then
  echo "Error: missing arguments"
  usage
  exit 1
else
  PATCH_SCRIPT_MD5="$1"
  ESAI_ENV="$2"
fi

salt_results=$(mktemp)

salt "*-${ESAI_ENV}-*" --out txt cmd.run 'md5sum /root/oneoffs/oneoffs/patch_script.sh' 2>/dev/null | grep 'patch_script.sh' > "$salt_results"
hosts="$(grep -rv "${PATCH_SCRIPT_MD5}" "$salt_results" | awk -F ':' '{print $1}')"

echo ""
echo "Hosts with missing or incorrect patch script:"
echo "$hosts"
echo ""
