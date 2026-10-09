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
// Do not add a second copy if the user has pinned or configured the plugin.
if (!config.plugins.some((entry) => {
  const name = typeof entry === "string" ? entry : entry.package;
  return name === "opencode-plugin-litellm" || name.startsWith("opencode-plugin-litellm@");
})) {
  config.plugins.push("opencode-plugin-litellm@latest");
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
