# Docker Sandbox kits

This project contains Alpine Linux and Fedora Docker Sandbox v3 workloads with
Docker Engine support, and separate mise, LiteLLM, OpenCode V2, and Pi mixins.

## Run a workload without mise

Both workloads start an interactive Bash shell without requiring mise:

```sh
sbx run ./alpine
sbx run ./fedora
```

Add the `mise` mixin when you want mise installed and automatically activated
for interactive Bash sessions.

## Run the Alpine workload with mise

From the repository root, create a sandbox using the workload and mixin from
the default branch of this GitHub repository:

```sh
sbx settings set kit.allowedSources '["docker.io/","github.com/Lichthagel/"]'
sbx run 'git+https://github.com/Lichthagel/docker-sandbox-kits.git#dir=alpine' --kit 'git+https://github.com/Lichthagel/docker-sandbox-kits.git#dir=mise' --kit-arg libc=musl
```

The allowed-sources setting permits kits from Docker Hub and this GitHub
account. The references follow the repository's default branch. For local
development, the equivalent command is
`sbx run ./alpine --kit ./mise --kit-arg libc=musl`.

The workload starts Bash as the non-root `agent` user (UID/GID 1000) in
`/home/agent/workspace`. It includes the Docker CLI, Buildx, and Compose, and
the `shell-docker` integration starts a private Docker Engine inside the
sandbox. It does not connect to your host's Docker daemon. Verify Docker and
Compose from inside the sandbox with:

```sh
docker info
docker compose version
```

Use `docker build`, `docker run`, and `docker compose` as usual; containers
remain inside the sandbox's private engine. Registry access is subject to the
sandbox's network policy.

Verify mise with:

```sh
mise --version
```

To install Node.js as the global default, run `mise use -g node`. The Alpine
workload configures mise to use prebuilt musl binaries rather than compiling
Node.js from source, and includes the `libstdc++` runtime those binaries need.
These Node.js binaries come from the community-maintained unofficial builds
project; they are not official Node.js releases. Run Node.js through mise with
`mise exec -- node --version`. Interactive Bash sessions activate mise
automatically; in a noninteractive Bash session, run
`eval "$(mise activate bash)"` to use `node` directly.
In policy-controlled sandboxes, the first install may require network approval
for `unofficial-builds.nodejs.org`.

## Run the Fedora workload with mixins

Use Fedora's native glibc mise binary by leaving the `libc` argument at its
default. The Fedora workload includes Docker Engine, Buildx, and Compose, and
starts Bash as the non-root `agent` user in `/home/agent/workspace`.

```sh
sbx run ./fedora --kit ./mise
# Include the LiteLLM deployment and OpenCode V2:
sbx run ./fedora --kit ./mise --kit ./litellm --kit ./opencode
```

The `mise` mixin defaults to `libc=glibc` for Fedora and other glibc workloads.
Alpine uses musl, so select the musl installer binary with
`--kit-arg libc=musl` when composing it there. The argument accepts only
`glibc` or `musl` and chooses the corresponding build stage; only that stage is
included in the mixin.
Passing arguments to local source Kits requires Docker Sandboxes `sbx` 0.48.0
or newer. With older versions, Fedora's default glibc composition works, but
the Alpine musl override cannot be resolved for a local kit directory.

## Use OpenCode V2

The `opencode/` mixin requires `mise/`. It installs Node.js LTS and OpenCode
for the `agent` user during sandbox creation using:

```sh
mise use -g --tool-option 'allow_builds=["@opencode/cli"]' npm:@opencode/cli
```

```sh
sbx run ./alpine --kit ./mise --kit-arg libc=musl --kit ./opencode
# Include the LiteLLM deployment:
sbx run ./alpine --kit ./mise --kit-arg libc=musl --kit ./litellm --kit ./opencode
# Fedora uses the default glibc variant:
sbx run ./fedora --kit ./mise --kit ./litellm --kit ./opencode
```

Inside the sandbox, run `opencode`. In noninteractive shells, use
`mise exec -- opencode --version` or `mise exec -- opencode`.

