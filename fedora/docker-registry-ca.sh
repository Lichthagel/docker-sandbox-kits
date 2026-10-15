#!/bin/bash
set -eu

if [[ -n "${PROXY_CA_CERT_B64:-}" ]]; then
  tmp=$(mktemp)
  trap 'rm -f "$tmp"' EXIT
  printf '%s' "$PROXY_CA_CERT_B64" | base64 -d > "$tmp"
  system_ca=/etc/pki/ca-trust/source/anchors/sandbox-proxy.crt
  install_privileged() {
    if [[ $(id -u) -eq 0 ]]; then
      install -m 0644 "$1" "$2"
    else
      sudo install -m 0644 "$1" "$2"
    fi
  }
  if ! cmp -s "$tmp" "$system_ca"; then
    install_privileged "$tmp" "$system_ca"
    if [[ $(id -u) -eq 0 ]]; then
      update-ca-trust
    else
      sudo update-ca-trust
    fi
  fi
  if ! cmp -s "$tmp" /etc/docker/certs.d/docker.io/ca.crt; then
    install_privileged "$tmp" /etc/docker/certs.d/docker.io/ca.crt
  fi
fi
