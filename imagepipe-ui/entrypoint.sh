#!/bin/sh

# Replace env var, generate nginx.conf
envsubst '$GATEWAY_URL' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

echo "----- FINAL nginx.conf -----"
cat /etc/nginx/nginx.conf

# cmd launch Nginx
nginx -g 'daemon off;'