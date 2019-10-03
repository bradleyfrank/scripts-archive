#!/bin/bash

DATE=$(date +%Y%m%d)
PASSWORD="password"

LETSENCRYPT="/etc/letsencrypt/live/example.com"
TOMCAT="/etc/tomcat8/Catalina/localhost"

BUNDLE="${TOMCAT}/bundle.pfx"
PRIVKEY="${LETSENCRYPT}/privkey.pem"
CERT="${LETSENCRYPT}/cert.pem"
CHAIN="${LETSENCRYPT}/chain.pem"

mv ${BUNDLE} ${TOMCAT}/bundle-"${DATE}".pfx
openssl pkcs12 -export -out ${BUNDLE} -inkey ${PRIVKEY} -in ${CERT} -certfile ${CHAIN} -password pass:${PASSWORD}
chown tomcat8:tomcat8 ${BUNDLE}
chmod 755 ${BUNDLE}
systemctl restart tomcat8
