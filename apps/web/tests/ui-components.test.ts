import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));

// packages/ui/src/components/ — 3 levels up from tests dir
const componentsDir = resolve(__dirname, "..", "..", "..", "packages", "ui", "src", "components");
const tokensCssPath = resolve(componentsDir, "..", "tokens.css");

function readComponent(name: string): string {
  return readFileSync(resolve(componentsDir, `${name}.astro`), "utf8");
}

// ── Design tokens CSS ──────────────────────────────────────────────────

describe("design tokens (tokens.css)", () => {
  let css: string;

  it("tokens.css exists and contains :root block", () => {
    css = readFileSync(tokensCssPath, "utf8");
    expect(css).toContain(":root");
  });

  it("defines all color custom properties", () => {
    css = readFileSync(tokensCssPath, "utf8");
    const expected = [
      "--color-text-primary",
      "--color-text-secondary",
      "--color-text-muted",
      "--color-text-disabled",
      "--color-text-inverse",
      "--color-bg-page",
      "--color-bg-card",
      "--color-bg-hover",
      "--color-bg-active",
      "--color-bg-muted",
      "--color-border",
      "--color-border-light",
      "--color-border-focus",
      "--color-link",
      "--color-link-hover",
      "--color-button-primary-bg",
      "--color-button-primary-text",
      "--color-button-primary-hover",
      "--color-success",
      "--color-error",
      "--color-warning",
    ];
    for (const prop of expected) {
      expect(css, `missing ${prop}`).toContain(prop);
    }
  });

  it("defines all spacing custom properties", () => {
    css = readFileSync(tokensCssPath, "utf8");
    for (const step of [0, 1, 2, 3, 4, 6, 8, 12, 16, 24]) {
      expect(css).toContain(`--space-${step}`);
    }
  });

  it("defines all typography custom properties", () => {
    css = readFileSync(tokensCssPath, "utf8");
    const expected = [
      "--font-serif",
      "--font-sans",
      "--font-mono",
      "--text-xs",
      "--text-sm",
      "--text-base",
      "--text-lg",
      "--text-xl",
      "--text-2xl",
      "--text-3xl",
      "--text-4xl",
      "--text-5xl",
      "--leading-tight",
      "--leading-snug",
      "--leading-normal",
      "--leading-relaxed",
      "--font-normal",
      "--font-medium",
      "--font-semibold",
      "--font-bold",
      "--tracking-tight",
      "--tracking-normal",
      "--tracking-wide",
      "--tracking-wider",
    ];
    for (const prop of expected) {
      expect(css, `missing ${prop}`).toContain(prop);
    }
  });

  it("defines all layout and transition custom properties", () => {
    css = readFileSync(tokensCssPath, "utf8");
    const expected = [
      "--content-max-width",
      "--page-max-width",
      "--touch-target-min",
      "--radius-card",
      "--radius-button",
      "--transition-fast",
    ];
    for (const prop of expected) {
      expect(css, `missing ${prop}`).toContain(prop);
    }
  });

  it("defines all 9 typography preset utility classes", () => {
    css = readFileSync(tokensCssPath, "utf8");
    const expected = [
      ".typo-hero",
      ".typo-page-title",
      ".typo-card-title",
      ".typo-section-heading",
      ".typo-body",
      ".typo-lead",
      ".typo-caption",
      ".typo-meta",
      ".typo-tag",
    ];
    for (const cls of expected) {
      expect(css, `missing ${cls}`).toContain(cls);
    }
  });

  it("serif font-family uses Georgia as primary", () => {
    css = readFileSync(tokensCssPath, "utf8");
    expect(css).toMatch(/--font-serif:\s*Georgia/);
  });
});

// ── Button.astro ───────────────────────────────────────────────────────

