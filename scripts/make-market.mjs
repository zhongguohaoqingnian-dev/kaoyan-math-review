/**
 * Regenerate market.json (plugin market index format 1) from package.json + git.
 *
 * Usage:
 *   node scripts/make-market.mjs                 # git source, pinned to HEAD
 *   node scripts/make-market.mjs --source npm    # npm source (after npm publish)
 *
 * The index is served from GitHub Pages, so it must be regenerated (and pushed)
 * for every release: the `version` and `publishTimestamp` come from here.
 */
import { execFileSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";

const args = process.argv.slice(2);
const flag = (name, fallback) => {
  const at = args.indexOf("--" + name);
  return at >= 0 && args[at + 1] ? args[at + 1] : fallback;
};

const pkg = JSON.parse(readFileSync("package.json", "utf8"));
const sourceType = flag("source", "git");
if (sourceType !== "git" && sourceType !== "npm") {
  console.error("--source must be git or npm");
  process.exit(1);
}

const repoField = typeof pkg.repository === "string" ? pkg.repository : pkg.repository?.url ?? "";
const match = /github\.com[/:]([^/]+)\/([^/#.]+)(?:\.git)?/.exec(repoField);
if (!match) {
  console.error("package.json repository must point at a GitHub repo");
  process.exit(1);
}
const [, owner, repo] = match;
const repoUrl = `https://github.com/${owner}/${repo}`;

let source;
if (sourceType === "npm") {
  source = { type: "npm" };
} else {
  const commit = execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim();
  if (!/^[0-9a-f]{40}$/.test(commit)) {
    console.error("cannot read a commit SHA; commit first");
    process.exit(1);
  }
  source = { type: "git", url: repoUrl, commit };
}

const index = {
  format: 1,
  title: { en: "Yanshu · Kaoyan Math market", zh: "研数 · 考研数学插件市场" },
  description: {
    en: "Kaoyan Math I review plugin for DeepSeek Harness with Math I & II past papers.",
    zh: "在 DeepSeek Harness 里复习考研数学的插件。",
  },
  metadata: {
    categories: { study: { title: { en: "Study", zh: "学习" } } },
    labels: { math: { title: { en: "Math", zh: "数学" } } },
  },
  plugins: [
    {
      name: pkg.name,
      title: { en: "Yanshu · Kaoyan Math Review", zh: "研数 · 考研数学复习" },
      description: {
        en: pkg.description,
        zh: "数一复习视图：21 章 132 个考点、数一/数二 2011–2026 真题与做题日历。",
      },
      icon: "./icon.svg",
      author: pkg.author,
      homepage: pkg.homepage,
      repository: { url: repoUrl },
      metadata: {
        category: "study",
        keywords: pkg.keywords ?? [],
        labels: ["math"],
      },
      versions: [
        {
          version: pkg.version,
          publishTimestamp: Math.floor(Date.now() / 1000),
          source,
          engines: pkg.engines?.dsh ? { dsh: pkg.engines.dsh } : {},
        },
      ],
    },
  ],
};

writeFileSync("market.json", JSON.stringify(index, null, 2) + "\n");
console.log(`market.json: ${pkg.name}@${pkg.version} via ${sourceType}`);
