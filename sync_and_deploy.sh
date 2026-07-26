#!/bin/bash
# 增量上线：图片下到哪就上线到哪。补完图后跑这一条命令即可。
#   用法: COS_SECRET_ID=xxx COS_SECRET_KEY=yyy bash sync_and_deploy.sh
set -e
cd "C:/Users/drxuj/OneDrive/claude/1001fish"

echo "== 1/5 从母版重建上线数据（只含已有图的物种）=="
python build_shipped.py

echo "== 2/5 目名繁转简 =="
node -e "
const fs=require('fs');
const OpenCC=require('C:/Users/drxuj/OneDrive/claude/1001art/node_modules/opencc-js');
const conv=OpenCC.Converter({from:'t',to:'cn'});
const p='fish.js'; const lines=fs.readFileSync(p,'utf8').split('\n'); let n=0;
const out=lines.map(l=>{const t=l.trim(); if(!t.startsWith('{\"id\"'))return l;
  const c=t.endsWith(','); const o=JSON.parse(c?t.slice(0,-1):t);
  if(o.order){const v=conv(o.order); if(v!==o.order){o.order=v;n++;}}
  return JSON.stringify(o)+(c?',':'');});
fs.writeFileSync(p,out.join('\n'),'utf8'); console.log('  转换',n,'条');
"

echo "== 3/5 挑出尚未上传 COS 的图 =="
rm -rf _upnew && mkdir -p _upnew
python - <<'PY'
import os, shutil, json, re
txt = open("fish.js", encoding="utf-8").read()
arr = re.sub(r"/\*.*?\*/", "", txt[txt.index("["):txt.rindex("]")+1], flags=re.S)
ship = sorted({f["id"] for f in json.loads(arr)})
up = set(json.load(open("_uploaded.json"))) if os.path.exists("_uploaded.json") else set()
todo = [i for i in ship if i not in up]
for i in todo:
    shutil.copy2("images/%d.jpg" % i, "_upnew/%d.jpg" % i)
print("  待传 %d 张（上线 %d 种）" % (len(todo), len(ship)))
PY

if [ "$(ls _upnew/*.jpg 2>/dev/null | wc -l)" -gt 0 ]; then
  echo "== 4/5 上传到腾讯云 COS =="
  python cos_upload.py _upnew fish --workers 10 | tail -2
  python - <<'PY'
import json, re
txt = open("fish.js", encoding="utf-8").read()
arr = re.sub(r"/\*.*?\*/", "", txt[txt.index("["):txt.rindex("]")+1], flags=re.S)
json.dump(sorted({f["id"] for f in json.loads(arr)}), open("_uploaded.json", "w"))
PY
else
  echo "== 4/5 无新图需上传 =="
fi

echo "== 5/5 打缓存版本号 + 提交部署 =="
# 静态资源加 ?v=时间戳，否则老访客会一直用缓存的旧 css/js 看不到更新
V=$(date +%Y%m%d%H%M)
python - "$V" <<'PY'
import io, re, sys
v = sys.argv[1]
p = "index.html"; s = io.open(p, encoding="utf-8").read()
for f in ("style.css", "fish.js", "app.js"):
    s = re.sub(r'(href|src)="%s(\?v=\d+)?"' % re.escape(f),
               lambda m: '%s="%s?v=%s"' % (m.group(1), f, v), s)
io.open(p, "w", encoding="utf-8").write(s)
p = "app.js"; a = io.open(p, encoding="utf-8").read()
a = re.sub(r'fetch\("credits\.json(\?v=\d+)?"\)', 'fetch("credits.json?v=%s")' % v, a)
io.open(p, "w", encoding="utf-8").write(a)
print("  版本号 %s" % v)
PY

N=$(python -c "import json,re;t=open('fish.js',encoding='utf-8').read();print(len(json.loads(re.sub(r'/\*.*?\*/','',t[t.index('['):t.rindex(']')+1],flags=re.S))))")
git add -A
git -c user.name=cosmos1001 -c user.email=popstudy@gmail.com commit -q -m "Sync: $N species live" || echo "  (无变更)"
git push origin main | tail -1
echo ""
echo "完成：$N 种已上线 https://xujiann.github.io/1001fish/"
