import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const staticDir = path.join(__dirname, 'web');   // the phone app (served by the PC at /app/ too)
const wwwDir = path.join(__dirname, 'www');

// Ensure www exists
if (!fs.existsSync(wwwDir)) {
  fs.mkdirSync(wwwDir, { recursive: true });
}

// Copy all static files into www
function copyRecursive(src, dest) {
  const stats = fs.statSync(src);
  if (stats.isDirectory()) {
    if (!fs.existsSync(dest)) fs.mkdirSync(dest, { recursive: true });
    fs.readdirSync(src).forEach(child => {
      copyRecursive(path.join(src, child), path.join(dest, child));
    });
  } else {
    fs.copyFileSync(src, dest);
  }
}

copyRecursive(staticDir, wwwDir);
console.log('✓ Copied phone app (web/) to www/');
