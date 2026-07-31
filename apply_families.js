// 把 _families.json 的科名写进 fish.js 里 cat=more 的空 family 条目。繁体转简体。逐行保结构。
const fs = require('fs');
const OpenCC = require('C:/Users/drxuj/Claude/Projects/1001art/node_modules/opencc-js');
const conv = OpenCC.Converter({ from: 't', to: 'cn' });
const path = 'C:/Users/drxuj/Claude/Projects/1001fish/fish.js';

const fam = JSON.parse(fs.readFileSync('C:/Users/drxuj/Claude/Projects/1001fish/_families.json', 'utf8'));
const lines = fs.readFileSync(path, 'utf8').split('\n');
let n = 0;
const out = lines.map(line => {
  const t = line.trim();
  if (!t.startsWith('{"id"')) return line;
  const hadComma = t.endsWith(',');
  const obj = JSON.parse(hadComma ? t.slice(0, -1) : t);
  if (obj.cat === 'more' && !obj.family && fam[obj.sci]) {
    const f = fam[obj.sci];
    if (f.zh) obj.family = conv(f.zh);
    if (f.la) obj.family_en = f.la;
    if (obj.family || obj.family_en) n++;
  }
  return JSON.stringify(obj) + (hadComma ? ',' : '');
});
fs.writeFileSync(path, out.join('\n'), 'utf8');
console.log('filled family on', n, 'entries');
