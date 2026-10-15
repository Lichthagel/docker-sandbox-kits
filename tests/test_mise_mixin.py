from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class MiseMixinTests(unittest.TestCase):
    def test_mixin_installs_a_bash_activation_hook_for_agent(self):
        descriptor = (ROOT / "mise" / "mise.yaml").read_text(encoding="utf-8")
        dockerfile = (ROOT / "mise" / "mise.dockerfile").read_text(
            encoding="utf-8"
        )

        self.assertIn("com.docker.sandbox/lifecycle@1", descriptor)
        self.assertIn("[sh, /usr/local/share/mise/activate-bash.sh]", descriptor)
        self.assertIn("user: agent", descriptor)
        self.assertIn(
            "COPY activate-bash.sh /usr/local/share/mise/activate-bash.sh",
            dockerfile,
        )

    def test_activation_hook_appends_mise_to_existing_bashrc_once(self):
        script = ROOT / "mise" / "activate-bash.sh"
        self.assertTrue(script.is_file())

        shell = shutil.which("sh")
        if shell is None:
            self.skipTest("requires a POSIX shell")

        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            bashrc = home / ".bashrc"
            bashrc.write_text("export KEEP_ME=yes\n", encoding="utf-8")
            env = os.environ.copy()
            env["HOME"] = str(home)

            for _ in range(2):
                result = subprocess.run(
                    [shell, str(script)], capture_output=True, text=True, env=env
                )
                self.assertEqual(result.returncode, 0, result.stderr)

            self.assertEqual(
                bashrc.read_text(encoding="utf-8"),
                'export KEEP_ME=yes\neval "$(mise activate bash)"\n',
            )

    def test_libc_argument_defaults_to_glibc_and_accepts_both_variants(self):
        descriptor = (ROOT / "mise" / "mise.yaml").read_text(encoding="utf-8")

        self.assertIn("  libc:\n", descriptor)
        self.assertIn('    default: "glibc"', descriptor)
        self.assertIn('    enum: ["glibc", "musl"]', descriptor)
        self.assertIn("    buildArg: MISE_LIBC", descriptor)

    def test_installer_builds_only_the_selected_libc_variant(self):
        dockerfile = (ROOT / "mise" / "mise.dockerfile").read_text(
            encoding="utf-8"
        )

        self.assertIn("FROM alpine:3.24.2 AS build-musl", dockerfile)
        self.assertIn("FROM fedora:44 AS build-glibc", dockerfile)
        self.assertIn("ARG MISE_LIBC=glibc\n\nFROM alpine:3.24.2", dockerfile)
        self.assertIn("FROM build-${MISE_LIBC} AS selected", dockerfile)
        self.assertIn("COPY --from=selected", dockerfile)
        self.assertNotIn("MISE_INSTALL_MUSL", dockerfile)

    def test_readme_explicitly_selects_musl_for_alpine(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("--kit-arg libc=musl", readme)
        self.assertIn("defaults to `glibc`", readme)
        self.assertIn("--build-arg libc=musl", readme)


if __name__ == "__main__":
    unittest.main()
