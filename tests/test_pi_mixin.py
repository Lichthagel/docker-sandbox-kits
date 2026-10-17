from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PiMixinTests(unittest.TestCase):
    def test_kit_installs_pi_for_the_agent_using_mise(self):
        descriptor = (ROOT / "pi" / "pi.yaml").read_text(encoding="utf-8")

        self.assertIn('displayName: Pi', descriptor)
        self.assertIn("requires: [mise]", descriptor)
        self.assertLess(
            descriptor.index("command: [mise, use, -g, node@lts]"),
            descriptor.index("command: [mise, use, -g, pi]"),
        )
        install_commands = [
            "command: [mise, exec, --, pi, install, npm:pi-provider-litellm]",
            "command: [mise, exec, --, pi, install, npm:pi-subagents]",
            "command: [mise, exec, --, pi, install, npm:pi-web-access]",
        ]
        positions = [descriptor.index(command) for command in install_commands]
        self.assertGreater(
            positions[0], descriptor.index("command: [mise, use, -g, pi]")
        )
        self.assertEqual(positions, sorted(positions))
        self.assertIn("user: agent", descriptor)

    def test_network_policy_allows_pi_install_and_catalog_access(self):
        descriptor = (ROOT / "pi" / "pi.yaml").read_text(encoding="utf-8")

        self.assertIn("github.com", descriptor)
        self.assertIn("api.github.com", descriptor)
        self.assertIn("release-assets.githubusercontent.com", descriptor)
        self.assertIn("unofficial-builds.nodejs.org", descriptor)
        self.assertIn("nodejs.org", descriptor)
        self.assertIn("pi.dev", descriptor)
        self.assertIn("registry.npmjs.org", descriptor)
        self.assertIn("runtime:\n        allow: [pi.dev, llm.licht.moe]", descriptor)

    def test_pi_uses_a_proxy_managed_placeholder_for_litellm_auth(self):
        dockerfile = (ROOT / "pi" / "pi.dockerfile").read_text(encoding="utf-8")

        self.assertIn("LITELLM_API_KEY=proxy-managed", dockerfile)

    def test_readme_documents_pi_with_litellm_on_both_workloads(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn(
            "sbx run ./alpine --kit ./mise-musl --kit ./litellm --kit ./pi",
            readme,
        )
        self.assertIn(
            "sbx run ./fedora --kit ./mise --kit ./litellm --kit ./pi", readme
        )
        self.assertIn("mise exec -- pi --version", readme)
        self.assertIn("pi-provider-litellm", readme)
        self.assertIn("pi-subagents", readme)
        self.assertIn("pi-web-access", readme)


if __name__ == "__main__":
    unittest.main()
