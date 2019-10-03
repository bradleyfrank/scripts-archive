#!/bin/bash

set -eu


SSL_CONF="/etc/httpd/conf.d/ssl.conf"
TMP_SSL_CONF="$SSL_CONF".tmp
ORIG_SSL_CONF="$SSL_CONF"."$(date +%Y%m%d)"


# Exit if ssl.conf doesn't exist
if [[ ! -f "$SSL_CONF" ]]; then exit 0; fi


# Make two copies for modification and a backup
# Use 'command' to get around the system '-i' alias
command cp "$SSL_CONF" "$TMP_SSL_CONF"
command cp "$SSL_CONF" "$ORIG_SSL_CONF"


#
# SSLHonorCipherOrder
#
echo -n "Trying to set 'SSLHonorCipherOrder'... "

honor_cipher_order="SSLHonorCipherOrder on"

if ! grep -qE "^$honor_cipher_order" "$TMP_SSL_CONF"; then
  # Attempt to change existing value
  sed -i "s/^SSLHonorCipherOrder.*$/$honor_cipher_order/" "$TMP_SSL_CONF"
fi

if ! grep -qE "^$honor_cipher_order" "$TMP_SSL_CONF"; then
  # Attempt to change commented value
  sed -i "s/^#SSLHonorCipherOrder.*$/$honor_cipher_order/" "$TMP_SSL_CONF"
fi

# Final check if change was made
if ! grep -qE "^$honor_cipher_order" "$TMP_SSL_CONF"; then
  echo "failed"
  exit 1
fi


#
# SSLProtocol
#
echo "Trying to set 'SSLProtocol'... "

protocols="SSLProtocol all -SSLv2 -SSLv3"

if ! grep -qE "^$protocols" "$TMP_SSL_CONF"; then
  # Attempt to change existing value
  sed -i "s/^SSLProtocol.*$/$protocols/" "$TMP_SSL_CONF"
fi

if ! grep -qE "^$protocols" "$TMP_SSL_CONF"; then
  # Attempt to change commented value
  sed -i "s/^#SSLProtocol.*$/$protocols/" "$TMP_SSL_CONF"
fi

# Final check if change was made
if ! grep -qE "^$protocols" "$TMP_SSL_CONF"; then
  echo "failed"
  exit 1
fi


#
# SSLCipherSuite
#
echo "Trying to set 'SSLCipherSuite'... "

cipher_suites="SSLCipherSuite ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA:ECDHE-RSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-RSA-AES256-SHA256:DHE-RSA-AES256-SHA:ECDHE-ECDSA-DES-CBC3-SHA:ECDHE-RSA-DES-CBC3-SHA:EDH-RSA-DES-CBC3-SHA:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:AES256-SHA256:AES128-SHA:AES256-SHA:DES-CBC3-SHA:!DSS"

if ! grep -qE "^$cipher_suites" "$TMP_SSL_CONF"; then
  # Attempt to change existing value
  sed -i "s/^SSLCipherSuite.*$/$cipher_suites/" "$TMP_SSL_CONF"
fi

if ! grep -qE "^$cipher_suites" "$TMP_SSL_CONF"; then
  # Attempt to change commented value
  sed -i "s/^#SSLCipherSuite.*$/$cipher_suites/" "$TMP_SSL_CONF"
fi

# Final check if change was made
if ! grep -qE "^$cipher_suites" "$TMP_SSL_CONF"; then
  echo "failed"
  exit 1
fi


#
# Move the file into place
#
echo -n "Moving new file into place... "
command cp "$TMP_SSL_CONF" "$SSL_CONF"
rm -f "$TMP_SSL_CONF"
echo "done"


#
# Run a httpd validation
#
echo -n "Running httpd validation... "
if ! httpd -t &>/dev/null; then
  echo "failed"
  echo -n "Putting back original ssl.conf... "
  command cp "$ORIG_SSL_CONF" "$SSL_CONF"
  echo "done"
  exit 1
else
  # Reload httpd
  echo "done"
  echo -n "Restarting httpd... "
  httpd -k restart &>/dev/null
  echo "done"
  exit 0
fi