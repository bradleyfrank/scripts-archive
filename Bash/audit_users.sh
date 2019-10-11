#!/bin/bash
#
# Description: The script parses /etc/passwd and /etc/sudoers for all user
# accounts that are non-system accounts. The results are emailed to an auditor
# for review.
#
# Install a crontab entry on any hosts where this needs to run:
# 0 6 1 * * /root/oneoffs/oneoffs/audit_utln.sh >/dev/null 2>&1
#

# date in YYYYMMDD format
date="$(date +'%Y%m%d')"

# hostname in short format (e.g. vmname-prod-01)
short_hostname="$(hostname --short)"

# email address(es) to send audit
addresses=""

# a temp directory for performing all work
audit_dir="$(mktemp -d)"

# a copy of the raw passwd and sudoers files
etc_passwd="$audit_dir"/"$date"_"$short_hostname"_raw_passwd.txt
etc_sudoers="$audit_dir"/"$date"_"$short_hostname"_raw_sudoers.txt

# files to save all resulting non-system users
passwd_users="$audit_dir"/"$date"_"$short_hostname"_passwd_users.txt
sudo_users="$audit_dir"/"$date"_"$short_hostname"_sudo_users.txt

# system users within passwd
passwd_system_users=( HOST root bin daemon adm lp sync shutdown halt mail ftp \
  nobody dbus polkitd postfix sshd nscd nslcd ntp vmware puppet exim tss \
  systemd-bus-proxy systemd-network nx geoclue usbmuxd libstoragemgmt abrt \
  rtkit saslauth setroubleshoot pulse colord gdm qemu readvd unbound \
  gnome-intial-setup php-fpm apache nobody gnome-initial-setup games operator \
  avahi avahi-autoipd nagios splunk nrpe rpc rpcuser tcpdump nfsnobody \
  infoscan c0ra1e haldaemon audit tidal uucp vcsa advadm advxfer gopher mysql )

# system users within sudoers
sudo_system_users=( HOST c0ra1e snapgc FIN_PROD_ADMIN exim foreman-proxy \
  infoscan iiiroot jenkins nagios nrpe oracle etesta03 etesb01 icinga jab \
  ppadmin sungardhe weblog )


# copy system files out of an abundance of caution
command cp /etc/passwd "$etc_passwd"
command cp /etc/sudoers "$etc_sudoers"


# function to search system_users array for a specific utln
# copy pasta from StackOverflow: https://stackoverflow.com/a/8574392
is_sys_account() {
  local sys_accounts utln="$1"
  shift
  for sys_accounts; do
    [[ "$sys_accounts" == "$utln" ]] && return 0
  done
  return 1
}


# compare all accounts in 'passwd' against the list of system users to
# create a list of the non-system users
while read -r passwd_utln; do

  if ! is_sys_account "$passwd_utln" "${passwd_system_users[@]}"; then
    echo "$passwd_utln" >> "$passwd_users"
  fi

done <<< "$(cut -f1 -d ':' < "$etc_passwd")"


# compare all accounts in 'sudoers' against the list of system users to
# create a list of the non-system users
while read -r sudo_utln; do

  if ! is_sys_account "$sudo_utln" "${sudo_system_users[@]}"; then
    echo "$sudo_utln" >> "$sudo_users"
  fi

done <<< "$(grep -E '^User_Alias' "$etc_sudoers" | cut -f2 -d= | tr , '\n' | sed 's/ //g' | sort -u)"


# email the files as attachments
mailx -s "UTLN Audit for $(date +'%B %Y') on $short_hostname" \
  -a "$passwd_users" -a "$sudo_users" -a "$etc_passwd" -a "$etc_sudoers" \
  "$addresses" \
  <<< "This is the monthly user audit script. Attached are 4 files:

    * raw_passwd -- The /etc/passwd file
    * raw_sudoers -- The /etc/sudoers file
    * passwd_users -- Non-system users present on the server
    * sudo_users -- Non-system users present in /etc/sudoers

  The file checksum and block count are as follows:

    * /etc/sudoers -- $(sum /etc/sudoers)
    * /etc/passwd  -- $(sum /etc/passwd)
  "


rm -rf "$audit_dir"
