#!/bin/bash
set -eu

if [[ -n "${PROXY_CA_CERT_B64:-}" ]]; then
  tmp=$(mktemp)
  trap 'rm -f "$tmp"' EXIT
  printf '%s' "$PROXY_CA_CERT_B64" | base64 -d > "$tmp"
  system_ca=/etc/pki/ca-trust/source/anchors/sandbox-proxy.crt
  if ! cmp -s "$tmp" "$system_ca"; then
    sudo install -m 0644 "$tmp" "$system_ca"
    sudo update-ca-trust
  fi
  if ! cmp -s "$tmp" /etc/docker/certs.d/docker.io/ca.crt; then
    sudo install -m 0644 "$tmp" /etc/docker/certs.d/docker.io/ca.crt
  fi
fi
