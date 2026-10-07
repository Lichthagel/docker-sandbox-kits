# Docker Sandbox kits

This project contains a minimal Alpine Linux Docker Sandbox v3 workload and a
separate `mise` tool mixin.

## Run the Alpine workload with mise

From the repository root, create a sandbox using the workload and mixin from
this GitHub repository. Replace `<commit>` with the 40-character commit SHA
you want to use (the same commit is used for both kits):

```sh
sbx run "git+https://github.com/Lichthagel/docker-sandbox-kits.git#ref=635d7b7524e5562396182b195a1d492c21148da8&dir=alpine" \
  --kit "git+https://github.com/Lichthagel/docker-sandbox-kits.git#ref=635d7b7524e5562396182b195a1d492c21148da8&dir=mise"
```

The source references are pinned to commit `635d7b7524e5562396182b195a1d492c21148da8`. For local development, the equivalent command is `sbx run ./alpine --kit ./mise`.

The workload starts Bash as the non-root `agent` user (UID/GID 1000) in
`/home/agent/workspace`. Inside the sandbox, verify mise with:

```sh
mise --version
```

## Build the Alpine workload

The workload and mixin use Alpine `3.24.2` as their build base.

Build for the target architecture with Docker Buildx:

```sh
docker buildx build ./alpine -f ./alpine/alpine.yaml \
  --platform linux/amd64 -t alpine-workload:amd64 --load
```

For arm64, build with:

```sh
docker buildx build ./alpine -f ./alpine/alpine.yaml \
  --platform linux/arm64 -t alpine-workload:arm64 --load
```

The `alpine/` workload contains only the sandbox essentials (`bash`, `git`,
`curl`, and CA certificates); mise is installed separately by `mise/`.

## Build the mise mixin

Build a v3 kit image with Docker Buildx:

```sh
docker buildx build ./mise -f ./mise/mise.yaml \
  --platform linux/amd64 -t mise-mixin:dev --load
```

To build an arm64 image, use `--platform linux/arm64` instead. The target
platform determines which musl binary the installer downloads.

By default, the installer selects the latest eligible stable mise release
(releases at least 24 hours old) at kit build time. To pin a release for a
build, pass the optional build-time version override:

```sh
docker buildx build ./mise -f ./mise/mise.yaml -t mise-mixin:dev \
  --platform linux/amd64 --build-arg version=<version> --load
```

Use `--platform linux/arm64` to build for arm64. The override must be a
three-part version such as `2026.10.3`; leave it unset for the installer's
latest-release behavior.

The local kit directories can be passed directly to `sbx`; manually building
the kit images is not required for local use. To publish kits, push their
images to a registry and use the registry references.