describe("Button component", () => {
  let src: string;

  it("file exists and has frontmatter", () => {
    src = readComponent("Button");
    expect(src).toMatch(/^---/);
  });

  it("defines variant prop with primary / secondary / ghost", () => {
    src = readComponent("Button");
    expect(src).toContain('"primary"');
    expect(src).toContain('"secondary"');
    expect(src).toContain('"ghost"');
  });

  it("defines size prop with sm / md", () => {
    src = readComponent("Button");
    expect(src).toContain('"sm"');
    expect(src).toContain('"md"');
  });

  it("defines href prop for link rendering", () => {
    src = readComponent("Button");
    expect(src).toMatch(/href\??:\s*string/);
  });

  it("defines disabled prop", () => {
    src = readComponent("Button");
    expect(src).toMatch(/disabled\??:\s*boolean/);
  });

  it("renders dynamic tag (a or button) based on href", () => {
    src = readComponent("Button");
    expect(src).toContain('href ? "a"');
  });

  it("scoped CSS includes .btn base class", () => {
    src = readComponent("Button");
    expect(src).toContain("class");
    expect(src).toMatch(/["']btn["']/);
  });

  it("scoped CSS includes all 3 variant classes", () => {
    src = readComponent("Button");
    expect(src).toContain("btn--primary");
    expect(src).toContain("btn--secondary");
    expect(src).toContain("btn--ghost");
  });

  it("scoped CSS includes both size classes", () => {
    src = readComponent("Button");
    expect(src).toContain("btn--sm");
    expect(src).toContain("btn--md");
  });

  it("scoped CSS includes disabled state handling", () => {
    src = readComponent("Button");
    expect(src).toContain("[disabled]");
    expect(src).toContain("aria-disabled");
  });

  it("uses CSS custom properties from design tokens", () => {
    src = readComponent("Button");
    expect(src).toContain("--color-button-primary-bg");
    expect(src).toContain("--color-button-primary-text");
  });

  it("includes a <slot /> for content projection", () => {
    src = readComponent("Button");
    expect(src).toContain("<slot />");
  });
});

// ── Card.astro ─────────────────────────────────────────────────────────

describe("Card component", () => {
  let src: string;

  it("file exists and has frontmatter", () => {
    src = readComponent("Card");
    expect(src).toMatch(/^---/);
  });

  it("defines padding prop with none / sm / md / lg", () => {
    src = readComponent("Card");
    expect(src).toContain('"none"');
    expect(src).toContain('"sm"');
    expect(src).toContain('"md"');
    expect(src).toContain('"lg"');
  });

  it("defines element prop for semantic wrapper", () => {
    src = readComponent("Card");
    expect(src).toMatch(/"div"|"article"|"section"|"li"/);
  });

  it("defines href prop for link rendering", () => {
    src = readComponent("Card");
    expect(src).toMatch(/href\??:\s*string/);
  });

  it("renders dynamic tag (a or element) based on href", () => {
    src = readComponent("Card");
    expect(src).toContain('href ? "a"');
  });

  it("scoped CSS includes .card base class with border", () => {
    src = readComponent("Card");
    expect(src).toMatch(/["']card["']/);
    expect(src).toMatch(/border/);
  });

  it("scoped CSS includes all 4 padding variants", () => {
    src = readComponent("Card");
    expect(src).toContain("card--padding-none");
    expect(src).toContain("card--padding-sm");
    expect(src).toContain("card--padding-md");
    expect(src).toContain("card--padding-lg");
  });

  it("scoped CSS includes link-card hover style", () => {
    src = readComponent("Card");
    expect(src).toContain("a.card");
  });

  it("includes a <slot /> for content projection", () => {
    src = readComponent("Card");
    expect(src).toContain("<slot />");
  });
});

// ── Heading.astro ──────────────────────────────────────────────────────

describe("Heading component", () => {
  let src: string;

  it("file exists and has frontmatter", () => {
    src = readComponent("Heading");
    expect(src).toMatch(/^---/);
  });

  it("defines level prop as HeadingLevel type", () => {
    src = readComponent("Heading");
    expect(src).toMatch(/level:\s*HeadingLevel/);
    expect(src).toContain("type HeadingLevel");
    for (let i = 1; i <= 6; i++) {
      expect(src).toContain(String(i));
    }
  });

  it("defines preset prop with all 4 typography presets", () => {
    src = readComponent("Heading");
    expect(src).toContain('"hero"');
    expect(src).toContain('"page-title"');
    expect(src).toContain('"card-title"');
    expect(src).toContain('"section-heading"');
  });

  it("computes dynamic heading tag from level prop", () => {
    src = readComponent("Heading");
    // Dynamic tag: `h${level}`
    expect(src).toMatch(/`h\$\{level\}`/);
  });

  it("renders with <Tag> dynamic element", () => {
    src = readComponent("Heading");
    expect(src).toMatch(/<Tag\b/);
  });

  it("scoped CSS defines all 6 heading-level size classes", () => {
    src = readComponent("Heading");
    for (let i = 1; i <= 6; i++) {
      expect(src).toContain(`heading--level-${i}`);
    }
  });

  it("scoped CSS sets serif font-family as default", () => {
    src = readComponent("Heading");
    expect(src).toMatch(/--font-serif/);
  });

  it("applies typo- prefixed preset class when preset is provided", () => {
    src = readComponent("Heading");
    expect(src).toContain("typo-");
  });

  it("includes a <slot /> for content projection", () => {
    src = readComponent("Heading");
    expect(src).toContain("<slot />");
  });
});

// ── Tag.astro ──────────────────────────────────────────────────────────

describe("Tag component", () => {
  let src: string;

  it("file exists and has frontmatter", () => {
    src = readComponent("Tag");
    expect(src).toMatch(/^---/);
  });

  it("defines variant prop with default / accent / muted", () => {
    src = readComponent("Tag");
    expect(src).toContain('"default"');
    expect(src).toContain('"accent"');
    expect(src).toContain('"muted"');
  });

  it("defines size prop with sm / md", () => {
    src = readComponent("Tag");
    expect(src).toContain('"sm"');
    expect(src).toContain('"md"');
  });

  it("defines href prop for link rendering", () => {
    src = readComponent("Tag");
    expect(src).toMatch(/href\??:\s*string/);
  });

  it("renders dynamic tag (a or span) based on href", () => {
    src = readComponent("Tag");
    expect(src).toContain('href ? "a"');
  });

  it("scoped CSS includes .tag base class with uppercase", () => {
    src = readComponent("Tag");
    expect(src).toMatch(/["']tag["']/);
    expect(src).toMatch(/text-transform:\s*uppercase/);
  });

  it("scoped CSS includes all 3 variant classes", () => {
    src = readComponent("Tag");
    expect(src).toContain("tag--default");
    expect(src).toContain("tag--accent");
    expect(src).toContain("tag--muted");
  });

  it("scoped CSS includes both size classes", () => {
    src = readComponent("Tag");
    expect(src).toContain("tag--sm");
    expect(src).toContain("tag--md");
  });

  it("includes a <slot /> for content projection", () => {
    src = readComponent("Tag");
    expect(src).toContain("<slot />");
  });
});

// ── SourceBadge.astro ──────────────────────────────────────────────────

describe("SourceBadge component", () => {
  let src: string;

  it("file exists and has frontmatter", () => {
    src = readComponent("SourceBadge");
    expect(src).toMatch(/^---/);
  });

  it("defines required name prop", () => {
    src = readComponent("SourceBadge");
    // name is required (not optional)
    expect(src).toMatch(/name:\s*string/);
  });

  it("defines href prop for link rendering", () => {
    src = readComponent("SourceBadge");
    expect(src).toMatch(/href\??:\s*string/);
  });

  it("defines size prop with sm / md", () => {
    src = readComponent("SourceBadge");
    expect(src).toContain('"sm"');
    expect(src).toContain('"md"');
  });

  it("renders dynamic tag (a or span) based on href", () => {
    src = readComponent("SourceBadge");
    expect(src).toContain('href ? "a"');
  });

  it("displays the name prop as content", () => {
    src = readComponent("SourceBadge");
    expect(src).toContain("{name}");
  });

  it("scoped CSS includes .source-badge base class", () => {
    src = readComponent("SourceBadge");
    expect(src).toContain("source-badge");
  });

  it("scoped CSS includes both size classes", () => {
    src = readComponent("SourceBadge");
    expect(src).toContain("source-badge--sm");
    expect(src).toContain("source-badge--md");
  });

  it("scoped CSS includes hover state for link variant", () => {
    src = readComponent("SourceBadge");
    expect(src).toContain("a.source-badge");
  });
});

// ── Cross-component consistency checks ─────────────────────────────────

describe("design system consistency", () => {
  it("all 5 components reference design token CSS variables", () => {
    const components = ["Button", "Card", "Heading", "Tag", "SourceBadge"];
    for (const name of components) {
      const src = readComponent(name);
      expect(src, `${name} missing CSS vars`).toMatch(/--color-|--font-|--space-|--text-|--leading-|--tracking-|--radius-|--transition-/);
    }
  });

  it("all 5 components include <slot /> for content projection", () => {
    const components = ["Button", "Card", "Heading", "Tag", "SourceBadge"];
    for (const name of components) {
      const src = readComponent(name);
      expect(src, `${name} missing slot`).toContain("<slot />");
    }
  });

  it("all 5 components have scoped <style> blocks", () => {
    const components = ["Button", "Card", "Heading", "Tag", "SourceBadge"];
    for (const name of components) {
      const src = readComponent(name);
      expect(src, `${name} missing style block`).toContain("<style>");
    }
  });

  it("link-capable components (Button, Card, Tag, SourceBadge) all support href prop", () => {
    const components = ["Button", "Card", "Tag", "SourceBadge"];
    for (const name of components) {
      const src = readComponent(name);
      expect(src, `${name} missing href prop`).toMatch(/href\??:\s*string/);
      expect(src, `${name} missing dynamic tag`).toContain('href ? "a"');
    }
  });

  it("Button and Tag support size prop (sm / md)", () => {
    for (const name of ["Button", "Tag"]) {
      const src = readComponent(name);
      expect(src).toContain('"sm"');
      expect(src).toContain('"md"');
    }
  });
});
