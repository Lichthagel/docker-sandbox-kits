import os
from pathlib import Path
import subprocess
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[1]


class FedoraWorkloadTests(unittest.TestCase):
    def test_descriptor_declares_v3_sbx_workload(self):
        descriptor = (ROOT / "fedora" / "fedora.yaml").read_text(encoding="utf-8")

        self.assertTrue(descriptor.startswith('# syntax=docker/sandbox-kit:3\n'))
        self.assertIn('schemaVersion: "3"', descriptor)
        self.assertIn("kind: workload", descriptor)
        self.assertIn("type: com.docker.sandbox/sbx@1", descriptor)

    def test_dockerfile_provides_the_agent_and_private_docker_environment(self):
        dockerfile = (ROOT / "fedora" / "fedora.dockerfile").read_text(
            encoding="utf-8"
        )

        self.assertIn("FROM fedora:44", dockerfile)
        for package in (
            "bash",
            "ca-certificates",
            "curl",
            "docker-buildx",
            "docker-compose",
            "docker-cli",
            "git",
            "git-daemon",
            "iptables-nft",
            "moby-engine",
            "sudo",
            "tini-static",
        ):
            with self.subTest(package=package):
                self.assertIn(package, dockerfile)
        self.assertIn("groupadd --gid 1000 agent", dockerfile)
        self.assertIn("useradd --uid 1000 --gid agent", dockerfile)
        self.assertIn("--groups docker", dockerfile)
        self.assertIn("agent ALL=(ALL) NOPASSWD: ALL", dockerfile)
        self.assertIn('LABEL com.docker.sandboxes.start-docker="true"', dockerfile)
        self.assertIn('ENTRYPOINT ["/usr/bin/tini-static", "-s", "--"]', dockerfile)
        self.assertIn('CMD ["bash"]', dockerfile)
        self.assertIn("docker-registry-ca", dockerfile)
        self.assertIn("COPY docker /usr/local/bin/docker", dockerfile)
        self.assertIn("USER agent", dockerfile)
        self.assertIn("WORKDIR /home/agent/workspace", dockerfile)
        self.assertIn("alternatives --set iptables /usr/sbin/iptables-nft", dockerfile)
        self.assertNotIn("apk add", dockerfile)
        self.assertNotIn("mise", dockerfile.lower())

    def test_bash_activates_mise(self):
        bashrc = (ROOT / "fedora" / "bashrc").read_text(encoding="utf-8")
        self.assertEqual(bashrc.strip(), 'eval "$(mise activate bash)"')

    def test_docker_registry_ca_installer_is_safe_without_proxy_ca(self):
        installer = (ROOT / "fedora" / "docker-registry-ca.sh").read_text(
            encoding="utf-8"
        )
        dockerfile = (ROOT / "fedora" / "fedora.dockerfile").read_text(
            encoding="utf-8"
        )
        self.assertIn('"${PROXY_CA_CERT_B64:-}"', installer)
        self.assertIn("/etc/docker/certs.d/docker.io/ca.crt", installer)
        self.assertIn("sudo install -m 0644", installer)
        self.assertIn(
            "chmod 0755 /usr/local/sbin/docker-registry-ca /usr/local/bin/docker",
            dockerfile,
        )
        wrapper = (ROOT / "fedora" / "docker").read_text(encoding="utf-8")
        self.assertIn("/usr/local/sbin/docker-registry-ca", wrapper)
        self.assertIn('exec /usr/bin/docker "$@"', wrapper)

    def test_readme_documents_fedora_and_libc_selection(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("sbx run ./fedora --kit ./mise", readme)
        self.assertIn("--kit-arg libc=musl", readme)
        self.assertIn("defaults to `glibc`", readme)
        self.assertIn(
            "sbx run ./fedora --kit ./mise --kit ./litellm --kit ./opencode",
            readme,
        )


@unittest.skipUnless(
    os.environ.get("RUN_SBX_INTEGRATION") == "1",
    "set RUN_SBX_INTEGRATION=1 to create a Docker Sandbox",
)
class FedoraSandboxIntegrationTests(unittest.TestCase):
    def test_private_docker_engine_buildx_and_compose(self):
        sandbox = f"fedora-docker-test-{uuid.uuid4().hex[:10]}"

        try:
            create = subprocess.run(
                ["sbx", "run", "--name", sandbox, "--detached", str(ROOT / "fedora")],
                cwd=ROOT,
                capture_output=True,
                check=False,
                text=True,
                timeout=300,
            )
            self.assertEqual(create.returncode, 0, create.stdout + create.stderr)

            smoke = subprocess.run(
                [
                    "sbx",
                    "exec",
                    sandbox,
                    "sh",
                    "-lc",
                    "set -eu; "
                    "id -u | grep -qx 1000; "
                    "test -w /home/agent/workspace; "
                    "docker info --format '{{.ServerVersion}}'; "
                    "docker buildx version; "
                    "docker compose version; "
                    "docker run --rm hello-world",
                ],
                cwd=ROOT,
                capture_output=True,
                check=False,
                text=True,
                timeout=600,
            )
            self.assertEqual(smoke.returncode, 0, smoke.stdout + smoke.stderr)
            self.assertIn("Hello from Docker!", smoke.stdout)
        finally:
            subprocess.run(
                ["sbx", "rm", "--force", sandbox],
                cwd=ROOT,
                capture_output=True,
                check=False,
                text=True,
                timeout=120,
            )


if __name__ == "__main__":
    unittest.main()
