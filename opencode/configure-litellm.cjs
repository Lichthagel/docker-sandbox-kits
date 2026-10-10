const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const baseURL = process.env.LITELLM_BASE_URL;
if (!baseURL) process.exit(0);

const directory = path.join(
  process.env.XDG_CONFIG_HOME || path.join(os.homedir(), ".config"),
  "opencode",
);
const filename = path.join(directory, "opencode.json");
let config = {};
if (fs.existsSync(filename)) {
  const content = fs.readFileSync(filename, "utf8");
  try {
    config = JSON.parse(content);
  } catch (error) {
    if (!(error instanceof SyntaxError)) throw error;
    console.warn(`LiteLLM setup skipped: ${filename} is not strict JSON; configure the provider and plugin manually.`);
    process.exit(0);
  }
}

config.$schema ??= "https://opencode.ai/config.json";
config.plugins ??= [];
let hasLiteLLMPlugin = false;
config.plugins = config.plugins.map((entry) => {
  const name = typeof entry === "string" ? entry : entry.package;
  if (name !== "opencode-plugin-litellm" && !name.startsWith("opencode-plugin-litellm@")) {
    return entry;
  }
  hasLiteLLMPlugin = true;
  const plugin = typeof entry === "string" ? { package: entry } : entry;
  // Initial discovery can run before provider settings are available in V2.
  return { ...plugin, options: { ...plugin.options, formatModelNames: false } };
});
if (!hasLiteLLMPlugin) {
  config.plugins.push({
    package: "opencode-plugin-litellm@latest",
    options: { formatModelNames: false },
  });
}
config.providers ??= {};
const provider = config.providers.litellm ??= {};
provider.name ??= "LiteLLM";
provider.package ??= "@opencode/ai/providers/openai-compatible";
provider.settings ??= {};
const endpoint = baseURL.replace(/\/+$/, "");
provider.settings.baseURL = endpoint.endsWith("/v1") ? endpoint : `${endpoint}/v1`;
provider.settings.formatModelNames = false;

fs.mkdirSync(directory, { recursive: true });
fs.writeFileSync(filename, `${JSON.stringify(config, null, 2)}\n`);
