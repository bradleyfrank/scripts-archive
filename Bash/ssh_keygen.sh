PASSPHRASE_FILE="$HOME/.ssh/passphrase-$DATE"
PASSPHRASE_WORDS=4
PASSPHRASE_SAVE=$FALSE

#
# Generate a unique, secure passphrase using custom dictionary
#
generate_passphrase() {
  if [[ ! -d "$HOME"/.ssh ]]; then
    mkdir "$HOME"/.ssh
    chmod 700 "$HOME"/.ssh
  fi

  echo -n "Generating passphrase... "
  "$SHUF" --random-source=/dev/random -n "$PASSPHRASE_WORDS" "$DICT" | tr '[:upper:]' '[:lower:]' | sed -e ':a' -e 'N' -e '$!ba' -e "s/\\n/-/g" > "$PASSPHRASE_FILE"
  echo "done"
}


#
# Create a SSH key with ssh-keygen
#
generate_sshkey() {
  local comment
  local file
  local passphrase

  file="$HOME/.ssh/id_$1"

  if [[ ! -e "$file" ]]; then
    echo -n "Generating $1 SSH key... "

    comment="$USER@$HOSTNAME"
    passphrase=$(< "$PASSPHRASE_FILE" tr -d '\n')

    if ssh-keygen -t "$1" -b 4096 -N "$passphrase" -C "$comment" -f "$file" -q; then
      echo "done"
      PASSPHRASE_SAVE=$TRUE
    else
      echo "failed"
    fi
  fi
}


authkeys="$DOTFILES_DIR/ssh/.ssh/authorized_keys"
known_hosts="$HOME/.ssh/known_hosts"
ssh_create_files=("$authkeys" "$known_hosts")
sshkeys=("rsa" "ed25519")
commit=$FALSE


# Generate a temporary secure passphrase
install_dict
generate_passphrase

# Loop through keys to generate
for sshkey in "${sshkeys[@]}"; do
  generate_sshkey "$sshkey"
done

# Save or delete temporary passphrase
if [[ "$PASSPHRASE_SAVE" -eq $FALSE ]]; then
  rm -f "$PASSPHRASE_FILE"
else
  chmod 400 "$PASSPHRASE_FILE"
fi

# Create required SSH files
for ssh_file in "${ssh_create_files[@]}"; do
  touch_file "$ssh_file" "0600"
done

# Add public keys to authorized_keys
pushd "$HOME"/.ssh >/dev/null 2>&1
shopt -s nullglob
keys=(*.pub)

for key in "${keys[@]}"; do
  publickey=$(< "$HOME/.ssh/$key" tr -d '\n')

  if ! grep -rq "$publickey" "$authkeys"; then
    echo -n "Adding $key... "
    echo "$publickey" >> "$authkeys"
    echo "done"
    commit=$TRUE
  fi
done

popd >/dev/null 2>&1

if [[ "$commit" -eq $TRUE ]]; then
  pushd "$DOTFILES_DIR" >/dev/null 2>&1
  "$GIT" add "$authkeys" >/dev/null 2>&1
  "$GIT" commit -m "Added $HOST_NAME keys to authorized_keys." >/dev/null
  popd >/dev/null 2>&1
fi