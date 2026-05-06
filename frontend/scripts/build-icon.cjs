const sharp = require('sharp')
const path = require('path')
const fs = require('fs')

const svgPath = path.join(__dirname, '..', 'public', 'icon.svg')
const pngPath = path.join(__dirname, '..', 'public', 'icon.png')

async function main() {
  const svgBuffer = fs.readFileSync(svgPath)
  await sharp(svgBuffer)
    .resize(512, 512)
    .png()
    .toFile(pngPath)
  console.log(`Icon generated: ${pngPath}`)
}

main().catch(console.error)
