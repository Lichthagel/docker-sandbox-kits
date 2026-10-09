import os
from pathlib import Path
import subprocess
import unittest
import uuid


@unittest.skipUnless(
    os.environ.get("RUN_SBX_INTEGRATION") == "1",
    "set RUN_SBX_INTEGRATION=1 to create a Docker Sandbox",
)
class AlpineSandboxIntegrationTests(unittest.TestCase):
    def test_private_docker_engine_buildx_and_compose(self):
        root = Path(__file__).resolve().parents[1]
        sandbox = f"alpine-docker-test-{uuid.uuid4().hex[:10]}"

        try:
            create = subprocess.run(
                ["sbx", "run", "--name", sandbox, "--detached", str(root / "alpine")],
                cwd=root,
                capture_output=True,
                check=False,
                text=True,
                timeout=300,
            )
            self.assertEqual(create.returncode, 0, create.stdout + create.stderr)
            self.assertNotIn(
                "Tini is not running as PID 1",
                create.stdout + create.stderr,
            )

            smoke = subprocess.run(
                [
                    "sbx",
                    "exec",
                    sandbox,
                    "sh",
                    "-lc",
                    "set -eu; "
                    "docker info --format '{{.ServerVersion}}'; "
                    "docker buildx version; "
                    "docker compose version; "
                    "docker run --rm hello-world; "
                    "printf 'FROM alpine:3.24.2\\nCMD [\"echo\", \"Docker build works\"]\\n' "
                    "| docker build -t alpine-engine-build-test -; "
                    "docker run --rm alpine-engine-build-test; "
                    "printf 'services:\\n  hello:\\n    image: hello-world\\n' "
                    "| docker compose -f - run --rm hello",
                ],
                cwd=root,
                capture_output=True,
                check=False,
                text=True,
                timeout=600,
            )
            self.assertEqual(smoke.returncode, 0, smoke.stdout + smoke.stderr)
            self.assertNotIn(
                "Tini is not running as PID 1",
                smoke.stdout + smoke.stderr,
            )
            self.assertIn("Hello from Docker!", smoke.stdout)
            self.assertIn("Docker build works", smoke.stdout)
        finally:
            subprocess.run(
                ["sbx", "rm", "--force", sandbox],
                cwd=root,
                capture_output=True,
                check=False,
                text=True,
                timeout=120,
            )
