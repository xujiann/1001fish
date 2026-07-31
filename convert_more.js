// 对 fish.js 里 cat=more 的条目：繁体名转简体 + 冗余 name_en(==sci) 置空。逐行保结构，幂等。
const fs = require('fs');
const OpenCC = require('C:/Users/drxuj/Claude/Projects/1001art/node_modules/opencc-js');
const conv = OpenCC.Converter({ from: 't', to: 'cn' });
const hasCJK = s => /[一-鿿]/.test(s);
const path = 'C:/Users/drxuj/Claude/Projects/1001fish/fish.js';

const lines = fs.readFileSync(path, 'utf8').split('\n');
let nConv = 0, nBlank = 0;
const out = lines.map(line => {
  const t = line.trim();
  if (!t.startsWith('{"id"')) return line;
  const hadComma = t.endsWith(',');
  const o = JSON.parse(hadComma ? t.slice(0, -1) : t);
  if (o.cat === 'more') {
    const c = conv(o.name); if (c !== o.name) { o.name = c; nConv++; }
    if (o.name_en) {
      if (o.name_en === o.sci) { o.name_en = ''; nBlank++; }
      else if (hasCJK(o.name_en)) o.name_en = conv(o.name_en);
    }
  }
  return JSON.stringify(o) + (hadComma ? ',' : '');
});
fs.writeFileSync(path, out.join('\n'), 'utf8');
console.log('converted', nConv, '| blanked name_en', nBlank);
