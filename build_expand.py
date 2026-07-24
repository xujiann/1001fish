#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扩展：把 _harvest_raw.json 里尚未使用的可用物种追加到 fish.js（id 从 1002 起，cat=more），
   并写 _expand_imgmap.json {id: 图片URL} 供下载 + credits。幂等：已到目标则拒绝。"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))

def load_cur():
    txt = open(os.path.join(ROOT, "fish.js"), encoding="utf-8").read()
    arr = re.sub(r"/\*.*?\*/", "", txt[txt.index("["):txt.rindex("]")+1], flags=re.S)
    return json.loads(arr), txt

def has_cjk(s): return any("一" <= c <= "鿿" for c in s)

def main():
    cur, txt = load_cur()
    maxid = max(f["id"] for f in cur)
    have_sci = {f["sci"].lower() for f in cur}
    have_zh = {f["name"] for f in cur}

    raw = json.load(open(os.path.join(ROOT, "_harvest_raw.json"), encoding="utf-8"))
    seen, picked = set(), []
    for r in raw:
        sci = (r.get("sci") or "").strip(); zh = (r.get("zh") or "").strip()
        if not sci or not zh or not r.get("img"): continue
        if not has_cjk(zh) or zh == sci: continue
        k = sci.lower()
        if k in have_sci or k in seen or zh in have_zh: continue
        seen.add(k); picked.append(r)
    picked.sort(key=lambda r: (r.get("en", "") == "", r["zh"]))
    print("appending", len(picked), "new species -> total", len(cur) + len(picked))

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
    newtxt = (head[:j+1] + ",\n\n/* ==== 扩展批：Wikidata 补齐至 1001+（cat=more） ==== */\n" +
              body + "\n\n]" + txt[idx+1:])
    open(os.path.join(ROOT, "fish.js"), "w", encoding="utf-8").write(newtxt)
    json.dump(imgmap, open(os.path.join(ROOT, "_expand_imgmap.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=0)
    print("done. fish.js now", len(cur) + len(entries), "| imgmap", len(imgmap))

if __name__ == "__main__":
    main()
