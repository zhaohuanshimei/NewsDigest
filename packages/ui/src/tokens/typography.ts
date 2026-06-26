/**
 * Typography tokens for News Digest V2.
 *
 * Design direction: Direction C ("极简升级版") with Direction A newspaper influence.
 * - Headings: serif (Georgia / system serif stack) for authority and readability
 * - Body: system font stack for performance and native feel
 * - Monospace: for code, dates, metadata
 *
 * Constraints (from docs/design & non-functional-targets):
 * - System font stacks only — zero web font loading
 * - Lighthouse Performance > 90 → no render-blocking font requests
 * - Mobile-first sizing with responsive scaling
 */

// ── Font families ────────────────────────────────────────────────────

export const fontFamily = {
  /**
   * Serif stack for headings.
   * Georgia is chosen as the primary serif — it ships with all major OS
   * and renders crisply at all sizes.
   */
  serif: [
    'Georgia',
    '"Playfair Display"',
    '"Times New Roman"',
    'Times',
    'serif',
  ].join(', '),

  /**
   * System sans-serif stack for body text and UI elements.
   * Follows the native OS font for maximum performance.
   */
  sans: [
    '-apple-system',
    'BlinkMacSystemFont',
    '"Segoe UI"',
    'Roboto',
    '"Helvetica Neue"',
    'Arial',
    '"Noto Sans"',
    'sans-serif',
  ].join(', '),

  /**
   * System monospace stack for metadata, dates, and code.
   */
  mono: [
    '"SF Mono"',
    '"Fira Code"',
    '"Fira Mono"',
    '"Roboto Mono"',
    'Menlo',
    'Consolas',
    'monospace',
  ].join(', '),
} as const;

// ── Font sizes (mobile-first) ────────────────────────────────────────

export const fontSize = {
  /** 12px — fine print, tags, badges */
  xs: '12px',
  /** 13px — metadata, timestamps */
  sm: '13px',
  /** 14px — secondary text, captions */
  base: '14px',
  /** 16px — primary body text */
  lg: '16px',
  /** 18px — article lead / intro text */
  xl: '18px',
  /** 20px — section headings */
  '2xl': '20px',
  /** 24px — card titles, sub-headings */
  '3xl': '24px',
  /** 32px — page titles */
  '4xl': '32px',
  /** 40px — hero / feature headline */
  '5xl': '40px',
} as const;

// ── Line heights ─────────────────────────────────────────────────────

export const lineHeight = {
  /** 1.2 — headings, display text */
  tight: 1.2,
  /** 1.4 — sub-headings, card titles */
  snug: 1.4,
  /** 1.6 — body text, articles (default reading) */
  normal: 1.6,
  /** 1.8 — relaxed reading, featured articles */
  relaxed: 1.8,
} as const;

// ── Font weights ─────────────────────────────────────────────────────

export const fontWeight = {
  normal: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
} as const;

// ── Letter spacing ───────────────────────────────────────────────────

export const letterSpacing = {
  /** -0.02em — large headlines */
  tight: '-0.02em',
  /** 0 — body text */
  normal: '0em',
  /** 0.02em — small caps, labels */
  wide: '0.02em',
  /** 0.06em — uppercase labels, category tags */
  wider: '0.06em',
} as const;

// ── Type scale presets ────────────────────────────────────────────────
// Pre-composed type styles for common use cases. Each preset bundles
// font-family, size, line-height, weight, and letter-spacing.

export interface TypeStyle {
  fontFamily: string;
  fontSize: string;
  lineHeight: number;
  fontWeight: number;
  letterSpacing: string;
}

export const typography = {
  /** Hero headline — newspaper masthead feel */
  hero: {
    fontFamily: fontFamily.serif,
    fontSize: fontSize['5xl'],
    lineHeight: lineHeight.tight,
    fontWeight: fontWeight.bold,
    letterSpacing: letterSpacing.tight,
  } satisfies TypeStyle,

  /** Page title */
  pageTitle: {
    fontFamily: fontFamily.serif,
    fontSize: fontSize['4xl'],
    lineHeight: lineHeight.tight,
    fontWeight: fontWeight.bold,
    letterSpacing: letterSpacing.tight,
  } satisfies TypeStyle,

  /** Card / article title */
  cardTitle: {
    fontFamily: fontFamily.serif,
    fontSize: fontSize['3xl'],
    lineHeight: lineHeight.snug,
    fontWeight: fontWeight.semibold,
    letterSpacing: letterSpacing.normal,
  } satisfies TypeStyle,

  /** Section heading */
  sectionHeading: {
    fontFamily: fontFamily.serif,
    fontSize: fontSize['2xl'],
    lineHeight: lineHeight.snug,
    fontWeight: fontWeight.semibold,
    letterSpacing: letterSpacing.normal,
  } satisfies TypeStyle,

  /** Article body text — primary reading */
  body: {
    fontFamily: fontFamily.sans,
    fontSize: fontSize.lg,
    lineHeight: lineHeight.normal,
    fontWeight: fontWeight.normal,
    letterSpacing: letterSpacing.normal,
  } satisfies TypeStyle,

  /** Article lead / intro paragraph */
  lead: {
    fontFamily: fontFamily.sans,
    fontSize: fontSize.xl,
    lineHeight: lineHeight.relaxed,
    fontWeight: fontWeight.normal,
    letterSpacing: letterSpacing.normal,
  } satisfies TypeStyle,

  /** Secondary / caption text */
  caption: {
    fontFamily: fontFamily.sans,
    fontSize: fontSize.base,
    lineHeight: lineHeight.normal,
    fontWeight: fontWeight.normal,
    letterSpacing: letterSpacing.normal,
  } satisfies TypeStyle,

  /** Metadata — dates, source labels, tags */
  meta: {
    fontFamily: fontFamily.sans,
    fontSize: fontSize.sm,
    lineHeight: lineHeight.normal,
    fontWeight: fontWeight.normal,
    letterSpacing: letterSpacing.wide,
  } satisfies TypeStyle,

  /** Tag / badge label — uppercase */
  tag: {
    fontFamily: fontFamily.sans,
    fontSize: fontSize.xs,
    lineHeight: lineHeight.normal,
    fontWeight: fontWeight.medium,
    letterSpacing: letterSpacing.wider,
  } satisfies TypeStyle,
} as const;

export type TypographyPreset = keyof typeof typography;
export type FontFamily = keyof typeof fontFamily;
export type FontSize = keyof typeof fontSize;
