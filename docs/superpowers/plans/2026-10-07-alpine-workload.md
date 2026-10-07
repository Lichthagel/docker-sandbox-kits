# Alpine Docker Sandbox Workload Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a minimal, pinned Alpine 3.24.2 Docker Sandbox v3 workload to this project and document how to compose it with the existing `mise` mixin.

**Architecture:** Add a standalone `alpine/` v3 workload kit with a descriptor and matching Dockerfile. The workload installs only Sandbox prerequisites, runs as the required non-root `agent` user, and launches Bash; `mise` remains solely in the separate mixin. Update the README with local composition and verification instructions.

**Tech Stack:** Docker Sandbox Kit v3 frontend, Docker Buildx, Alpine Linux 3.24.2, `sbx`.

**Spec:** `docs/superpowers/specs/2026-10-07-alpine-workload-design.md`

## Global Constraints

- The workload is based on Alpine 3.24.2, pinned to the latest stable release at the time of the version update.
- The workload kit directory is `alpine/`, with `alpine.yaml` and `alpine.dockerfile`.
- The v3 workload descriptor declares `com.docker.sandbox/sbx@1` with no config.
- Install only `bash`, `git`, `curl`, and CA certificates as sandbox prerequisites.
- Create non-root `agent` with UID/GID 1000, home `/home/agent`, and workspace `/home/agent/workspace`.
- Set image `USER agent`, `WORKDIR /home/agent/workspace`, Bash entrypoint, and no default command arguments.
- The workload does not include mise, language runtimes, or other development tools; mise remains in its separate mixin.
- Do not request network access, credentials, or unrelated capabilities.

## Review Focus

- **Image identity:** Ensure `USER agent` resolves to UID/GID 1000 and an absolute `/home/agent` home in `/etc/passwd`; assert this in the workload smoke test.
- **Sandbox launch contract:** Ensure both `/bin/sh` and `/bin/bash` are executable and the descriptor claims `sbx@1`; validate kit build and launch through `sbx`.
- **Workspace usability:** Ensure `/home/agent/workspace` exists and is writable by `agent`; check it from the composed sandbox.
- **Mixin composition and version:** Ensure the workload does not provide or install `mise`, the `mise` mixin remains separate, and the composed sandbox reports the mixin's installer-selected version.
- **Architecture selection:** Build the workload and mixin together for amd64 and arm64 where the host Buildx builder supports them; verify the workload image targets the selected platform.

---

### Task 1: Add and document the Alpine workload

**Files:**
- Create: `tests/test_alpine_workload.py`
- Create: `alpine/alpine.yaml`
- Create: `alpine/alpine.dockerfile`
- Modify: `README.md`

**Interfaces:**
- Consumes: Docker Sandbox v3 `workload` descriptor and `com.docker.sandbox/sbx@1` contract; existing `./mise` mixin source.
- Produces: Local workload source `./alpine`, runnable with `sbx run ./alpine --kit ./mise`; interactive Bash as `agent` at `/home/agent/workspace` with mise selected at mixin build time and available on PATH.

- [x] **Step 1: Write static contract tests first**

Add Python standard-library `unittest` tests in `tests/test_alpine_workload.py`:

```python
def test_descriptor_declares_v3_sbx_workload():
    text = Path("alpine/alpine.yaml").read_text()
    assert text.startswith('# syntax=docker/sandbox-kit:3\n')
    assert 'schemaVersion: "3"' in text
    assert "kind: workload" in text
    assert "type: com.docker.sandbox/sbx@1" in text

def test_dockerfile_has_minimal_agent_environment():
    text = Path("alpine/alpine.dockerfile").read_text()
    assert "FROM alpine:3.24.2" in text
    for package in ("bash", "git", "curl", "ca-certificates"):
        assert package in text
    assert "adduser -D -u 1000" in text
    assert "addgroup -g 1000" in text
    assert "USER agent" in text
    assert "WORKDIR /home/agent/workspace" in text
    assert 'ENTRYPOINT ["bash"]' in text
    assert "CMD []" in text
    self.assertNotIn("mise", text.lower())

def test_readme_uses_local_workload_and_mixin():
    text = Path("README.md").read_text()
    self.assertIn("sbx run ./alpine --kit ./mise", text)
    self.assertIn("mise --version", text)
```

