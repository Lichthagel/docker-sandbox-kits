#!/bin/sh
set -eu

mise use -g node@lts
eval "$(mise activate sh --shims)"
mise use -g --tool-option 'allow_builds=["@opencode/cli"]' npm:@opencode/cli