When `LITELLM_BASE_URL` is nonempty, the startup hook configures the V2
`litellm` provider and
[`opencode-plugin-litellm@latest`](https://github.com/yuseferi/opencode-litellm/)
for dynamic model discovery. It normalizes the endpoint to end in `/v1`.
Model names remain raw LiteLLM IDs: setup disables formatting in both provider
settings and plugin options so the setting also applies during V2's initial
discovery. Existing plugin version pins and unrelated options are preserved.
No secret check or authentication probe is performed. Store the host-side
`licht-moe-litellm` secret as described below; the existing LiteLLM mixin
injects authentication through the proxy without exposing the key to OpenCode.
Without `LITELLM_BASE_URL`, no OpenCode configuration is written.

Setup merges into `~/.config/opencode/opencode.json` (or under
`XDG_CONFIG_HOME`), preserving unrelated settings and curated models. Existing
JSONC files are left untouched; if `opencode.json` itself contains comments or
trailing commas, setup skips it with a warning instead of failing startup.
Installation permits the npm registry and
Node.js download hosts; runtime npm access allows OpenCode to load plugins.

## Use Pi

The `pi/` mixin requires `mise/`. It installs Pi with `mise use -g pi`, Node.js
LTS for npm package installation, and the `pi-provider-litellm` package, which
dynamically discovers models from the configured LiteLLM proxy.

```sh
sbx run ./alpine --kit ./mise --kit-arg libc=musl --kit ./litellm --kit ./pi
# Fedora uses the default glibc variant:
sbx run ./fedora --kit ./mise --kit ./litellm --kit ./pi
```

Inside the sandbox, run `pi`. In noninteractive shells, use
`mise exec -- pi --version` or `mise exec -- pi`. The extension uses
`LITELLM_BASE_URL` from the LiteLLM mixin to discover configured models; runtime
access is permitted to `llm.licht.moe`, while the npm registry is allowed only
during installation. Store the host-side
`licht-moe-litellm` secret as described in
[Use the LiteLLM deployment](#use-the-litellm-deployment). The Pi mixin sets
`LITELLM_API_KEY=proxy-managed` so the extension can discover models. This is
only a placeholder; the sandbox proxy injects the host-side secret into
matching requests, so the real key is not exposed to Pi.

Pi is installed from GitHub releases with mise. The mixin installs the
extension using `pi install npm:pi-provider-litellm`. It requires access to
`registry.npmjs.org` during sandbox creation. The extension uses Pi's native
provider and model picker; run `/model` to select discovered LiteLLM models.
The LiteLLM mixin's host-side credential proxy provides authentication without
placing the real API key in the sandbox.

## Build the Alpine workload

The Alpine workload uses Alpine `3.24.2` as its build base. The `mise` mixin
uses Fedora 44 for the default glibc binary and Alpine `3.24.2` for the optional
musl binary.

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
and CA certificates), Docker Engine, CLI, Buildx and Compose, `libstdc++` for
Node.js musl binaries, and global mise settings to select those binaries
instead of compiling from source. mise is still installed separately by
`mise/`.

## Build the mise mixin

Build a v3 kit image with Docker Buildx:

```sh
docker buildx build ./mise -f ./mise/mise.yaml \
  --platform linux/amd64 -t mise-mixin:dev --load
```

To build an arm64 image, use `--platform linux/arm64` instead. The `libc`
argument defaults to `glibc`; the build runs only the selected libc-specific
stage and leaves installer autodetection enabled in that stage. To build a
musl variant for Alpine, add `--build-arg libc=musl` to the Buildx command.

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

## Use the LiteLLM deployment

The `litellm/` mixin configures OpenAI-compatible clients to use
`https://llm.licht.moe/v1`. Compose it with either workload and, optionally,
the mise mixin:

```sh
sbx run ./alpine --kit ./mise --kit-arg libc=musl --kit ./litellm
# Fedora uses the mixin's default glibc variant:
sbx run ./fedora --kit ./mise --kit ./litellm
```

Inside the sandbox, OpenAI-compatible SDKs can use `OPENAI_BASE_URL` without
extra client configuration. The mixin also sets `OPENAI_API_BASE` for clients
that use the legacy variable, and `LITELLM_BASE_URL` for LiteLLM-specific
integrations. For example, with the OpenAI Python SDK:

```python
from openai import OpenAI

client = OpenAI()  # reads OPENAI_BASE_URL and OPENAI_API_KEY from the environment
print(client.models.list())
```

The kit permits network access to `llm.licht.moe` and declares the
`licht-moe-litellm` credential service, allowing Docker Sandbox's host-side
proxy to inject its key as an `Authorization: Bearer` header for requests to
that host. Store your LiteLLM virtual key as the service secret on the host:

```sh
sbx secret set licht-moe-litellm
```

Enter the key at the interactive prompt and approve the kit's credential
request when prompted. With proxy-managed credentials, the real key stays on
the host; the sandbox gets no key in its environment. If the deployment does
not require authentication, the service is optional and you can run without a
stored secret.
The local kit directories can be passed directly to `sbx`; manually building
the kit images is not required for local use. To publish kits, push their
images to a registry and use the registry references.

## Build the Fedora workload

The Fedora workload uses Fedora 44 and Fedora's `moby-engine`, Docker CLI,
Buildx, and Compose packages. At sandbox creation, an install hook adds the
host-injected proxy CA to Fedora's system and Docker registry trust stores so
OpenCode, mise, and Docker use the same CA without shell or Docker-command
wrappers.

```sh
docker buildx build ./fedora -f ./fedora/fedora.yaml \
  --platform linux/amd64 -t fedora-workload:amd64 --load
```

Use `--platform linux/arm64` and a matching tag to build for arm64.
