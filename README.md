# Miniloop Social Image Generator

Automated social media image generation for Twitter/X posts via GitHub Actions.

## Usage

Trigger the workflow via GitHub API or manually:

```bash
gh workflow run generate-image.yml \
  -f template=announcement \
  -f headline="Your headline here" \
  -f subheadline="Optional subheadline" \
  -f filename="output-name.png"
```

Or via API:
```javascript
github_trigger_workflow({
  owner: "wyattm14",
  repo: "imagerepo",
  workflow: "generate-image.yml",
  inputs: {
    template: "announcement",
    headline: "AI Employees for GTM",
    subheadline: "Set it and forget it delegation",
    filename: "gtm-launch-001.png"
  }
})
```

## Templates

| Template | Use Case | Style |
|----------|----------|-------|
| `announcement` | Big news, launches | Indigo/purple gradient, centered |
| `feature-launch` | Product features | Dark theme, left-aligned |
| `tip` | Educational content | Green gradient, centered |
| `listicle` | List-style posts | Blue gradient, left-aligned |
| `comparison` | vs/comparison content | Split amber, centered |

## Output

Generated images are saved to `output/` and can be accessed via:
```
https://raw.githubusercontent.com/wyattm14/imagerepo/main/output/{filename}
```

## Customization

### Fonts
Add custom fonts (Inter recommended) to `fonts/`:
- `Inter-Regular.ttf`
- `Inter-Bold.ttf`

Download: https://fonts.google.com/specimen/Inter

### Logo
Add `assets/logo.png` for watermark (auto-positioned bottom-right).

### Brand Colors
Edit `scripts/generate.py` to update the `COLORS` and `TEMPLATE_CONFIG` dictionaries.

## Image Specs

- Size: 1200x675px (Twitter optimal)
- Format: PNG
- Optimized for < 1MB file size
