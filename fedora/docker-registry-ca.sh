#!/bin/bash
set -eu

if [[ -n "${PROXY_CA_CERT_B64:-}" ]]; then
  tmp=$(mktemp)
  trap 'rm -f "$tmp"' EXIT
  printf '%s' "$PROXY_CA_CERT_B64" | base64 -d > "$tmp"
  if ! cmp -s "$tmp" /etc/docker/certs.d/docker.io/ca.crt; then
    sudo install -m 0644 "$tmp" /etc/docker/certs.d/docker.io/ca.crt
  fi
fi
