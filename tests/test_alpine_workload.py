from pathlib import Path
import re
import unittest


class AlpineWorkloadTests(unittest.TestCase):
    def test_descriptor_declares_v3_sbx_workload(self):
        text = Path("alpine/alpine.yaml").read_text(encoding="utf-8")
        self.assertTrue(text.startswith('# syntax=docker/sandbox-kit:3\n'))
        self.assertIn('schemaVersion: "3"', text)
        self.assertIn("kind: workload", text)
        self.assertIn(
            "capabilities:\n  - type: com.docker.sandbox/sbx@1\n", text
        )
        self.assertNotIn("config:", text)
        self.assertNotIn("network:", text)
        self.assertNotIn("credentials:", text)

    def test_mise_defaults_to_official_installer_latest(self):
        descriptor = Path("mise/mise.yaml").read_text(encoding="utf-8")
        dockerfile = Path("mise/mise.dockerfile").read_text(encoding="utf-8")
        readme = Path("README.md").read_text(encoding="utf-8")

        self.assertIn('default: ""', descriptor)
        self.assertIn("buildArg: MISE_VERSION", descriptor)
        self.assertIn("pattern: '^([0-9]+\\.[0-9]+\\.[0-9]+)?$'", descriptor)
        self.assertNotIn("provides:", descriptor)
        self.assertIn("FROM alpine:3.24.2 AS build", dockerfile)
        self.assertIn('MISE_VERSION="${MISE_VERSION:+v$MISE_VERSION}"', dockerfile)
        self.assertIn("latest eligible stable mise release", readme)
        self.assertIn("at kit build time", readme)
        self.assertIn("3.24.2", readme)
        self.assertNotIn("pins mise", readme)

    def test_dockerfile_has_minimal_agent_environment(self):
        text = Path("alpine/alpine.dockerfile").read_text(encoding="utf-8")
        self.assertIn("FROM alpine:3.24.2\n", text)
        self.assertIn(
            "RUN apk add --no-cache bash git curl ca-certificates \\", text
        )
        self.assertIn("adduser -D -u 1000", text)
        self.assertIn("addgroup -g 1000", text)
        self.assertIn("-s /bin/bash -h /home/agent agent", text)
        self.assertIn("mkdir -p /home/agent/workspace", text)
        self.assertIn("chown -R agent:agent /home/agent", text)
        self.assertIn("USER agent", text)
        self.assertIn("WORKDIR /home/agent/workspace", text)
        self.assertIn('ENTRYPOINT ["bash"]', text)
        self.assertIn("CMD []", text)
        self.assertNotIn("mise", text.lower())

    def test_readme_uses_local_workload_and_mixin(self):
        text = Path("README.md").read_text(encoding="utf-8")
        self.assertIn("sbx run ./alpine --kit ./mise", text)
        self.assertIn("mise --version", text)
        self.assertIn("--platform linux/amd64", text)
        self.assertIn("--platform linux/arm64", text)
        self.assertIn("alpine-workload:amd64", text)
        self.assertIn("alpine-workload:arm64", text)

    def test_readme_uses_default_branch_github_kit_references(self):
        text = Path("README.md").read_text(encoding="utf-8")
        source = r"git\+https://github\.com/Lichthagel/docker-sandbox-kits\.git#dir="

        self.assertRegex(text, source + "alpine")
        self.assertRegex(text, source + "mise")
        self.assertNotIn("#ref=", text)


if __name__ == "__main__":
    unittest.main()
