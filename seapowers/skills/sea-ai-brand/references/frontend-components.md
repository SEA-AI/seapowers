---
File: sea-ai-brand
Description: Core Frontend UI Component Library Reference
Creator: Claude
Date: 2026-05-09
---

# Frontend Components Library

Reference guide for reusable UI components from Core-Frontend/CoreComponents. Only read the section for components you need to use. All components follow SEA.AI design tokens and typography from `ui-coding.md`.

## Quick Index by Category

| Category | Components |
|----------|-----------|
| Buttons | DefaultButton, ButtonText, LinkButton, SectionButton, InteractionButton |
| Form Controls | Input, CheckBox, Toggle, Dropdown, OtpInput, Slider |
| Progress & Status | ProgressBar, CircularProgressBar, Pill, ExpireTag |
| Layouts & Containers | Panel, Menu, Modal, Notification, Bar |
| Typography & Labels | Typography, Label, ButtonText |
| Mobile-specific | MobileSlideUp, MobileControls |

---

## Buttons

### DefaultButton
**File:** `CoreComponents/Element/Button/DefaultButton.js`

Primary button component with multiple color variants and states.

**Props:**
```js
{
  children: node,                    // Button content
  color: string,                     // Color: "primary", "primary2-4", "danger", "success", "warning", "neutral", etc.
  disabled: bool,                    // Disable button
  ghost: bool,                       // Ghost style (outlined)
  onClick: func,                     // Click handler
  stretched: bool,                   // Full width
  flexGrow: bool,                    // Grow to fill flex container
  iconButton: bool,                  // Icon-only button
  vertical: bool,                    // Vertical icon layout
  rotateIcon: bool,                  // Rotate icon on interaction
  fitContent: bool,                  // Fit to content width
  smallIcon: bool,                   // Smaller icon size
  datatestid: string,                // Test ID
}
```

**Example:**
```jsx
<DefaultButton color="primary" onClick={handleClick}>
  Save Changes
</DefaultButton>

<DefaultButton color="danger" ghost disabled>
  Delete
</DefaultButton>
```

### ButtonText
**File:** `CoreComponents/Element/ButtonText/ButtonText.js`

Text-based button variant, lightweight styling.

**Props:** Similar to DefaultButton but optimized for text-only usage.

### LinkButton
**File:** `CoreComponents/Element/LinkButton/LinkButton.js`

Button styled as a hyperlink.

### SectionButton
**File:** `CoreComponents/Element/SectionButton/SectionButton.js`

Larger button for section navigation/headers.

### InteractionButton
**File:** `CoreComponents/Element/InteractionButton/InteractionButton.js`

Button with interaction feedback for real-time controls.

---

## Form Controls

### Input
**File:** `CoreComponents/Element/Input/Input.js`

Text input with optional unit display and validation.

**Props:**
```js
{
  placeholder: string,               // Placeholder text
  value: string,                     // Current value
  onChange: func,                    // Change handler (for normal inputs)
  onChangeSmall: func,               // Change handler (for small/JSON inputs)
  type: string,                      // "small" (JSON), "text", "number", "password"
  unit: string,                      // Unit to display (e.g., "km/h")
  unitLabel: string,                 // Unit label text
  showUnit: bool,                    // Show unit display
  unitDark: bool,                    // Dark theme for unit
  disabled: bool,                    // Disable input
  errorInput: bool,                  // Show error state
  onBlur: func,                      // Blur handler
  clearInput: bool,                  // Clear input when true
  datatestid: string,                // Test ID
}
```

**Example:**
```jsx
<Input
  placeholder="Enter speed"
  value={speed}
  onChange={(val) => setSpeed(val)}
  unit="km/h"
  unitLabel="Speed"
/>
```

### CheckBox
**File:** `CoreComponents/Element/CheckBox/CheckBox.js`

Checkbox with optional icon and label.

**Props:**
```js
{
  value: string,                     // Checkbox value (required)
  label: string,                     // Label text (required)
  checked: bool,                     // Checked state (required)
  onChange: func,                    // Change handler (required)
  Icon: element,                     // Optional icon component
}
```

**Example:**
```jsx
<CheckBox
  value="gps"
  label="Enable GPS"
  checked={gpsEnabled}
  onChange={(val, checked) => setGpsEnabled(checked)}
/>
```

### Toggle
**File:** `CoreComponents/Element/Toggle/Toggle.js`

On/off switch component.

**Props:**
```js
{
  checked: bool,                     // Checked state
  onChange: func,                    // Change handler
  disabled: bool,                    // Disable toggle
}
```

**Example:**
```jsx
<Toggle checked={darkMode} onChange={setDarkMode} />
```

### Dropdown
**File:** `CoreComponents/Element/Dropdown/Dropdown.js`

Select menu component.

**Props:** Check source file for full prop list including options, value, onChange.

