import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const testDir = dirname(fileURLToPath(import.meta.url));
const componentsDir = resolve(testDir, "..", "src", "components");

function readComponent(relativePath: string): string {
  return readFileSync(resolve(componentsDir, relativePath), "utf8");
}

describe("state components", () => {
  describe("EmptyState", () => {
    const html = readComponent("states/EmptyState.astro");

    it("renders an empty-state message", () => {
      expect(html).toContain("No digest published yet");
    });

    it("uses aria-live for accessibility", () => {
      expect(html).toContain('aria-live="polite"');
    });

    it("uses state-panel styling class", () => {
      expect(html).toContain("state-panel");
    });
  });

  describe("ErrorState", () => {
    const html = readComponent("states/ErrorState.astro");

    it("renders an error-state heading", () => {
      expect(html).toContain("temporarily unavailable");
    });

    it("accepts a message prop for details", () => {
      expect(html).toContain("message");
    });

    it("uses aria-live for accessibility", () => {
      expect(html).toContain('aria-live="polite"');
    });
  });

  describe("LoadingState", () => {
    const html = readComponent("states/LoadingState.astro");

    it("renders loading message", () => {
      expect(html).toContain("Loading digest content");
      expect(html).toContain("Please wait while we fetch the latest stories");
    });

    it("has animated loading indicator", () => {
      expect(html).toContain("state-loading-indicator");
      expect(html).toContain("state-loading-dot");
    });

    it("has role=status for screen readers", () => {
      expect(html).toContain('role="status"');
    });

    it("has aria-live region for accessibility", () => {
      expect(html).toContain('aria-live="polite"');
    });

    it("marks decorative indicator as aria-hidden", () => {
      expect(html).toContain('aria-hidden="true"');
    });

    it("includes loading animation keyframes", () => {
      expect(html).toContain("@keyframes");
    });
  });

  describe("NoResultsState", () => {
    const html = readComponent("states/NoResultsState.astro");

    it("renders no results heading", () => {
      expect(html).toContain("No results found");
    });

    it("shows the search query in the heading when provided", () => {
      expect(html).toContain("query");
    });

    it("provides search tips to help users", () => {
      expect(html).toContain("Search tips");
      expect(html).toContain("typos");
    });

    it("includes link to archive page", () => {
      expect(html).toContain('href="/archive"');
    });

    it("has aria-live region for accessibility", () => {
      expect(html).toContain('aria-live="polite"');
    });
  });
});

describe("SearchBar component", () => {
  const html = readComponent("search/SearchBar.astro");

  it("renders a search input", () => {
    expect(html).toContain('type="search"');
    expect(html).toContain("search-bar-input");
  });

  it("has a search role landmark", () => {
    expect(html).toContain('role="search"');
  });

  it("includes an aria-label for accessibility", () => {
    expect(html).toContain("aria-label");
  });

  it("has a clear button", () => {
    expect(html).toContain("search-bar-clear");
    expect(html).toContain("Clear");
  });

  it("supports keyboard shortcuts in client script", () => {
    expect(html).toContain("Escape");
    expect(html).toContain("'/'");
  });

  it("emits a digest-search custom event", () => {
    expect(html).toContain("digest-search");
    expect(html).toContain("CustomEvent");
  });

  it("debounces search input", () => {
    expect(html).toContain("debounce");
  });

  it("accepts placeholder and initialValue props", () => {
    expect(html).toContain("placeholder");
    expect(html).toContain("initialValue");
  });

  it("uses scoped styles for the search bar", () => {
    expect(html).toContain(".search-bar-input");
    expect(html).toContain(".search-bar-clear");
  });
});

describe("state components visual distinction", () => {
  it("empty state has distinct copy from error state", () => {
    const emptyHtml = readComponent("states/EmptyState.astro");
    const errorHtml = readComponent("states/ErrorState.astro");

    // Empty state talks about nothing published
    expect(emptyHtml).toContain("No digest published");
    // Error state talks about unavailability
    expect(errorHtml).toContain("unavailable");
    // They should not share the same heading
    expect(emptyHtml).not.toContain("unavailable");
    expect(errorHtml).not.toContain("No digest published");
  });

  it("no-results state has distinct copy from empty state", () => {
    const noResultsHtml = readComponent("states/NoResultsState.astro");
    const emptyHtml = readComponent("states/EmptyState.astro");

    expect(noResultsHtml).toContain("No results found");
    expect(emptyHtml).toContain("No digest published");
    expect(noResultsHtml).not.toContain("No digest published");
  });
});
