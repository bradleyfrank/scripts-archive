#!/bin/bash

function add_to_known_hosts () {
  local url="$1" host_fingerprint="$2" 
  local known_hosts keyfile keyscan fingerprint

  known_hosts="$HOME/.ssh/known_hosts"
  keyfile=$(mktemp)
  keyscan=$(ssh-keyscan "$url" 2>/dev/null)

  echo "$keyscan" > "$keyfile"
  
  fingerprint=$(ssh-keygen -lf "$keyfile" -E md5 | cut -d ' ' -f 2)

  if [[ "$fingerprint" == "$host_fingerprint" ]]; then
    key="$(echo "$keyscan" | cut -d ' ' -f 3)"
    if ! grep -qr "$key" "$known_hosts" 2>/dev/null; then
      echo -n "Adding $url SSH key to known_hosts... "
      echo "$keyscan" >> "$known_hosts"
      echo "done"
    fi
  else
    echo "Error: $url SSH key fingerprints do not match."
    exit 1
  fi
}
