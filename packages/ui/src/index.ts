/**
 * @news-digest/ui — public API
 *
 * Re-exports all design tokens for consumption by apps/web and other packages.
 */

export { colors, neutral, accent } from './tokens/colors.js';
export type { ColorToken, NeutralToken, AccentToken } from './tokens/colors.js';

export {
  spacing,
  spacingScale,
  breakpoints,
  breakpointValues,
  layout,
} from './tokens/spacing.js';
export type {
  SpacingToken,
  SpacingScale,
  Breakpoint,
} from './tokens/spacing.js';

export {
  fontFamily,
  fontSize,
  lineHeight,
  fontWeight,
  letterSpacing,
  typography,
} from './tokens/typography.js';
export type {
  TypeStyle,
  TypographyPreset,
  FontFamily,
  FontSize,
} from './tokens/typography.js';
