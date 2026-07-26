#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二轮扩展：从 _harvest_raw.json 补到 TARGET 种。
   优先级：有英文俗名的（文献记载更充分、更知名）> 其余；同级按中文名排序保证可复现。
   输出：追加到 fish.js（cat=more），写 _expand2_imgmap.json 供下载。"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET = int(sys.argv[1]) if len(sys.argv) > 1 else 5000

def load_cur():
    txt = open(os.path.join(ROOT, "fish.js"), encoding="utf-8").read()
    arr = re.sub(r"/\*.*?\*/", "", txt[txt.index("["):txt.rindex("]")+1], flags=re.S)
    return json.loads(arr), txt

def has_cjk(s): return any("一" <= c <= "鿿" for c in s)

def main():
    cur, txt = load_cur()
    maxid = max(f["id"] for f in cur)
    have_sci = {f["sci"].lower() for f in cur}
    have_zh  = {f["name"] for f in cur}

    raw = json.load(open(os.path.join(ROOT, "_harvest_raw.json"), encoding="utf-8"))
    seen, cand = set(), []
    for r in raw:
        sci = (r.get("sci") or "").strip(); zh = (r.get("zh") or "").strip()
        if not sci or not zh or not r.get("img"): continue
        if not has_cjk(zh) or zh == sci: continue
        k = sci.lower()
        if k in have_sci or k in seen or zh in have_zh: continue
        seen.add(k); cand.append(r)
    # 有英文名的排前（notability 代理），其次按中文名，稳定可复现
    cand.sort(key=lambda r: (not (r.get("en") or "").strip(), r["zh"]))

    need = max(0, TARGET - len(cur))
    picked = cand[:need]
    withEn = sum(1 for r in picked if (r.get("en") or "").strip())
    print("现有 %d，候选 %d，需补 %d，实取 %d（其中有英文名 %d）"
          % (len(cur), len(cand), need, len(picked), withEn))

    entries, imgmap = [], {}
    nid = maxid
    for r in picked:
        nid += 1
        en = (r.get("en") or "").strip()
        entries.append({"id": nid, "name": r["zh"], "name_en": en or r["zh"],
                        "sci": r["sci"], "family": "", "family_en": "",
                        "cat": "more", "habitat": "", "habitat_en": "", "size": ""})
        imgmap[str(nid)] = r["img"]

    body = ",\n".join(json.dumps(e, ensure_ascii=False) for e in entries)
    idx = txt.rindex("]"); head = txt[:idx]; j = head.rindex("}")
    newtxt = (head[:j+1] + ",\n\n/* ==== 第二轮扩展：Wikidata 全类群采集（cat=more） ==== */\n"
              + body + "\n\n]" + txt[idx+1:])
    open(os.path.join(ROOT, "fish.js"), "w", encoding="utf-8").write(newtxt)
    json.dump(imgmap, open(os.path.join(ROOT, "_expand2_imgmap.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=0)
    print("fish.js 现有 %d 条，待下载新图 %d 张" % (len(cur)+len(entries), len(imgmap)))

if __name__ == "__main__":
    main()
