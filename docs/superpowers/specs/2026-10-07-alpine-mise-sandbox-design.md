# mise Docker Sandbox Mixin Design

## Goal

Create a minimal Docker Sandbox v3 tool mixin that adds `mise` to an existing
Alpine-based workload. It should make the `mise` executable available without
adding a sample project, `.mise.toml`, or additional development tools. The
mixin must not replace the workload's base image or launch command.

## Proposed contents

- A `mise/` kit directory containing `mise.yaml` and its matching
  `mise.dockerfile`, following Docker Sandbox's v3 authoring layout.
- A descriptor using the v3 kit syntax and declaring `kind: mixin`, with an
  optional build-time version override that defaults to empty. It does not
  declare a versioned `provides` entry because the default installed version
  is resolved by the official installer at build time.
- A Dockerfile that obtains an Alpine/musl-compatible `mise` executable and
  contributes only the needed file(s) to the mixin. Its Alpine build image is
  pinned to the latest stable release; installer/build-only dependencies
  should not be added to the target workload.
- A concise `README.md` with Buildx build/use instructions and a command to
  verify `mise` in an Alpine-based v3 workload.

## Compatibility and scope

Alpine uses `musl`, unlike Ubuntu's `glibc`. The mixin is intended for Alpine-
based workloads, and the implementation must use an installation path that
supports musl. Verify the executable in the target workload rather than
assuming a glibc-targeted binary will work. Because mixins contribute files to
an existing workload, do not make the mixin's build-stage base image an
assumption about the target workload's full operating system.

## Validation

Build the kit with Docker Buildx using its YAML descriptor, then attach it to a
compatible Alpine-based v3 workload and run `mise --version`. Documentation
should provide equivalent commands for users. A plain `docker build` of a
standalone Alpine image is not the acceptance path because this is a Docker
Sandbox mixin, not a standalone workload image.

The installer should choose its latest eligible stable release by default.
Users may supply an optional version build argument to pin a specific mise
release.
