# mise Docker Sandbox Mixin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a minimal Docker Sandbox v3 mixin that adds an Alpine/musl-compatible `mise` executable to an existing Alpine-based workload, defaulting to the official installer's latest eligible stable release.

**Architecture:** Author a v3 YAML mixin descriptor and matching Dockerfile in `mise/`. Use an Alpine build stage and the official `mise.run` installer to obtain its static musl executable, then copy only the executable into a minimal final stage so the mixin does not overlay the workload's OS or replace its launch configuration. Default to the installer's latest eligible stable release, with an optional build-time version override. Document how to build and attach the local mixin to a compatible Alpine-based v3 workload.

**Tech Stack:** Docker Sandbox Kit v3 frontend, Docker Buildx, Alpine Linux 3.24.2, `mise`.

**Spec:** `docs/superpowers/specs/2026-10-07-alpine-mise-sandbox-design.md`

## Global Constraints

- The kit is a Docker Sandbox v3 `mixin`, not a standalone workload image.
- Target an Alpine-based workload and verify the `mise` executable works with musl.
- Do not add a sample project, `.mise.toml`, or other development tools.
- The mixin must not replace the workload's base image or launch command.
- Do not include build-stage installer dependencies in the mixin overlay.
- Use a Docker Sandbox v3 descriptor with a matching `<stem>.dockerfile`.

## Review Focus

- **Non-Alpine/musl target:** Scope and documentation must make clear that the intended target is Alpine/musl; no claim of general glibc compatibility.
- **Architecture mismatch:** Buildx should build for the requested platform so the installer selects a supported matching musl binary; validate both `linux/amd64` and `linux/arm64` builds.
- **Overlay contamination:** The final mixin layer should add only the `mise` executable, not overwrite system files from its build-stage base.
- **PATH availability:** Verify documented invocation resolves `mise` in the workload. Install at `/usr/local/bin/mise` and confirm it is on Alpine's standard PATH.
- **Runtime side effects:** Mixin must not redefine entrypoint, command, user, or workdir; only the executable is contributed.

---

### Task 1: Author and verify the mise mixin

**Files:**
- Create: `mise/mise.yaml`
- Create: `mise/mise.dockerfile`
- Create: `README.md`

**Interfaces:**
- Consumes: Docker Sandbox v3 kit descriptor contract and the official `mise.run` installer with its musl build option.
- Produces: Local kit directory `./mise`, usable as a local source via `sbx run <alpine-v3-workload-ref> --kit ./mise`; installed executable at `/usr/local/bin/mise` in an Alpine-based workload.

- [x] **Step 1: Create the v3 mixin descriptor**

The current descriptor defaults the optional build-time version override to empty so the official installer selects its latest eligible stable release; it omits `provides` because that version is resolved during the image build. Any explicit override remains constrained to a numeric dotted version.

- [x] **Step 2: Install the musl binary and create the minimal overlay**

Create `mise/mise.dockerfile` using `FROM alpine:3.24.2 AS build` with `curl` and CA certificates. Pass `MISE_VERSION` as an optional build arg from the descriptor; run the official `mise.run` installer with `MISE_INSTALL_MUSL=1`, an empty `MISE_VERSION` when no override is supplied (allowing latest-eligible resolution), a `v` prefix only for a non-empty override, and `MISE_INSTALL_PATH=/out/usr/local/bin/mise`. Use a `scratch` final stage to copy only that executable to `/usr/local/bin/mise`. Buildx's `--platform` option sets the build stage architecture so the installer selects the matching supported musl binary. Do not set `ENTRYPOINT`, `CMD`, `USER`, or `WORKDIR`.

- [x] **Step 3: Document build and use**

Create root `README.md` describing the Alpine/musl target, prerequisites (`sbx`, Docker, and Buildx), and exact command to attach the local source to an existing Alpine-based v3 workload using `sbx run <alpine-v3-workload-ref> --kit ./mise`. Show `mise --version` as the verification command. Clearly note this is a mixin, not a standalone image, and avoid claiming support for glibc workloads. Explain that the installer selects its latest eligible stable mise release by default, and that optional version overrides are build-time rather than sandbox-creation arguments. Document amd64 and arm64 platform examples.

- [x] **Step 4: Build the kit**

Run for each supported architecture:

```sh
docker buildx build --platform linux/amd64 --load -f mise/mise.yaml -t mise-mixin:amd64 mise/
docker buildx build --platform linux/arm64 --load -f mise/mise.yaml -t mise-mixin:arm64 mise/
```

Expected: successful v3 kit validation and image build for both target architectures. **Verified:** Buildx completed for amd64 and arm64. Direct `sbx kit validate` cannot build the local v3 source in the current load path; `sbx run` successfully built it through the source-kit builder.

The descriptor uses the `docker/sandbox-kit:3` BuildKit frontend, which is separate from the downloaded `mise` executable. Docker emitted `RedundantTargetPlatform` while the original Dockerfile used `FROM --platform=$TARGETPLATFORM`; this was removed because BuildKit already builds `FROM` stages for the requested target platform.

- [x] **Step 5: Verify the mixin image contents and binary**

Run the matching locally loaded image tag for the host architecture, for example: `docker run --rm --entrypoint /usr/local/bin/mise mise-mixin:amd64 --version`.

Expected: the executable starts and reports the version selected by the installer on the host architecture. Inspect the image filesystem/layers to confirm the mixin contributes the executable and kit metadata only, with no build dependencies or replacement runtime config. If the image is scratch-based, a direct `docker run` may not work because the image has no shell/config; use an ephemeral Alpine test image that copies the artifact's binary, or rely on the Sandbox composition smoke test. **Verified before latest-default change:** both architecture images reported the then-pinned mise version; amd64 image config had no entrypoint, cmd, user, or non-root workdir, and history showed only the binary layer plus kit metadata. **Reverified:** latest-default builds for amd64 and arm64 selected and ran mise `2026.10.3` (the latest eligible release during verification).

- [x] **Step 6: Verify in an Alpine-based v3 workload**

Run using `sbx` and a compatible Alpine-based v3 workload: `sbx run <alpine-v3-workload-ref> --kit ./mise`; then run `mise --version` inside the composed sandbox.

Expected: the command succeeds and reports the installed version; existing workload launch behavior remains intact. If no compatible Alpine-based v3 workload is available in the environment, record this composition smoke test as unavailable rather than substituting an incompatible workload. `docker run` alone does not apply mixin composition and is not a valid verification of the kit. **Verified before the latest-default change:** a temporary Alpine v3 workload composed with the local mixin and `sbx exec ... mise --version` printed `2026.10.3`; the temporary sandbox was removed afterward. **Reverified with latest-default behavior:** the composed Alpine workload reported `2026.10.3`; the temporary sandbox was removed.

- [x] **Step 7: Review files against the spec**

Confirm the descriptor is v3 and `kind: mixin`, the Dockerfile overlay only contributes the executable, README commands match Docker's documented Buildx/mixin flow, and no sample project or unrelated tools were added. **Verified before latest-default change:** independent review found no Critical, Important, or Minor issues. It recommended platform-specific examples, which are included in the README. **Reverified:** static regression tests pass (4/4); both platform builds and the default-version sandbox smoke test passed.
