---
name: accessibility-audit
description: WCAG accessibility compliance audit. Use when checking web apps for accessibility issues, ARIA compliance, keyboard navigation, screen reader support, color contrast, and inclusive design.
---

# Accessibility Audit (WCAG 2.2)

Perform a comprehensive accessibility audit covering these categories:

## 1. Perceivable

- **Images**: All `<img>` tags have meaningful `alt` attributes (not "image" or "photo")
- **Color contrast**: Text meets WCAG AA ratio (4.5:1 normal text, 3:1 large text)
- **Video/Audio**: Captions and transcripts provided
- **Text resizing**: Content readable at 200% zoom without horizontal scrolling
- **Sensory cues**: Information not conveyed by color, shape, or position alone

## 2. Operable

- **Keyboard navigation**: All interactive elements reachable via Tab/Shift+Tab
- **Focus indicators**: Visible focus styles on all interactive elements
- **Skip links**: "Skip to main content" link present
- **No keyboard traps**: Focus can always move away from any element
- **Touch targets**: Minimum 44x44px for mobile
- **Motion**: `prefers-reduced-motion` respected for animations

## 3. Understandable

- **Language**: `lang` attribute set on `<html>` element
- **Form labels**: All inputs have associated `<label>` elements
- **Error messages**: Clear, specific, and associated with the field
- **Consistent navigation**: Same navigation pattern across pages
- **Predictable behavior**: No unexpected context changes

## 4. Robust

- **Valid HTML**: Proper semantic structure, no duplicate IDs
- **ARIA usage**: Correct roles, states, and properties
- **ARIA landmarks**: `main`, `nav`, `banner`, `contentinfo` present
- **Live regions**: Dynamic content uses `aria-live` appropriately
- **Name/Role/Value**: Custom components expose correct semantics

## Audit Output Format

For each issue found, report:
```
### [Category] Issue Title
- **WCAG Criterion**: [e.g., 1.4.3 Contrast]
- **Level**: A / AA / AAA
- **Severity**: Critical / Major / Minor
- **Location**: [file:line or CSS selector]
- **Current**: [what's wrong]
- **Fix**: [how to fix it]
```

## Automated Checks

Run these when applicable:
- Check all `<img>` for `alt` attributes
- Scan CSS for hardcoded colors and check contrast ratios
- Verify all form `<input>` elements have labels
- Check for `tabindex` values > 0 (anti-pattern)
- Verify heading hierarchy (h1 -> h2 -> h3, no skips)
- Check for `aria-hidden="true"` on focusable elements (bug)
