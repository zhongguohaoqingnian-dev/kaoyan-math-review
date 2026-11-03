/**
 * Content checker for client.js.
 *
 * Loads the Client module's factory with a stubbed React, walks every content
 * string (SECTIONS + LINEAR), and runs the built-in TeX-ish parser over every
 * math fragment. Catches unbalanced $, unbalanced braces, bad environments and
 * command names the renderer does not know.
 *
 * Usage: node scripts/check-content.mjs
 */
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const file = resolve(here, "..", "client.js");
const source = readFileSync(file, "utf8");

const bodyStart = source.indexOf("factory(require) {");
const registration = source.lastIndexOf("6. Registration");
const registrationComment = source.lastIndexOf("/* ---", registration);
if (bodyStart < 0 || registration < 0 || registrationComment < 0) {
  console.error("client.js: cannot locate the factory body");
  process.exit(1);
}

const body = source.slice(bodyStart + "factory(require) {".length, registrationComment);

const reactStub = {
  createElement: (type, props, ...children) => ({ type, props, children }),
  Fragment: "Fragment",
  useMemo: (fn) => fn(),
  useState: (value) => [typeof value === "function" ? value() : value, () => {}],
  useRef: (value) => ({ current: value }),
  useEffect: () => {},
  useCallback: (fn) => fn,
};
reactStub.default = reactStub;

const requireStub = (name) => {
  if (name === "react") return reactStub;
  throw new Error("unexpected require: " + name);
};

const storageStub = {
  getItem: () => null,
  setItem: () => {},
  removeItem: () => {},
};
const windowStub = { localStorage: storageStub, setTimeout: () => 0, clearTimeout: () => {} };

const factory = new Function(
  "require",
  "window",
  body +
    "\n;return { SECTIONS, LINEAR, PROBABILITY, CALCULUS, POINTS, SUBJECTS, TREE, PAPERS, parseMath, SYMBOLS, PointCard, TreeNode, Panel };\n",
);

const api = factory(requireStub, windowStub);
const { SECTIONS, LINEAR, PROBABILITY, CALCULUS, POINTS, SUBJECTS, TREE, PAPERS, parseMath, PointCard, TreeNode, Panel } = api;

const CHAPTERS = { ...CALCULUS, ...LINEAR, ...PROBABILITY };

/* Render smoke test: build every PointCard and the whole tree with stubbed React. */
const renderStats = { cards: 0, elements: 0 };
let elementCount = 0;

function countElements(node) {
  if (!node || typeof node !== "object") return;
  if (Array.isArray(node)) {
    node.forEach(countElements);
    return;
  }
  if (!("type" in node)) return;
  elementCount += 1;
  countElements(node.children);
}

function tryRender(label, element) {
  const before = elementCount;
  try {
    countElements(element);
    renderStats.elements += elementCount - before;
  } catch (error) {
    errors.push(label + ": render threw — " + error.message);
  }
}

/* Supported command names, derived from the renderer itself. */
const symbolBlock = source.slice(
  source.indexOf("const SYMBOLS = {"),
  source.indexOf("const GREEK_LOWER"),
);
const supported = new Set();
for (const match of symbolBlock.matchAll(/([A-Za-z]+):/g)) supported.add(match[1]);
for (const match of source.matchAll(/name === "([A-Za-z]+)"/g)) supported.add(match[1]);
for (const name of [
  "begin", "end", "left", "right", "mid", "frac", "dfrac", "tfrac", "sqrt",
  "text", "mathrm", "mathbf", "mathit", "operatorname", "textbf",
]) {
  supported.add(name);
}

const errors = [];
const seenFormulas = new Set();