- [x] **Step 2: Run tests and verify they fail for missing workload kit**

Run: `py -3 -m unittest discover -s tests -v`

Expected: FAIL because the `alpine/` kit files do not yet exist (not a test import or syntax error).

- [x] **Step 3: Add the v3 workload descriptor**

Create `alpine/alpine.yaml` with the Docker Sandbox v3 syntax line, `schemaVersion: "3"`, `kind: workload`, display metadata describing a minimal Alpine Bash workload, and one config-less capability entry of `type: com.docker.sandbox/sbx@1`. Do not add `provides`, args, network rules, credentials, or other capabilities.

- [x] **Step 4: Add the minimal Alpine Dockerfile**

Create `alpine/alpine.dockerfile` based on `alpine:3.24.2`. Install `bash`, `git`, `curl`, and `ca-certificates` with `apk add --no-cache`; create group and user `agent` with GID/UID 1000, shell `/bin/bash`, home `/home/agent`; create and chown `/home/agent/workspace`; then set `USER agent`, `WORKDIR /home/agent/workspace`, `ENTRYPOINT ["bash"]`, and `CMD []`. Do not install mise or any other development runtimes/tools.

- [x] **Step 5: Update README for local composition and builds**

Replace the placeholder `<alpine-v3-workload-ref>` run example with `sbx run ./alpine --kit ./mise`. Explain that `alpine/` is the reusable minimal workload and `mise/` is a separate mixin. Keep `mise --version` verification and the existing build-time mise version override explanation. Document Buildx commands for both `linux/amd64` and `linux/arm64` builds of the Alpine workload kit, using `-f alpine/alpine.yaml` and build context `alpine/`.

- [x] **Step 6: Run static tests and build both workload architectures**

Run: `py -3 -m unittest discover -s tests -v`

Expected: all 3 tests PASS.

Run:

```sh
docker buildx build --platform linux/amd64 --load -f alpine/alpine.yaml -t alpine-workload:amd64 alpine/
docker buildx build --platform linux/arm64 --load -f alpine/alpine.yaml -t alpine-workload:arm64 alpine/
```

Expected: both v3 workload kit builds succeed. **Verified:** Buildx completed for linux/amd64 and linux/arm64; both images pass shell, user, and workspace contract checks.

- [x] **Step 7: Verify the composed sandbox runtime contract**

Run: `sbx run --detached --name alpine-mise-test ./alpine --kit ./mise`, then run the following in the sandbox:

```sh
id
getent passwd agent
test -x /bin/sh && test -x /bin/bash
test -w /home/agent/workspace
command -v mise
mise --version
```

Expected: effective identity is `agent` UID/GID 1000; passwd home is `/home/agent`; both shells are executable; workspace is writable; `mise` resolves to `/usr/local/bin/mise`; and `mise --version` succeeds. Remove the temporary sandbox after successful verification with `sbx rm --force alpine-mise-test`. **Verified before changing the default version behavior:** the composed sandbox reported the expected agent identity and mise version `2026.10.3`, and was removed. **Reverified:** after changing the defaults, the composed sandbox met the same runtime contract and reported installer-selected mise `2026.10.3`.

- [x] **Step 8: Review the kit and documentation against the spec**

Confirm `sbx@1` matches the built image, the workload contains only the four listed packages and no `mise`, the run command composes `./alpine` with `./mise`, and the README's build commands use valid descriptor/context paths for both platforms. **Verified:** independent review found no Critical or Important issues; it recommended stricter static assertions and plan tracking. Assertions were strengthened and execution checkboxes updated; final tests passed.