### Slider
**File:** `CoreComponents/Element/Slider/Slider.js`

Range slider for numeric input.

### OtpInput
**File:** `CoreComponents/Element/OtpInput/OtpInput.js`

One-time password input with individual digit fields.

---

## Progress & Status

### ProgressBar
**File:** `CoreComponents/Element/ProgressBar/ProgressBar.js`

Horizontal progress indicator.

**Props:**
```js
{
  percentage: number,                // Progress 0-100 (default: 1.5)
  type: string,                      // Style variant (default: "default")
  viewProgress: bool,                // Show percentage text (default: false)
}
```

**Example:**
```jsx
<ProgressBar percentage={65} viewProgress={true} />
```

### CircularProgressBar
**File:** `CoreComponents/Element/CircularProgressBar/CircularProgressBar.js`

Circular progress indicator.

### Pill
**File:** `CoreComponents/Element/Pill/Pill.js`

Status badge component.

**Props:**
```js
{
  status: string,                    // "Connected", "NotConnected", "Connecting"
}
```

**Example:**
```jsx
<Pill status="Connected" />
```

### ExpireTag
**File:** `CoreComponents/Element/ExpireTag/ExpireTag.js`

Time-based expiration tag for warnings.

---

## Typography & Labels

### Typography
**File:** `CoreComponents/Element/Typography/Typography.js`

Semantic text component with style variants.

**Props:**
```js
{
  type: string,                      // "main-title-l", "main-title-m", "main-body-m", "main-body-s", "card-title-m", "card-label-s"
  children: node,                    // Text content
  color: string,                     // CSS color value or CSS variable
  tid: string,                       // Translation ID for i18n
  className: string,                 // Additional CSS classes
}
```

**Example:**
```jsx
<Typography type="main-title-l" color="white">
  Dashboard Title
</Typography>

<Typography type="card-label-s" color="var(--content-neutral-2)">
  STATUS
</Typography>
```

**Available types:**
- `main-title-l` — 40px, weight 500, large title
- `main-title-m` — 24px, weight 500, medium title
- `main-body-m` — 20px, weight 400, body text
- `main-body-s` — 16px, weight 400, small body text
- `card-title-m` — 24px, uppercase, card title
- `card-label-s` — 16px, weight 500, uppercase, card label

### Label
**File:** `CoreComponents/Element/Label/Label.js`

Simple label component for form fields.

---

## Layouts & Containers

### Panel
**File:** `CoreComponents/Panel/` (multiple variants)

Flexible container component with multiple layout options. Check folder for specific variants.

### Menu
**File:** `CoreComponents/Menu/` (multiple variants)

Menu and navigation components. Includes MenuButton, ModesButton, PanelButton.

### Modal
**File:** `CoreComponents/Modal/` (multiple variants)

Modal dialog container. Check folder for specific modal types.

### Notification
**File:** `CoreComponents/Notification/` (multiple variants)

Notification and alert components:
- InlineNotification
- BottomNotification
- SystemNotification
- PopUp
- InteractiveNotification
- AlarmTag

---

## Mobile-Specific

### MobileSlideUp
**File:** `CoreComponents/Element/MobileSlideUp/MobileSlideUp.js`

Slide-up panel for mobile interfaces.

### MobileControls
**File:** `CoreComponents/Menu/MobileControls/MobileControls.js`

Mobile-optimized control panel.

---

## Component Import Path

All components are available through the `core-components` package alias in Vite projects:

```jsx
import DefaultButton from 'core-components/Element/Button/DefaultButton';
import Typography from 'core-components/Element/Typography/Typography';
import Toggle from 'core-components/Element/Toggle/Toggle';
```

Or import from the full path in non-aliased contexts:

```jsx
import DefaultButton from 'CoreComponents/Element/Button/DefaultButton';
```

---

## Design System Integration

All components use theme tokens from `ui-coding.md`:
- **Surface colors:** `--surface-neutral-1` through `--surface-neutral-5`
- **Signal colors:** `--surface-primary-3`, `--surface-danger-3`, `--surface-warning-3`, `--surface-success-3`
- **Typography:** Barlow Semi Condensed font family
- **Spacing:** Uses consistent 8px base unit (4px, 8px, 12px, 16px, 24px, 32px)
- **Border radius:** 4px (chips), 8px (standard), 16px (large)

For colors not listed in a component's props, check the component's CSS file for CSS variables used.

---

## Finding Additional Components

Browse `CoreComponents/` for more components:
- `Element/` — Basic UI elements
- `Panel/` — Complex container layouts
- `Menu/` — Navigation and menu components
- `Notification/` — Alerts and notifications
- `Modal/` — Modal dialogs
- `Detection/` — Detection-specific visualizations
- `Map/` — Map components (maritime context)
- `Bar/` — Bar charts and data visualizations
- `Layout/` — Page layout structures
