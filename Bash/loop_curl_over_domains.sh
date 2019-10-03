#!/bin/bash

#IFS=$'\n' read -d '' -r -a lines < /root/domains
while IFS=$'\n' read -r line; do
  echo -n "$line,"
  if response="$(curl -Is --max-time 5 http://"$line"/server-status | head -n 1)"
  then
    echo "$response"
  else
    echo "404"
  fi
done < /root/domains
