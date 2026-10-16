// Usage: node render_pngs.cjs [path to an installed sharp module]
const path = require('node:path');
const sharp = require(process.argv[2] || 'sharp');
const diagrams = ['casos-acceso', 'casos-paginas', 'casos-anuncios', 'secuencia-publicacion'];

async function main() {
  for (const name of diagrams) {
    const input = path.join(__dirname, `${name}.svg`);
    const output = path.join(__dirname, `${name}.png`);
    await sharp(input).png().toFile(output);
    const { width, height } = await sharp(output).metadata();
    console.log(`${name}.png: ${width} x ${height}`);
  }
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
