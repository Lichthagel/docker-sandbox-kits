from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class MiseMixinTests(unittest.TestCase):
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
