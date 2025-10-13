# GitCloud Website

A modern, animated landing page for GitCloud - showcasing the intelligent cloud provisioning workflow.

## Features

- **Animated Workflow**: Interactive animation showing the complete process from GitHub to cloud deployment
- **Modern Design**: Dark theme with gradient accents, inspired by e2b.dev
- **Responsive**: Fully responsive design that works on all devices
- **Interactive Elements**:
  - Auto-play animation when section comes into view
  - Timeline navigation to jump between stages
  - Replay button to restart animation
  - Smooth scrolling and hover effects
  - Particle background for visual appeal

## Quick Start

### Option 1: Open Directly

Simply open `index.html` in your web browser:

```bash
cd website
open index.html  # macOS
# or
start index.html # Windows
# or
xdg-open index.html # Linux
```

### Option 2: Use a Local Server

For the best experience (especially for testing), use a local HTTP server:

**Using Python:**
```bash
cd website
python3 -m http.server 8000
# Visit http://localhost:8000
```

**Using Node.js (http-server):**
```bash
npm install -g http-server
cd website
http-server -p 8000
# Visit http://localhost:8000
```

**Using PHP:**
```bash
cd website
php -S localhost:8000
# Visit http://localhost:8000
```

## Project Structure

```
website/
├── index.html          # Main HTML file
├── css/
│   └── style.css       # All styles (dark theme, animations)
├── js/
│   └── main.js         # Interactive animations and effects
├── assets/             # Images and other assets (if needed)
└── README.md           # This file
```

## Key Sections

### 1. Hero Section
- Eye-catching title with gradient text
- Call-to-action buttons
- Installation command with copy functionality

### 2. Animated Workflow
The centerpiece of the website showing:
- **Stage 1**: GitHub Repository input
- **Stage 2**: AI Analysis with animated lines
- **Stage 3**: Cloud Provisioning with progress bars
- **Stage 4**: Running application with deployment info

Features:
- Auto-plays when scrolled into view
- Timeline navigation at bottom
- Replay button to restart animation
- Smooth transitions between stages

### 3. Features Grid
Six cards highlighting GitCloud's key features with hover effects

### 4. Call-to-Action
Final section encouraging users to get started

## Customization

### Colors

Edit CSS variables in `css/style.css`:

```css
:root {
    --color-bg: #0a0a0f;
    --color-accent: #6366f1;
    --gradient-primary: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    /* ... more variables */
}
```

### Animation Speed

Adjust animation timing in `js/main.js`:

```javascript
this.animationSpeed = 1500; // milliseconds per stage
```

### Content

Edit the HTML content in `index.html` to update:
- Repository examples
- Feature descriptions
- Installation commands
- Links and navigation

## Animation Controls

- **Auto-play**: Animation starts when the workflow section comes into view
- **Timeline**: Click timeline dots to jump to specific stages
- **Replay**: Click the "Replay Animation" button to restart
- **Keyboard**: Press 'R' to replay animation

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Performance

The website includes:
- Optimized CSS animations using `transform` and `opacity`
- Intersection Observer for efficient scroll detection
- Minimal JavaScript for smooth performance
- Canvas-based particle effect (can be disabled if needed)

To disable particle background, comment out this line in `js/main.js`:
```javascript
// createParticleBackground();
```

## Deployment

### GitHub Pages

1. Create a `gh-pages` branch:
```bash
git checkout -b gh-pages
git add website/*
git commit -m "Add website"
git push origin gh-pages
```

2. Enable GitHub Pages in repository settings

3. Your site will be available at: `https://yourusername.github.io/GitCloud/website/`

### Netlify

1. Drag and drop the `website` folder to [Netlify Drop](https://app.netlify.com/drop)
2. Or connect your repository and set build directory to `website`

### Vercel

```bash
cd website
vercel deploy
```

## Fonts

The website uses:
- **Inter**: Modern sans-serif for body text
- **JetBrains Mono**: Monospace for code blocks

Fonts are loaded from Google Fonts CDN.

## Development

### Making Changes

1. Edit HTML in `index.html`
2. Edit styles in `css/style.css`
3. Edit animations/interactions in `js/main.js`
4. Refresh browser to see changes

### Adding New Stages

To add a new workflow stage:

1. Add HTML in the workflow container
2. Add stage object in `js/main.js`:
```javascript
this.stages = [
    // existing stages...
    { id: 'stage-new', arrow: 'arrow-new', timeline: 4 }
];
```
3. Add corresponding CSS animations

## Credits

- Design inspired by [e2b.dev](https://e2b.dev/)
- Icons from inline SVG
- Fonts: Inter & JetBrains Mono
- Built for GitCloud CLI

## License

Same as GitCloud CLI project

## Support

For issues or questions:
- Open an issue in the main GitCloud repository
- Check the main project README for contact information
