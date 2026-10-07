# Alpine Docker Sandbox Workload Design

## Goal

Add a minimal, reusable Alpine Docker Sandbox v3 workload to this project so
users can run the existing `mise` v3 mixin without needing a separately
published Alpine workload.

## Proposed contents

- An `alpine/` kit directory with `alpine.yaml` and its matching
  `alpine.dockerfile`.
- A v3 descriptor declaring `kind: workload` and the config-less
  `com.docker.sandbox/sbx@1` capability.
- An Alpine 3.24.2-based Dockerfile, pinning the latest stable Alpine release
  when this design was updated, containing only sandbox prerequisites:
  `bash`, `git`, `curl`, and CA certificates. It creates a non-root `agent`
  user with UID/GID 1000 and home `/home/agent`, provides a workspace at
  `/home/agent/workspace`, and launches Bash.
- README instructions to run `sbx run ./alpine --kit ./mise` and verify the
  composition with `mise --version`.

## Runtime contract

The workload must satisfy the Docker Sandbox `sbx@1` contract: executable
`/bin/sh` and `/bin/bash`, a declared non-root image user resolving through
`/etc/passwd` to UID/GID and an absolute home directory, and a working
directory suitable for the workspace. Set the image user to `agent`, its
working directory to `/home/agent/workspace`, and its entrypoint to Bash with
no default command arguments. The workload descriptor must not request
network access, credentials, or unrelated capabilities.

The existing `mise/` mixin remains a separate kit and remains the only kit
installing mise. The Alpine workload contains no `mise` binary, language
runtimes, or other development tools.

## Documentation and validation

Update the root README's current placeholder workload reference to use the
local `./alpine` workload together with `--kit ./mise`. The Alpine base is
version-pinned. The mise mixin defaults to the official installer's latest
eligible stable release; an optional build-time version override can pin a
specific release. Retain instructions to build the v3 kits with Docker
Buildx.

Validate both descriptors and Dockerfiles with Docker Buildx. Run the
composed Alpine workload and verify that it runs as the non-root `agent` user,
starts Bash as its launch command, resolves `mise` on PATH, and successfully
prints the mise version. The workload's `sbx@1` declaration must be consistent
with the image configuration it describes.
