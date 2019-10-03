#!/bin/bash

set -o errexit
set -o pipefail

if pgrep httpd >/dev/null 2>&1; then
  while read -r conf; do
    if [[ ! -f "$conf" ]]; then continue; fi

    mapfile -t server_names < <(grep -Er '^\s*ServerName.*' "$conf" | awk '{print $2}' | tr -d '"' | tr -d "'")

    mapfile -t document_roots< <(grep -Er '^\s*DocumentRoot.*' "$conf" | awk '{print $2}' | tr -d '"' | tr -d "'")

    num_docroots=${#document_roots[@]}
    num_servers=${#server_names[@]}

    if [[ $num_docroots -ne $num_servers ]]; then
      exit 1
    fi

    for ((i = 0; i <= ((num_servers - 1)); i++)); do
      vhost="${server_names[i]}"
      docroot="${document_roots[i]}"

      if [[ ! -d "$docroot" ]]; then continue; fi

      du="$(du -hc "$docroot" | tail -n 1 | awk '{print $1}')"

      echo -n "$HOSTNAME,$vhost,$docroot,$du,"
    done

  done <<< "$(httpd -t -D DUMP_VHOSTS 2>&1 | grep -E ':(80|443)' | grep -oE '\(.*\)' | tr -d '()' | cut -f1 -d ':')"
  exit 0
else
  echo -n "$HOSTNAME,-,-,-,"
  exit 0
fi
