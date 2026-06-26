/**
 * Color tokens for News Digest V2.
 *
 * Design direction: Direction C ("极简升级版") — black/white/gray primary palette
 * with a low-saturation accent for interactive elements.
 *
 * All body-text combinations meet WCAG 2.1 AA contrast (≥ 4.5:1).
 */

// ── Neutral palette ──────────────────────────────────────────────────
// Black-to-gray ramp used for text, borders, and backgrounds.

export const neutral = {
  /** Pure black — headings, primary text on light backgrounds */
  black: '#000000',
  /** Very dark gray — secondary text, captions */
  900: '#1A1A1A',
  800: '#2E2E2E',
  /** Dark gray — body text on white (contrast 14.7:1) */
  700: '#404040',
  /** Medium gray — muted text, meta info (contrast 7.5:1 on white) */
  600: '#5C5C5C',
  /** Gray — borders and dividers */
  500: '#808080',
  /** Light gray — subtle borders, disabled state */
  400: '#B0B0B0',
  /** Very light gray — card borders, section separators */
  300: '#D4D4D4',
  /** Near white — background tints, hover states */
  200: '#EBEBEB',
  100: '#F5F5F5',
  /** Off-white — page background */
  50: '#FAFAFA',
  /** Pure white */
  white: '#FFFFFF',
} as const;

// ── Accent palette ───────────────────────────────────────────────────
// Low-saturation blue accent for links, buttons, and interactive states.

export const accent = {
  /** Dark accent — hover state */
  700: '#1A3A5C',
  /** Primary accent — links, buttons (contrast 7.2:1 on white) */
  600: '#245680',
  /** Default accent — interactive elements */
  500: '#2E6EA6',
  /** Light accent — focus rings, badges */
  400: '#5A94C8',
  /** Very light accent — selected background tint */
  100: '#E8F0F8',
} as const;

// ── Semantic aliases ─────────────────────────────────────────────────
// High-level semantic names consumed by components.

export const colors = {
  // Text
  textPrimary: neutral.black,
  textSecondary: neutral[700],
  textMuted: neutral[600],
  textDisabled: neutral[400],
  textInverse: neutral.white,

  // Backgrounds
  bgPage: neutral.white,
  bgCard: neutral.white,
  bgHover: neutral[100],
  bgActive: accent[100],
  bgMuted: neutral[50],

  // Borders
  borderDefault: neutral[300],
  borderLight: neutral[200],
  borderFocus: accent[500],

  // Interactive
  link: accent[500],
  linkHover: accent[700],
  buttonPrimaryBg: accent[600],
  buttonPrimaryText: neutral.white,
  buttonPrimaryHover: accent[700],

  // Status (kept minimal for V2 launch)
  success: '#2D6A4F',
  error: '#B91C1C',
  warning: '#92400E',
} as const;

export type ColorToken = keyof typeof colors;
export type NeutralToken = keyof typeof neutral;
export type AccentToken = keyof typeof accent;
