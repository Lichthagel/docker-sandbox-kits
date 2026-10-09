from pathlib import Path
import unittest


class LiteLLMMixinTests(unittest.TestCase):
    def test_descriptor_declares_proxy_managed_litellm_service(self):
        descriptor = Path("litellm/litellm.yaml").read_text(encoding="utf-8")

        self.assertTrue(descriptor.startswith('# syntax=docker/sandbox-kit:3\n'))
        self.assertIn('schemaVersion: "3"', descriptor)
        self.assertIn("kind: mixin", descriptor)
        self.assertIn("type: com.docker.sandbox/network-policy@1", descriptor)
        self.assertIn("allow: [llm.licht.moe]", descriptor)
        self.assertIn("type: com.docker.sandbox/credential@1", descriptor)
        self.assertIn("service: licht-moe-litellm", descriptor)
        self.assertIn("phase: runtime", descriptor)
        self.assertIn('name: ""', descriptor)
        self.assertIn("proxyManaged: true", descriptor)
        self.assertIn("domain: llm.licht.moe", descriptor)
        self.assertIn("header: Authorization", descriptor)
        self.assertIn('format: "Bearer %s"', descriptor)

    def test_dockerfile_configures_litellm_openai_compatible_endpoint(self):
        dockerfile = Path("litellm/litellm.dockerfile").read_text(encoding="utf-8")

        self.assertIn("OPENAI_BASE_URL=https://llm.licht.moe/v1", dockerfile)
        self.assertIn("OPENAI_API_BASE=https://llm.licht.moe/v1", dockerfile)
        self.assertIn("LITELLM_BASE_URL=https://llm.licht.moe", dockerfile)
        self.assertNotIn("OPENAI_API_KEY", dockerfile)
        self.assertNotIn("LITELLM_API_KEY", dockerfile)

    def test_readme_documents_service_secret_and_authentication(self):
        readme = Path("README.md").read_text(encoding="utf-8")

        self.assertIn("sbx run ./alpine --kit ./mise --kit ./litellm", readme)
        self.assertIn("llm.licht.moe/v1", readme)
        self.assertIn("sbx secret set licht-moe-litellm", readme)
        self.assertIn("proxy-managed", readme)


if __name__ == "__main__":
    unittest.main()
