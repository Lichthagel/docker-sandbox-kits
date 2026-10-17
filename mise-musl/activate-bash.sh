#!/bin/sh
set -eu

bashrc="${HOME:?HOME must be set}/.bashrc"
activation='eval "$(mise activate bash)"'

touch "$bashrc"
if ! grep -Fqx "$activation" "$bashrc"; then
    printf '%s\n' "$activation" >> "$bashrc"
fi
