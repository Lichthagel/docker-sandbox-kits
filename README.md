# Docker Sandbox kits

This project contains a minimal Alpine Linux Docker Sandbox v3 workload and a
separate `mise` tool mixin.

## Run the Alpine workload with mise

From the repository root, create a sandbox using the workload and mixin from
the default branch of this GitHub repository:

```sh
sbx settings set kit.allowedSources '["docker.io/","github.com/Lichthagel/"]'
sbx run 'git+https://github.com/Lichthagel/docker-sandbox-kits.git#dir=alpine' --kit 'git+https://github.com/Lichthagel/docker-sandbox-kits.git#dir=mise'
```

The allowed-sources setting permits kits from Docker Hub and this GitHub
account. The references follow the repository's default branch. For local
development, the equivalent command is `sbx run ./alpine --kit ./mise`.

The workload starts Bash as the non-root `agent` user (UID/GID 1000) in
`/home/agent/workspace`. Inside the sandbox, verify mise with:

```sh
mise --version
```

To install Node.js as the global default, run `mise use -g node`. The Alpine
workload configures mise to use prebuilt musl binaries rather than compiling
Node.js from source, and includes the `libstdc++` runtime those binaries need.
These Node.js binaries come from the community-maintained unofficial builds
project; they are not official Node.js releases. Run Node.js through mise with
`mise exec -- node --version`, or activate mise with
`eval "$(mise activate bash)"` to use `node` directly in the shell.
In policy-controlled sandboxes, the first install may require network approval
for `unofficial-builds.nodejs.org`.

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

The `alpine/` workload contains the sandbox essentials (`bash`, `git`, `curl`,
and CA certificates), `libstdc++` for Node.js musl binaries, and global mise
settings to select those binaries instead of compiling from source. mise is
still installed separately by `mise/`.

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
