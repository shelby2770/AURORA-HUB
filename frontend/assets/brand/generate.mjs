// Generates every raster icon/splash from the brand SVG sources.
// Run from the frontend dir:  node assets/brand/generate.mjs
import sharp from "sharp";
import { readFileSync, mkdirSync, copyFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const FE = resolve(here, "../..");
const src = (f) => readFileSync(resolve(here, f));

const icon = src("aurora-icon.svg");
const iconRound = src("aurora-icon-round.svg");
const foreground = src("aurora-foreground.svg");
const maskable = src("aurora-maskable.svg");
const mark = src("aurora-mark.svg");

const out = (p) => {
  const abs = resolve(FE, p);
  mkdirSync(dirname(abs), { recursive: true });
  return abs;
};

async function png(svg, size, dest) {
  await sharp(svg, { density: 512 })
    .resize(size, size, { fit: "contain", background: { r: 0, g: 0, b: 0, alpha: 0 } })
    .png()
    .toFile(out(dest));
  console.log("  ", dest, `${size}x${size}`);
}

// Dark splash: solid #0a0a0a (matches capacitor backgroundColor) + centred mark.
async function splash(w, h, dest) {
  const m = Math.round(Math.min(w, h) * 0.32);
  const markPng = await sharp(mark, { density: 512 }).resize(m, m).png().toBuffer();
  await sharp({
    create: { width: w, height: h, channels: 4, background: { r: 10, g: 10, b: 10, alpha: 1 } },
  })
    .composite([{ input: markPng, gravity: "center" }])
    .png()
    .toFile(out(dest));
  console.log("  ", dest, `${w}x${h}`);
}

const ANDROID = "android/app/src/main/res";

console.log("vector icons");
const copySvg = (name, dest) => {
  copyFileSync(resolve(here, name), out(dest));
  console.log("  ", dest);
};
copySvg("aurora-icon.svg", "src/app/icon.svg"); // SVG favicon (Next file convention)
copySvg("aurora-icon.svg", "public/aurora-icon.svg");
copySvg("aurora-mark.svg", "public/aurora-mark.svg");

console.log("web icons");
await png(icon, 192, "public/icon-192.png");
await png(icon, 512, "public/icon-512.png");
await png(maskable, 512, "public/icon-maskable-512.png");
await png(icon, 180, "src/app/apple-icon.png");
// favicon source PNGs (assembled into .ico by ImageMagick afterwards)
await png(icon, 16, "public/.fav-16.png");
await png(icon, 32, "public/.fav-32.png");
await png(icon, 48, "public/.fav-48.png");

console.log("android launcher (legacy square)");
const legacy = { "mipmap-mdpi": 48, "mipmap-hdpi": 72, "mipmap-xhdpi": 96, "mipmap-xxhdpi": 144, "mipmap-xxxhdpi": 192 };
for (const [d, s] of Object.entries(legacy)) {
  await png(icon, s, `${ANDROID}/${d}/ic_launcher.png`);
  await png(iconRound, s, `${ANDROID}/${d}/ic_launcher_round.png`);
}

console.log("android adaptive foreground (108dp safe canvas)");
const fg = { "mipmap-mdpi": 108, "mipmap-hdpi": 162, "mipmap-xhdpi": 216, "mipmap-xxhdpi": 324, "mipmap-xxxhdpi": 432 };
for (const [d, s] of Object.entries(fg)) {
  await png(foreground, s, `${ANDROID}/${d}/ic_launcher_foreground.png`);
}

console.log("android splash (portrait / landscape / base)");
const portrait = { "mdpi": [320, 480], "hdpi": [480, 800], "xhdpi": [720, 1280], "xxhdpi": [960, 1600], "xxxhdpi": [1280, 1920] };
for (const [d, [w, h]] of Object.entries(portrait)) {
  await splash(w, h, `${ANDROID}/drawable-port-${d}/splash.png`);
  await splash(h, w, `${ANDROID}/drawable-land-${d}/splash.png`);
}
await splash(480, 320, `${ANDROID}/drawable/splash.png`);

console.log("done.");
