#!/bin/bash

set -e

PYTHON=(python3 python2 python)

for p in "${PYTHON[@]}"
do
  python=$(command -v "$p")
  if $python -m site >/dev/null 2>&1; then
    dirs=()
    while IFS= read -r line; do
      dirs+=( "$line" )
    done < <( $python -m site | grep -E "site-packages'" | awk -F"'" '{print $2}' )
    for d in "${dirs[@]}"
    do
      if [[ -d "${d}/powerline" ]]; then
        powerline=". ${d}/powerline/bindings/bash/powerline.sh"
        echo "${powerline}" > "${HOME}"/.config/homebox/powerline
        exit 0
      fi
    done
  fi
done

exit 1
