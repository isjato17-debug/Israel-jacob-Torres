import assert from "node:assert/strict";
import { mkdtemp, mkdir, readFile, rm, symlink, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { mockupPreviewPlugin } from "../../artifacts/mockup-sandbox/mockupPreviewPlugin.ts";

const root = fileURLToPath(new URL("../../", import.meta.url));
const app = createRequire(path.join(root, "artifacts/genesis-app/package.json"));
const api = createRequire(path.join(root, "artifacts/api-server/package.json"));
const spec = createRequire(path.join(root, "lib/api-spec/package.json"));
const express = createRequire(api.resolve("express"));
const typographyPath = app.resolve("@tailwindcss/typography");
const typography = createRequire(typographyPath);
const postcss = createRequire(createRequire(app.resolve("vite")).resolve("postcss"));
const orval = createRequire(spec.resolve("orval"));
const typedoc = createRequire(orval.resolve("typedoc"));
const minimatch = createRequire(typedoc.resolve("minimatch"));
const scalar = createRequire(orval.resolve("@scalar/openapi-parser"));
const ajv = createRequire(scalar.resolve("ajv"));

test("runtime resolution uses reviewed patched versions, not just the lockfile", () => {
  for (const [loader, name, version] of [
    [express, "proxy-addr", "2.0.8"],
    [minimatch, "brace-expansion", "5.0.12"],
    [postcss, "source-map-js", "1.2.2"],
    [ajv, "fast-uri", "3.1.8"],
    [typography, "postcss-selector-parser", "7.1.6"],
  ]) {
    assert.equal(loader(`${name}/package.json`).version, version);
  }
});

test("proxy-addr does not trust arbitrary IPv4 via a short mapped IPv6 subnet", () => {
  const proxy = express("proxy-addr");
  assert.equal(proxy.compile("::ffff:10.0.0.0/8")("192.0.2.1"), false);
  assert.equal(proxy.compile("10.0.0.0/8")("10.1.2.3"), true);
  assert.equal(proxy.compile("10.0.0.0/8")("192.0.2.1"), false);
});

const { expand } = minimatch("brace-expansion");
test("brace-expansion bounds comma parsing recursion", () => {
  assert.doesNotThrow(() => expand("{" + "{a},".repeat(7000) + "b}", { max: 10 }));
});
test("brace-expansion bounds nested expansion recursion", () => {
  assert.doesNotThrow(() => expand("{".repeat(3200) + "a,b" + "}".repeat(3200), { max: 10 }));
});
test("brace-expansion bounds repeated closing-brace rewrites", () => {
  assert.doesNotThrow(() => expand("{a}" + "}".repeat(64000) + ",z}", { max: 10 }));
});

test("source-map-js rejects an excessive indexed-section line offset", () => {
  const { SourceMapConsumer } = postcss("source-map-js");
  assert.throws(() => new SourceMapConsumer({
    version: 3,
    sections: [{
      offset: { line: 10000001, column: 0 },
      map: { version: 3, sources: [], names: [], mappings: "" },
    }],
  }), /offset|limit|large/i);
});

test("fast-uri normalizes percent-encoded uppercase scheme-relative hosts", () => {
  const uri = ajv("fast-uri");
  assert.equal(uri.parse("//%41.com").host, "a.com");
  assert.equal(uri.equal("//%41.com", "//a.com"), true);
});

test("the major parser update preserves selector handling and typography compilation", async () => {
  const parser = typography("postcss-selector-parser");
  for (const selector of [
    "a:hover", "h1, h2, h3", "ul > li::marker",
    '[data-state="open"] .item:not(.disabled)',
    '[class~="prose"] :where(a):not(:where([class~="not-prose"],[class~="not-prose"] *))',
    ".prose-lg :is(h1,h2)", "svg|a.foo#bar::before",
  ]) {
    assert.equal(parser().processSync(selector), selector);
  }
  const compiler = await app("tailwindcss").compile(
    '@plugin "@tailwindcss/typography"; @tailwind utilities;',
    { loadModule: async () => ({
      path: typographyPath, module: app("@tailwindcss/typography"), base: root,
    }) },
  );
  const css = compiler.build(["prose", "prose-lg", "prose-invert"]);
  assert.match(css, /\.prose/);
  assert.ok(css.length > 1000);
});

test("native mockup discovery retains nested/symlink previews and hidden-file exclusions", async () => {
  const fixture = await mkdtemp(path.join(tmpdir(), "genesis-glob-regression-"));
  try {
    for (const file of [
      "Visible.tsx", "nested/Other.tsx", "_Private.tsx",
      "_hidden/Excluded.tsx", "nested/_Internal.tsx", "not-a-preview.ts",
      ".Dot.tsx", ".hidden/DotChild.tsx",
    ]) {
      const target = path.join(fixture, "src/components/mockups", file);
      await mkdir(path.dirname(target), { recursive: true });
      await writeFile(target, "export default function Preview() { return null; }\n");
    }
    await symlink("nested", path.join(fixture, "src/components/mockups/linked"));
    await symlink("..", path.join(fixture, "src/components/mockups/nested/cycle"));
    const plugin = mockupPreviewPlugin();
    plugin.configResolved({ root: fixture });
    await plugin.buildStart();
    const generated = await readFile(path.join(fixture, "src/.generated/mockup-components.ts"), "utf8");
    assert.match(generated, /Visible\.tsx/);
    assert.match(generated, /nested\/Other\.tsx/);
    assert.match(generated, /linked\/Other\.tsx/);
    assert.doesNotMatch(generated, /Private|Excluded|Internal|not-a-preview|Dot|cycle/);
  } finally {
    await rm(fixture, { recursive: true, force: true });
  }
});
