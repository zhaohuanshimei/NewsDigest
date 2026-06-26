/**
 * Spacing tokens and responsive breakpoints for News Digest V2.
 *
 * Based on a 4px base grid. Design direction emphasizes generous whitespace
 * and breathing room (Direction C: "极简升级版").
 */

// ── Base grid ────────────────────────────────────────────────────────

const GRID = 4;

/** Numeric spacing scale (px values, no unit). */
export const spacingScale = {
  /** 0px */
  0: 0,
  /** 4px — micro gaps, icon padding */
  1: GRID * 1,
  /** 8px — inline element gaps */
  2: GRID * 2,
  /** 12px — compact padding */
  3: GRID * 3,
  /** 16px — default padding, vertical rhythm */
  4: GRID * 4,
  /** 24px — section padding, card gaps */
  6: GRID * 6,
  /** 32px — large card padding, major gaps */
  8: GRID * 8,
  /** 48px — section separation */
  12: GRID * 12,
  /** 64px — page-level section spacing */
  16: GRID * 16,
  /** 96px — hero / major section spacing */
  24: GRID * 24,
} as const;

/** Spacing as CSS string values (e.g. "16px"). */
export const spacing = {
  0: '0px',
  1: '4px',
  2: '8px',
  3: '12px',
  4: '16px',
  6: '24px',
  8: '32px',
  12: '48px',
  16: '64px',
  24: '96px',
} as const;

export type SpacingScale = keyof typeof spacingScale;
export type SpacingToken = keyof typeof spacing;

// ── Responsive breakpoints ───────────────────────────────────────────
// Mobile-first: base styles target <sm, then scale up.

export const breakpoints = {
  /** 640px — tablet portrait */
  sm: '640px',
  /** 1024px — tablet landscape / small desktop */
  md: '1024px',
  /** 1280px — large desktop */
  lg: '1280px',
} as const;

/** Numeric breakpoint values (px, no unit) for JS-side comparisons. */
export const breakpointValues = {
  sm: 640,
  md: 1024,
  lg: 1280,
} as const;

export type Breakpoint = keyof typeof breakpoints;

// ── Layout constants ─────────────────────────────────────────────────

export const layout = {
  /** Maximum content width for article body */
  contentMaxWidth: '680px',
  /** Maximum page width */
  pageMaxWidth: '1200px',
  /** Minimum touch target (WCAG 2.1 / non-functional-targets) */
  touchTargetMin: '44px',
  /** Default card border radius */
  radiusCard: '4px',
  /** Button / badge border radius */
  radiusButton: '2px',
} as const;
