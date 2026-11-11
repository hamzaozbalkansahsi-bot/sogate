/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/brand-preview.mjs
 * Açıklama   : Yerel kurulum, doğrulama veya operasyon komutunu yürütür.
 */
import { createRequire } from 'node:module';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const require = createRequire(import.meta.url);
let sharp;
try { sharp = require('sharp'); } catch {
  if (!process.env.BRAND_SHARP_PATH) throw new Error('Install app dependencies (sharp) or set BRAND_SHARP_PATH to the local bundled sharp package.');
  sharp = require(process.env.BRAND_SHARP_PATH);
}
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const brand = path.join(root, 'public/brand');
const preview = path.join(root, 'tmp/pdfs');
await mkdir(preview, { recursive: true });
for (const size of [16, 32]) {
  await sharp(await readFile(path.join(brand, 'favicon.svg'))).resize(size, size).png().toFile(path.join(brand, `favicon-${size}.png`));
}
await sharp(await readFile(path.join(brand, 'social-profile.svg'))).resize(48, 48).png().toFile(path.join(brand, 'profile-48.png'));
await sharp(await readFile(path.join(brand, 'social-profile.svg'))).png().toFile(path.join(brand, 'social-profile.png'));
await sharp(await readFile(path.join(brand, 'share-preview.svg'))).png().toFile(path.join(brand, 'share-preview.png'));
for (const file of ['logo-horizontal', 'logo-vertical', 'hero-silk', 'social-post-light', 'social-post-dark', 'social-product-dark', 'social-collection-light', 'social-information-light']) {
  await sharp(await readFile(path.join(brand, `${file}.svg`))).resize({ width: file === 'hero-silk' ? 1200 : 700 }).png().toFile(path.join(preview, `${file}.png`));
}
const layers = [];
for (const [i, name] of ['favicon-16.png', 'favicon-32.png', 'profile-48.png'].entries()) {
  layers.push({ input: await sharp(path.join(brand, name)).resize(192, 192, { kernel: 'nearest' }).toBuffer(), left: 40 + i * 240, top: 40 });
}
await sharp({ create: { width: 760, height: 270, channels: 4, background: '#FBF4EF' }}).composite(layers).png().toFile(path.join(preview, 'icon-scale-check.png'));
const xmlFiles = (await import('node:fs/promises')).readdir;
const files = [...await xmlFiles(brand), ...await xmlFiles(path.join(root, 'public/media'))];
const report = { checked: new Date().toISOString(), rendered: 13, rasterSizes: [16, 32, 48], svgFiles: files.filter(x => x.endsWith('.svg')).length };
await writeFile(path.join(preview, 'brand-check.json'), JSON.stringify(report, null, 2));
console.log(JSON.stringify(report));
