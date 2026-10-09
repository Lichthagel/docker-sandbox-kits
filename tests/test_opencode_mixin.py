import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[1]


class OpenCodeMixinTests(unittest.TestCase):
    def configure(self, directory, base_url=None):
        script = ROOT / "opencode" / "configure-litellm.cjs"
        self.assertTrue(script.is_file(), "LiteLLM setup script is missing")
        env = os.environ.copy()
        env.pop("LITELLM_BASE_URL", None)
        env["XDG_CONFIG_HOME"] = str(directory)
        if base_url is not None:
            env["LITELLM_BASE_URL"] = base_url
        return subprocess.run(
            ["node", str(script)], env=env, capture_output=True, text=True
        )

    def test_no_provider_config_without_base_url(self):
        for value in (None, ""):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as temp:
                result = self.configure(Path(temp), value)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertFalse((Path(temp) / "opencode").exists())

    def test_provider_uses_v1_endpoint_without_a_secret(self):
        for url in ("https://llm.licht.moe", "https://llm.licht.moe/v1/"):
            with self.subTest(url=url), tempfile.TemporaryDirectory() as temp:
                result = self.configure(Path(temp), url)
                self.assertEqual(result.returncode, 0, result.stderr)
                config = json.loads(
                    (Path(temp) / "opencode" / "opencode.json").read_text()
                )
                self.assertEqual(config["plugins"], ["opencode-plugin-litellm@latest"])
                self.assertEqual(config["providers"]["litellm"], {
                    "name": "LiteLLM (proxy)",
                    "package": "@opencode/ai/providers/openai-compatible",
                    "settings": {"baseURL": "https://llm.licht.moe/v1"},
                })

    def test_repeated_setup_preserves_other_settings_and_curated_models(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp) / "opencode"
            directory.mkdir()
            path = directory / "opencode.json"
            path.write_text(json.dumps({
                "model": "other/model",
                "plugins": ["other-plugin"],
                "providers": {"litellm": {"models": {"custom": {}}}},
            }))
            for _ in range(2):
                result = self.configure(Path(temp), "https://llm.licht.moe")
                self.assertEqual(result.returncode, 0, result.stderr)
            config = json.loads(path.read_text())
            self.assertEqual(config["model"], "other/model")
            self.assertEqual(config["plugins"], ["other-plugin", "opencode-plugin-litellm@latest"])
            self.assertEqual(config["providers"]["litellm"]["models"], {"custom": {}})

    def test_jsonc_content_is_preserved_without_failing_startup(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp) / "opencode"
            directory.mkdir()
            path = directory / "opencode.json"
            original = '{\n// User configuration\n"model": "other/model",\n}\n'
            path.write_text(original)
            result = self.configure(Path(temp), "https://llm.licht.moe")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(path.read_text(), original)
            self.assertIn("LiteLLM setup skipped", result.stderr)


@unittest.skipUnless(
    os.environ.get("RUN_SBX_INTEGRATION") == "1",
    "set RUN_SBX_INTEGRATION=1 to create a Docker Sandbox",
)
class OpenCodeSandboxIntegrationTests(unittest.TestCase):
    def test_install_and_conditional_litellm_setup(self):
        sandbox = f"opencode-test-{uuid.uuid4().hex[:10]}"
        try:
            create = subprocess.run(
                ["sbx", "run", str(ROOT / "alpine"), "--kit", str(ROOT / "mise"),
                 "--kit", str(ROOT / "opencode"), "--name", sandbox, "--detached"],
                capture_output=True, text=True, timeout=300,
            )
            self.assertEqual(create.returncode, 0, create.stdout + create.stderr)
            smoke = subprocess.run(
                ["sbx", "exec", sandbox, "sh", "-lc",
                 "set -eu; mise exec -- opencode --version; "
                 "test ! -f /home/agent/.config/opencode/opencode.json; "
                 "LITELLM_BASE_URL=https://llm.licht.moe mise exec -- node "
                 "/usr/local/share/opencode-kit/configure-litellm.cjs; "
                 "cat /home/agent/.config/opencode/opencode.json"],
                capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(smoke.returncode, 0, smoke.stdout + smoke.stderr)
            self.assertIn("opencode v2.", smoke.stdout)
            self.assertIn('"baseURL": "https://llm.licht.moe/v1"', smoke.stdout)
        finally:
            subprocess.run(
                ["sbx", "rm", "--force", sandbox],
                capture_output=True, text=True, timeout=120,
            )


if __name__ == "__main__":
    unittest.main()
