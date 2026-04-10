/**
 * Dream Academy — Playwright Renderer
 * Renders all HTML assets to PDF and PNG
 * Usage: npx playwright test render.js (or node render.js with playwright installed)
 */
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const ASSETS_DIR = __dirname;
const OUTPUT_DIR = path.join(__dirname, 'output');

async function render() {
  if (!fs.existsSync(OUTPUT_DIR)) fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  const browser = await chromium.launch();
  const context = await browser.newContext();

  // ── Helper: force fade-up elements visible ──
  async function forceVisible(page) {
    await page.evaluate(() => {
      document.querySelectorAll('.fade-up').forEach(el => {
        el.style.opacity = '1';
        el.style.transform = 'none';
      });
    });
  }

  // ── 1. Homepage → PDF ──
  console.log('Rendering homepage...');
  const homePage = await context.newPage();
  await homePage.goto(`file://${path.join(ASSETS_DIR, 'homepage.html')}`, { waitUntil: 'networkidle' });
  await forceVisible(homePage);
  await homePage.pdf({
    path: path.join(OUTPUT_DIR, 'dream-academy-homepage.pdf'),
    format: 'A4',
    printBackground: true,
    margin: { top: '0', bottom: '0', left: '0', right: '0' }
  });
  await homePage.close();

  // ── 2. Pitch Deck → PDF ──
  console.log('Rendering pitch deck...');
  const deckPage = await context.newPage();
  await deckPage.setViewportSize({ width: 1920, height: 1080 });
  await deckPage.goto(`file://${path.join(ASSETS_DIR, 'pitch-deck.html')}`, { waitUntil: 'networkidle' });
  await forceVisible(deckPage);
  await deckPage.pdf({
    path: path.join(OUTPUT_DIR, 'dream-academy-pitch-deck.pdf'),
    width: '1920px',
    height: '1080px',
    printBackground: true,
    margin: { top: '0', bottom: '0', left: '0', right: '0' },
    landscape: true
  });
  await deckPage.close();

  // ── 3. Audit Report → PDF ──
  console.log('Rendering audit report...');
  const auditPage = await context.newPage();
  await auditPage.goto(`file://${path.join(ASSETS_DIR, 'audit-report.html')}`, { waitUntil: 'networkidle' });
  await forceVisible(auditPage);
  await auditPage.pdf({
    path: path.join(OUTPUT_DIR, 'dream-academy-audit-report.pdf'),
    format: 'Letter',
    printBackground: true,
    margin: { top: '0.4in', bottom: '0.4in', left: '0.4in', right: '0.4in' }
  });
  await auditPage.close();

  // ── 4. Pricing Proposal → PDF ──
  console.log('Rendering pricing proposal...');
  const pricingPage = await context.newPage();
  await pricingPage.goto(`file://${path.join(ASSETS_DIR, 'pricing-proposal.html')}`, { waitUntil: 'networkidle' });
  await forceVisible(pricingPage);
  await pricingPage.pdf({
    path: path.join(OUTPUT_DIR, 'dream-academy-pricing-proposal.pdf'),
    format: 'Letter',
    printBackground: true,
    margin: { top: '0.4in', bottom: '0.4in', left: '0.4in', right: '0.4in' }
  });
  await pricingPage.close();

  // ── 5. Instagram Post → PNG (1080x1080) ──
  console.log('Rendering Instagram post...');
  const igPostPage = await context.newPage();
  await igPostPage.setViewportSize({ width: 1080, height: 1080 });
  await igPostPage.goto(`file://${path.join(ASSETS_DIR, 'ig-post.html')}`, { waitUntil: 'networkidle' });
  await forceVisible(igPostPage);
  await igPostPage.screenshot({
    path: path.join(OUTPUT_DIR, 'dream-academy-ig-post-1080x1080.png'),
    clip: { x: 0, y: 0, width: 1080, height: 1080 }
  });
  await igPostPage.close();

  // ── 6. Instagram Story → PNG (1080x1920) ──
  console.log('Rendering Instagram story...');
  const igStoryPage = await context.newPage();
  await igStoryPage.setViewportSize({ width: 1080, height: 1920 });
  await igStoryPage.goto(`file://${path.join(ASSETS_DIR, 'ig-story.html')}`, { waitUntil: 'networkidle' });
  await forceVisible(igStoryPage);
  await igStoryPage.screenshot({
    path: path.join(OUTPUT_DIR, 'dream-academy-ig-story-1080x1920.png'),
    clip: { x: 0, y: 0, width: 1080, height: 1920 }
  });
  await igStoryPage.close();

  // ── 7. Facebook Cover → PNG (1920x1005) ──
  console.log('Rendering Facebook cover...');
  const fbPage = await context.newPage();
  await fbPage.setViewportSize({ width: 1920, height: 1005 });
  await fbPage.goto(`file://${path.join(ASSETS_DIR, 'fb-cover.html')}`, { waitUntil: 'networkidle' });
  await forceVisible(fbPage);
  await fbPage.screenshot({
    path: path.join(OUTPUT_DIR, 'dream-academy-fb-cover-1920x1005.png'),
    clip: { x: 0, y: 0, width: 1920, height: 1005 }
  });
  await fbPage.close();

  // ── 8. Referral Card → PNG (672x total height) ──
  console.log('Rendering referral card...');
  const refPage = await context.newPage();
  await refPage.setViewportSize({ width: 672, height: 820 });
  await refPage.goto(`file://${path.join(ASSETS_DIR, 'referral-card.html')}`, { waitUntil: 'networkidle' });
  await forceVisible(refPage);
  // Front
  await refPage.screenshot({
    path: path.join(OUTPUT_DIR, 'dream-academy-referral-card-front-672x384.png'),
    clip: { x: 0, y: 0, width: 672, height: 384 }
  });
  // Full (front + back)
  await refPage.screenshot({
    path: path.join(OUTPUT_DIR, 'dream-academy-referral-card-full.png'),
    fullPage: true
  });
  await refPage.close();

  await browser.close();
  console.log(`\n✅ All assets rendered to ${OUTPUT_DIR}/`);
  console.log(fs.readdirSync(OUTPUT_DIR).map(f => `  → ${f}`).join('\n'));
}

render().catch(err => { console.error(err); process.exit(1); });
