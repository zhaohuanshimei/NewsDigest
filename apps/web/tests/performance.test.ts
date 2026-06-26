import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const testDir = dirname(fileURLToPath(import.meta.url));
const stylesDir = resolve(testDir, "..", "src", "styles");

describe("performance.css", () => {
  const performanceCss = readFileSync(resolve(stylesDir, "performance.css"), "utf8");

  it("exists and is not empty", () => {
    expect(performanceCss).toBeDefined();
    expect(performanceCss.length).toBeGreaterThan(0);
  });

  it("prevents layout shift for images and videos", () => {
    expect(performanceCss).toContain("img");
    expect(performanceCss).toContain("max-width: 100%");
    expect(performanceCss).toContain("height: auto");
  });

  it("uses CSS containment for rendering performance", () => {
    expect(performanceCss).toContain("contain:");
    // Should not use strict containment
    expect(performanceCss).not.toContain("contain: strict");
    // Uses safe paint/style containment
    expect(performanceCss).toContain("style paint");
  });

  it("optimizes text rendering for key headings", () => {
    expect(performanceCss).toContain("text-rendering: optimizeLegibility");
    expect(performanceCss).toContain("-webkit-font-smoothing: antialiased");
    expect(performanceCss).toContain("-moz-osx-font-smoothing: grayscale");
  });

  it("includes page-shell overflow protection", () => {
    expect(performanceCss).toContain(".page-shell");
    expect(performanceCss).toContain("overflow-x: hidden");
  });

  it("optimizes list rendering for archive and digest", () => {
    expect(performanceCss).toContain(".archive-date-list");
    expect(performanceCss).toContain(".digest-entry-list");
    expect(performanceCss).toContain("list-style: none");
  });

  it("removes link transitions to reduce repaints", () => {
    expect(performanceCss).toContain(".digest-entry-link");
    expect(performanceCss).toContain("transition: none");
  });

  it("optimizes mobile touch scrolling", () => {
    expect(performanceCss).toContain("@media (max-width: 48rem)");
    expect(performanceCss).toContain("overscroll-behavior-y: contain");
  });

  it("includes print styles", () => {
    expect(performanceCss).toContain("@media print");
    expect(performanceCss).toContain(".digest-surface");
    expect(performanceCss).toContain(".archive-surface");
    expect(performanceCss).toContain(".cluster-surface");
    expect(performanceCss).toContain(".state-panel");
  });

  it("prevents page break issues in print", () => {
    expect(performanceCss).toContain("page-break-inside: avoid");
  });

  it("coordinates with reduced motion preferences", () => {
    expect(performanceCss).toContain("@media (prefers-reduced-motion: reduce)");
    expect(performanceCss).toContain("transition: none");
    expect(performanceCss).toContain("animation: none");
  });
});

describe("performance baseline requirements", () => {
  const performanceCss = readFileSync(resolve(stylesDir, "performance.css"), "utf8");

  it("addresses CLS by constraining media elements", () => {
    expect(performanceCss).toContain("img");
    expect(performanceCss).toContain("max-width: 100%");
    expect(performanceCss).toContain("height: auto");
    expect(performanceCss).toContain("display: block");
  });

  it("uses containment to isolate style/paint of list items", () => {
    expect(performanceCss).toContain(".digest-entry");
    expect(performanceCss).toContain(".archive-date-item");
    expect(performanceCss).toContain("contain: style paint");
  });

  it("enables GPU-friendly text rendering", () => {
    expect(performanceCss).toContain("text-rendering: optimizeLegibility");
    expect(performanceCss).toContain("-webkit-font-smoothing: antialiased");
  });

  it("prevents horizontal overflow on the page shell", () => {
    expect(performanceCss).toContain(".page-shell");
    expect(performanceCss).toContain("overflow-x: hidden");
  });

  it("includes safe print styles without layout breaking", () => {
    expect(performanceCss).toContain("@media print");
    expect(performanceCss).toContain("page-break-inside: avoid");
  });

  it("respects reduced motion for performance-sensitive elements", () => {
    expect(performanceCss).toContain("@media (prefers-reduced-motion: reduce)");
    expect(performanceCss).toContain("transition: none");
    expect(performanceCss).toContain("animation: none");
  });
});
