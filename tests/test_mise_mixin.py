from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class MiseMixinTests(unittest.TestCase):
    def test_mixin_installs_a_bash_activation_hook_for_agent(self):
        for kit in ("mise", "mise-musl"):
            with self.subTest(kit=kit):
                descriptor = (ROOT / kit / f"{kit}.yaml").read_text(
                    encoding="utf-8"
                )
                dockerfile = (ROOT / kit / f"{kit}.dockerfile").read_text(
                    encoding="utf-8"
                )

                self.assertIn("com.docker.sandbox/lifecycle@1", descriptor)
                self.assertIn(
                    "[sh, /usr/local/share/mise/activate-bash.sh]", descriptor
                )
                self.assertIn("user: agent", descriptor)
                self.assertIn(
                    "COPY activate-bash.sh /usr/local/share/mise/activate-bash.sh",
                    dockerfile,
                )

    def test_activation_hook_appends_mise_to_existing_bashrc_once(self):
        shell = shutil.which("sh")
        if shell is None:
            self.skipTest("requires a POSIX shell")

        for kit in ("mise", "mise-musl"):
            with self.subTest(kit=kit):
                script = ROOT / kit / "activate-bash.sh"
                self.assertTrue(script.is_file())

                with tempfile.TemporaryDirectory() as temp_dir:
                    home = Path(temp_dir)
                    bashrc = home / ".bashrc"
                    bashrc.write_text("export KEEP_ME=yes\n", encoding="utf-8")
                    env = os.environ.copy()
                    env["HOME"] = str(home)

                    for _ in range(2):
                        result = subprocess.run(
                            [shell, str(script)],
                            capture_output=True,
                            text=True,
                            env=env,
                        )
                        self.assertEqual(result.returncode, 0, result.stderr)

                    self.assertEqual(
                        bashrc.read_text(encoding="utf-8"),
                        'export KEEP_ME=yes\neval "$(mise activate bash)"\n',
                    )

    def test_mise_is_glibc_only(self):
        descriptor = (ROOT / "mise" / "mise.yaml").read_text(encoding="utf-8")
        dockerfile = (ROOT / "mise" / "mise.dockerfile").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("  libc:\n", descriptor)
        self.assertIn("FROM fedora:46 AS build", dockerfile)
        self.assertNotIn("FROM alpine:", dockerfile)
        self.assertNotIn("MISE_LIBC", dockerfile)
        self.assertIn("COPY --from=build", dockerfile)

    def test_mise_musl_is_a_separate_alpine_only_kit(self):
        descriptor = (ROOT / "mise-musl" / "mise-musl.yaml").read_text(
            encoding="utf-8"
        )
        dockerfile = (ROOT / "mise-musl" / "mise-musl.dockerfile").read_text(
            encoding="utf-8"
        )

        self.assertIn('provides: ["mise@1"]', descriptor)
        self.assertNotIn("  libc:\n", descriptor)
        self.assertIn("musl", descriptor.lower())
        self.assertIn("FROM alpine:3.24.2 AS build", dockerfile)
        self.assertNotIn("FROM fedora:", dockerfile)
        self.assertNotIn("MISE_LIBC", dockerfile)
        self.assertIn("COPY --from=build", dockerfile)

    def test_readme_uses_dedicated_libc_kits_for_each_workload(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("--kit ./mise-musl", readme)
        self.assertIn("--kit ./mise", readme)
        self.assertNotIn("--kit-arg libc=musl", readme)
        self.assertNotIn("--build-arg libc=musl", readme)


if __name__ == "__main__":
    unittest.main()
