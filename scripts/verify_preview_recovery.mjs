/** Ubuntu-only, no-API-mock recovery check for the explicit local preview L2. */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";

const { values } = parseArgs({ options: {
  "l2-pid": { type: "string" }, "data-dir": { type: "string" },
  "web-port": { type: "string", default: "13200" },
  "l2-port": { type: "string", default: "18230" },
  report: { type: "string" },
} });
const pid = Number(values["l2-pid"]);
const webPort = Number(values["web-port"]);
const l2Port = Number(values["l2-port"]);
if (!Number.isSafeInteger(pid) || pid <= 1 || !values["data-dir"] ||
    ![webPort, l2Port].every(port => Number.isInteger(port) && port >= 1024 && port <= 65535)) {
  throw new Error("Provide --l2-pid, --data-dir and valid unprivileged local ports");
}
const command = fs.readFileSync(`/proc/${pid}/cmdline`, "utf8").split("\0");
const environment = new Set(fs.readFileSync(`/proc/${pid}/environ`, "utf8").split("\0"));
const database = `L2_DATABASE_URL=sqlite:///${path.resolve(values["data-dir"], "l2.db")}`;
if (!command.includes("judgment_graph.scripts.run_http") || !environment.has(database) ||
    !environment.has(`L2_HTTP_PORT=${l2Port}`) || !environment.has("L2_HTTP_HOST=127.0.0.1") ||
    !environment.has("L2_PROCESSING_MODE=heuristic")) {
  throw new Error("Refusing to signal a process other than this explicit loopback preview L2");
}
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(root, "pickblog/apps/reader-web/package.json"));
const { chromium, expect } = require("@playwright/test");
let paused = false;
const resume = () => { if (paused) { process.kill(pid, "SIGCONT"); paused = false; } };
for (const signal of ["SIGINT", "SIGTERM"]) {
  process.on(signal, () => { resume(); process.exit(1); });
}
const browser = await chromium.launch({
  ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ?
    { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH } : {}),
});
try {
  const base = `http://127.0.0.1:${webPort}`;
  const page = await browser.newPage();
  page.on("pageerror", error => console.error("Browser pageerror:", error.message));
  await page.goto(`${base}/en`);
  await expect(page.getByRole("heading", { name: "Public picks" })).toBeVisible();
  const title = await page.getByRole("article").first().getByRole("heading").innerText();
  process.kill(pid, "SIGSTOP");
  paused = true;
  await page.goto(`${base}/en?acceptance=recovery`, { timeout: 60_000 });
  await expect(page.getByRole("heading", { name: "The content service did not respond" })).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("No demonstration articles were substituted.")).toBeVisible();
  await expect(page.getByRole("article")).toHaveCount(0);
  resume();
  const health = await fetch(`${base}/api/feed?limit=1`, { signal: AbortSignal.timeout(15_000) });
  if (!health.ok) throw new Error(`Restored API not ready: ${health.status}`);
  // Deliberately click the same error page: a fresh page.goto would hide a broken Retry.
  await page.getByRole("button", { name: /Retry/ }).click();
  await expect(page.getByRole("heading", { name: "Public picks" })).toBeVisible({ timeout: 30_000 });
  await expect(page.getByRole("article").filter({ hasText: title })).toBeVisible();
  const report = {
    status: "PASS", recorded_at: new Date().toISOString(), api_mock: false,
    checks: ["initial real article", "paused L2 shows retryable error", "no demo substitution", "restored L2", "same-page Retry reads real article"],
  };
  if (values.report) fs.writeFileSync(values.report, JSON.stringify(report, null, 2) + "\n");
  console.log("REAL PREVIEW RECOVERY: PASS (SIGSTOP -> error -> SIGCONT -> same-page Retry)");
} finally {
  resume();
  await browser.close();
}
