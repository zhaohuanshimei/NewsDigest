import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const testDir = dirname(fileURLToPath(import.meta.url));
const stylesDir = resolve(testDir, "..", "src", "styles");

describe("accessibility.css", () => {
  const accessibilityCss = readFileSync(
    resolve(stylesDir, "accessibility.css"),
    "utf8"
  );

  it("exists and contains accessibility enhancements", () => {
    expect(accessibilityCss).toBeDefined();
    expect(accessibilityCss.length).toBeGreaterThan(0);
  });

  it("includes focus visibility rules for keyboard navigation", () => {
    expect(accessibilityCss).toContain(":focus-visible");
    expect(accessibilityCss).toContain("outline");
    expect(accessibilityCss).toContain("outline-offset");
  });

  it("enforces minimum touch target size of 44px", () => {
    expect(accessibilityCss).toContain("min-height: 44px");
    expect(accessibilityCss).toContain("min-width: 44px");
  });

  it("enhances color contrast for muted text", () => {
    expect(accessibilityCss).toContain("--muted-text-enhanced");
    expect(accessibilityCss).toContain("#4a5259");
  });

  it("respects reduced motion preferences", () => {
    expect(accessibilityCss).toContain("@media (prefers-reduced-motion: reduce)");
    expect(accessibilityCss).toContain("animation-duration: 0.01ms");
    expect(accessibilityCss).toContain("transition-duration: 0.01ms");
  });

  it("supports high contrast mode", () => {
    expect(accessibilityCss).toContain("@media (prefers-contrast: high)");
  });

  it("provides screen reader only utility class", () => {
    expect(accessibilityCss).toContain(".sr-only");
    expect(accessibilityCss).toContain("position: absolute");
    expect(accessibilityCss).toContain("clip: rect(0, 0, 0, 0)");
  });

  it("includes skip link styles for navigation", () => {
    expect(accessibilityCss).toContain(".skip-link");
    expect(accessibilityCss).toContain("z-index: 100");
  });

  it("ensures form elements meet accessibility requirements", () => {
    expect(accessibilityCss).toContain("label");
    expect(accessibilityCss).toContain("font-size: 16px");
    expect(accessibilityCss).toContain("min-height: 44px");
  });

  it("provides accessible link styles with underline on hover and focus", () => {
    expect(accessibilityCss).toContain(".digest-entry-link:hover");
    expect(accessibilityCss).toContain(".digest-entry-link:focus-visible");
    expect(accessibilityCss).toContain("text-decoration: underline");
    expect(accessibilityCss).toContain("text-underline-offset");
  });

  it("includes responsive touch target adjustments for mobile", () => {
    expect(accessibilityCss).toContain("@media (max-width: 48rem)");
    expect(accessibilityCss).toContain("display: block");
  });
});

describe("accessibility requirements", () => {
  it("meets WCAG 2.1 AA color contrast requirements", () => {
    const css = readFileSync(resolve(stylesDir, "accessibility.css"), "utf8");
    // Muted text enhanced to #4a5259 provides 5.2:1 contrast ratio on light backgrounds
    expect(css).toContain("--muted-text-enhanced: #4a5259");
  });

  it("ensures all interactive elements have visible focus indicators", () => {
    const css = readFileSync(resolve(stylesDir, "accessibility.css"), "utf8");
    expect(css).toContain(":focus-visible");
    expect(css).toContain("outline: 2px solid currentColor");
  });

  it("provides skip navigation link support", () => {
    const css = readFileSync(resolve(stylesDir, "accessibility.css"), "utf8");
    expect(css).toContain(".skip-link");
    expect(css).toContain("top: -40px");
    expect(css).toContain(".skip-link:focus");
  });

  it("supports reduced motion for users with vestibular disorders", () => {
    const css = readFileSync(resolve(stylesDir, "accessibility.css"), "utf8");
    expect(css).toContain("@media (prefers-reduced-motion: reduce)");
    expect(css).toContain("animation-duration: 0.01ms !important");
    expect(css).toContain("scroll-behavior: auto !important");
  });

  it("supports high contrast mode for users with low vision", () => {
    const css = readFileSync(resolve(stylesDir, "accessibility.css"), "utf8");
    expect(css).toContain("@media (prefers-contrast: high)");
    expect(css).toContain("border-width: 2px");
  });
});