function checkMath(math, where) {
  if (!math.trim()) {
    errors.push(where + ": empty math");
    return;
  }
  seenFormulas.add(math);
  for (const match of math.matchAll(/(^|[^\\])\\([A-Za-z]+)/g)) {
    if (!supported.has(match[2])) {
      errors.push(where + ": unsupported command \\" + match[2]);
    }
  }
  const count = (pattern) => (math.match(pattern) || []).length;
  if (count(/\\left/g) !== count(/\\right/g)) {
    errors.push(where + ": unbalanced \\left / \\right — " + math);
  }
  if (count(/\\begin\{/g) !== count(/\\end\{/g)) {
    errors.push(where + ": unbalanced \\begin / \\end — " + math);
  }
  let depth = 0;
  let balanced = true;
  for (let i = 0; i < math.length; i += 1) {
    if (math[i] === "\\") {
      i += 1;
      continue;
    }
    if (math[i] === "{") depth += 1;
    else if (math[i] === "}") {
      depth -= 1;
      if (depth < 0) balanced = false;
    }
  }
  if (!balanced || depth !== 0) {
    errors.push(where + ": unbalanced braces — " + math);
  }
  let tree;
  try {
    tree = parseMath(math);
  } catch (error) {
    errors.push(where + ": parser threw — " + error.message + "\n    " + math);
    return;
  }
  const walk = (node) => {
    if (!node || typeof node !== "object") return;
    if (node.type === "text" && typeof node.value === "string" && node.value.includes("\\")) {
      errors.push(where + ": leftover backslash in text — " + math);
    }
    for (const value of Object.values(node)) {
      if (Array.isArray(value)) value.forEach(walk);
      else if (value && typeof value === "object") walk(value);
    }
  };
  walk(tree);
}

function checkString(text, where) {
  if (typeof text !== "string") return;
  const pattern = /\$([^$]+)\$|\\\(([\s\S]*?)\\\)|\\\[([\s\S]*?)\\\]/g;
  let match;
  while ((match = pattern.exec(text)) !== null) {
    checkMath(match[1] ?? match[2] ?? match[3] ?? "", where);
  }
  const withoutMath = text.replace(pattern, "");
  if (withoutMath.includes("$")) {
    errors.push(where + ": unbalanced $ — " + text);
  }
}

function checkBlocks(blocks, where) {
  (blocks || []).forEach((block, index) => {
    const at = where + " #" + (index + 1) + " (" + block.kind + ")";
    if (block.kind === "formula") checkMath(block.x, at);
    else if (block.kind === "list" || block.kind === "steps") {
      block.items.forEach((item) => checkString(item, at));
    } else if (block.kind === "table") {
      block.head.forEach((cell) => checkString(cell, at));
      block.rows.forEach((row) => row.forEach((cell) => checkString(cell, at)));
    } else if (block.kind === "example") {
      checkString(block.x, at);
      checkString(block.answer, at);
    } else if (block.kind === "note" || block.kind === "cue" || block.kind === "p") {
      checkString(block.x, at);
    } else {
      errors.push(at + ": unknown block kind");
    }
  });
}

POINTS.forEach((point) => {
  renderStats.cards += 1;
  tryRender("PointCard " + point.id, PointCard({ point, done: false, onToggle: () => {} }));
});

tryRender(
  "Tree",
  TreeNode({
    node: TREE,
    expanded: Object.fromEntries(
      (function collect(node) {
        const rows = [[node.id, true]];
        (node.children || []).forEach((child) => rows.push(...collect(child)));
        return rows;
      })(TREE),
    ),
    onToggle: () => {},
    onPoint: () => {},
    onSoon: () => {},
    onPaper: () => {},
    mastered: {},
  }),
);

tryRender("Panel", Panel({ useChat: undefined, useSession: undefined, openView: () => {} }));

const ids = new Set();
const sectionIds = new Set();
let chapters = 0;
let sections = 0;
let points = 0;

function walkChapters(chapterSections, chapterLabel) {
  chapterSections.forEach((section) => {
    sections += 1;
    if (sectionIds.has(section.id)) errors.push(chapterLabel + ": duplicate section id " + section.id);
    sectionIds.add(section.id);
    if (!section.no) errors.push(chapterLabel + " / " + section.title + ": missing no");
    if (!section.desc) errors.push(chapterLabel + " / " + section.title + ": missing desc");
    section.points.forEach((point) => {
      points += 1;
      const where = chapterLabel + " / " + section.title + " / " + point.title;
      if (ids.has(point.id)) errors.push(where + ": duplicate point id " + point.id);
      ids.add(point.id);
      if (!point.no) errors.push(where + ": missing no");
      if (!point.lead) errors.push(where + ": missing lead");
      if (!Array.isArray(point.body) || point.body.length === 0) {
        errors.push(where + ": empty body");
        return;
      }
      checkString(point.lead, where + " (lead)");
      checkBlocks(point.body, where);
    });
  });
}

walkChapters(SECTIONS, "ode");

Object.keys(CHAPTERS).forEach((chapterId) => {
  chapters += 1;
  const known = SUBJECTS.some((subject) => subject.chapters.some((chapter) => chapter.id === chapterId));
  if (!known) errors.push("content key " + chapterId + " has no chapter in SUBJECTS");
  walkChapters(CHAPTERS[chapterId], chapterId);
});

SUBJECTS.forEach((subject) => {
  subject.chapters.forEach((chapter) => {
    if (!chapter.sections) {
      if (chapter.status === "ready") errors.push("ready chapter without sections: " + chapter.id);
      return;
    }
    if (CHAPTERS[chapter.id] && CHAPTERS[chapter.id] !== chapter.sections) {
      errors.push("chapter " + chapter.id + " sections is not the content array");
    }
  });
});

if (POINTS.length !== points) {
  errors.push("POINTS length " + POINTS.length + " != walked points " + points);
}
if (new Set(POINTS.map((point) => point.id)).size !== points) {
  errors.push("POINTS contains duplicate ids");
}

console.log("chapters: " + chapters + "  sections: " + sections + "  points: " + points);
console.log("formulas parsed: " + seenFormulas.size);
console.log("rendered cards: " + renderStats.cards + "  elements: " + renderStats.elements);

if (errors.length) {
  console.error("\n" + errors.length + " problem(s):");
  errors.forEach((error) => console.error("  - " + error));
  process.exit(1);
}
console.log("OK");
