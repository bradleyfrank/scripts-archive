#!/usr/bin/env bash

_progname="plex-backup"
_dayofweek=$(date +"%A")

_scratch_dir="/srv/sys/scratch/${_progname}-${_dayofweek}"
_backup_dir="/srv/sys/backups/plexms.francopuccini.casa"

fail_and_exit() {
  logger -t "$_progname" "$1"
  /bin/rm -rf "$_scratch_dir"
  exit 1
}

# Log start of script
logger -t "$_progname" "Starting backup..."
mkdir -p "$_scratch_dir"

# Backup plex application data
/bin/tar -cpzf "$_scratch_dir"/appdata.tar.gz -C /srv/appdata/plex . \
  || fail_and_exit "Failed to compress appdata directory."

# Archive backups into a single file
pushd "$_scratch_dir" > /dev/null 2>&1 \
  || fail_and_exit "Unable to find backup directory."

/bin/tar --remove-files -cpf "${_progname}"-"${_dayofweek}".tar \
  appdata.tar.gz || fail_and_exit "Failed to compress backups."

popd > /dev/null 2>&1 || fail_and_exit "Error changing directories."

# Sync backups to remote storage
/usr/bin/rsync -a --remove-source-files \
  "$_scratch_dir"/ "$_backup_dir"/ \
  || fail_and_exit "Failed to sync backup."

# Log end of script
logger -t "$_progname" "Finished backup."
