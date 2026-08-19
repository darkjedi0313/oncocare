---
name: Institutional Precision
colors:
  surface: '#fcf9f8'
  surface-dim: '#dcd9d9'
  surface-bright: '#fcf9f8'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f3f2'
  surface-container: '#f0eded'
  surface-container-high: '#eae7e7'
  surface-container-highest: '#e5e2e1'
  on-surface: '#1b1c1c'
  on-surface-variant: '#42474e'
  inverse-surface: '#303030'
  inverse-on-surface: '#f3f0ef'
  outline: '#72777f'
  outline-variant: '#c2c7cf'
  surface-tint: '#35618c'
  primary: '#00375e'
  on-primary: '#ffffff'
  primary-container: '#1f4e78'
  on-primary-container: '#95bff0'
  inverse-primary: '#a0cafb'
  secondary: '#006a6a'
  on-secondary: '#ffffff'
  secondary-container: '#90efef'
  on-secondary-container: '#006e6e'
  tertiary: '#700602'
  on-tertiary: '#ffffff'
  tertiary-container: '#912115'
  on-tertiary-container: '#ffa596'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d0e4ff'
  primary-fixed-dim: '#a0cafb'
  on-primary-fixed: '#001d35'
  on-primary-fixed-variant: '#194973'
  secondary-fixed: '#93f2f2'
  secondary-fixed-dim: '#76d6d5'
  on-secondary-fixed: '#002020'
  on-secondary-fixed-variant: '#004f4f'
  tertiary-fixed: '#ffdad4'
  tertiary-fixed-dim: '#ffb4a8'
  on-tertiary-fixed: '#410100'
  on-tertiary-fixed-variant: '#8a1c10'
  background: '#fcf9f8'
  on-background: '#1b1c1c'
  surface-variant: '#e5e2e1'
typography:
  display-lg:
    fontFamily: Public Sans
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.02em
  title-md:
    fontFamily: Public Sans
    fontSize: 18px
    fontWeight: '700'
    lineHeight: 24px
    letterSpacing: -0.01em
  body-md:
    fontFamily: Public Sans
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 22px
    letterSpacing: 0em
  body-md-bold:
    fontFamily: Public Sans
    fontSize: 15px
    fontWeight: '700'
    lineHeight: 22px
    letterSpacing: 0em
  label-sm:
    fontFamily: Public Sans
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
    letterSpacing: 0.01em
  number-data:
    fontFamily: Public Sans
    fontSize: 15px
    fontWeight: '700'
    lineHeight: 20px
    letterSpacing: 0.02em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  sidebar_width: 260px
  main_content_width: 1660px
  grid_gap: 24px
  container_padding: 32px
  section_margin: 40px
---

## Brand & Style
The design system is engineered for public health data analysis, prioritizing institutional trust, absolute clarity, and administrative rigor. The target audience includes government officials, healthcare researchers, and policy makers who require a high-density information environment that minimizes cognitive load.

The visual style is **Corporate / Modern** with a lean toward **Minimalism**. It mirrors the structure of a formal administrative document—stable, objective, and authoritative. The UI avoids decorative elements, favoring grid-based alignment and clear information hierarchy to ensure that data remains the primary focus.

## Colors
This design system utilizes a palette rooted in professional stability. 

- **Primary (#1F4E78):** Used for global navigation, headers, and primary actions to establish an authoritative anchor.
- **Secondary (#008080):** Reserved for data visualization and positive metrics, offering a distinct but professional contrast to the primary navy.
- **Accent/Alert (#E05A47):** Used sparingly for critical warnings, negative growth, or data anomalies.
- **Surface (#F2F4F7):** Applied to sidebar backgrounds and card containers to separate functional areas without using heavy borders.
- **Text (#222222):** The standard for all body copy to ensure maximum legibility against light backgrounds.

## Typography
The typography system uses **Public Sans** (or a clean local Sans-serif equivalent like Pretendard/Noto Sans KR) to maintain a neutral, institutional feel. 

- **Data Emphasis:** All numerical values within tables and dashboards must use the bold weight (`number-data`) to ensure they are easily scannable.
- **Hierarchy:** Headlines use a tight letter-spacing to appear more grounded. Body text maintains standard spacing for prolonged reading.
- **Language:** For Korean characters, ensure a font with optimized hinting for small sizes is used to maintain the 15px body legibility.

## Layout & Spacing
This design system utilizes a **Fixed Grid** model optimized for 1920x1080 resolution, ensuring consistency across institutional workstations.

- **Structure:** A permanent 260px left-hand sidebar for primary navigation, with a 1660px main stage.
- **Main Stage Grid:** The content area is divided into a 2-column layout with a 62:38 ratio (approx. 1030px and 630px). This ratio is designed to host primary data tables/charts on the left and contextual analysis/metadata on the right.
- **Rhythm:** A 24px gutter is used between all cards and layout modules to provide breathing room while maintaining a high-density data feel.

## Elevation & Depth
To maintain an "administrative" feel, this design system avoids heavy shadows. Instead, it uses **Tonal Layers** and **Low-contrast outlines**.

- **Level 0 (Canvas):** Pure white (#FFFFFF) for the main workspace background.
- **Level 1 (Surfaces):** 연회색 (#F2F4F7) for sidebars and background containers.
- **Level 2 (Cards):** White cards placed on Level 1 surfaces, defined by a 1px border (#DDE2E8) rather than a shadow.
- **Interactive State:** Only primary buttons may have a subtle, high-diffusion shadow to indicate pressability.

## Shapes
The shape language is **Soft** (4px - 8px radius). This provides a modern touch to the professional aesthetic without feeling overly casual or consumer-oriented. 

- **Cards & Inputs:** Use a 4px (0.25rem) radius.
- **Action Buttons:** Use a 4px (0.25rem) radius for a "stamp" like feel.
- **Status Tags/Chips:** May use 8px (0.5rem) to distinguish them from interactive input fields.

## Components
Consistent component behavior is critical for data accuracy and user confidence.

- **Data Tables:** Use a strict 40px row height. Headers should have a light grey background (#F8F9FA) with `body-md-bold` text. Borders should be horizontal-only to encourage scanning across data points.
- **Cards:** White background, 1px border (#DDE2E8), 4px corner radius. Internal padding is fixed at 24px.
- **Horizontal Bar Charts:** Use Primary (#1F4E78) for standard data and Secondary (#008080) for the "target" or "current" metric. Bars should have a fixed height (e.g., 24px) with subtle 2px rounded ends.
- **Buttons:**
    - *Primary:* Solid #1F4E78 with White text.
    - *Secondary:* Ghost style with #1F4E78 border and text.
- **Input Fields:** 1px border (#CED4DA) that turns Primary (#1F4E78) on focus. Labels sit 8px above the field in `label-sm`.
- **Status Indicators:** Small circles (8px) using Secondary (Green) for 'Normal' and Accent (Coral) for 'Alert'.