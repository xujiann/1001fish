#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 _harvest_raw.json 的 Wikidata 物种去重、质量过滤后补进 fish.js，凑到 TARGET 条。
- 去重：学名(小写)已在精选 239 里的跳过；学名重复的跳过。
- 质量：中文名必须含 CJK 字符（否则只是拉丁名，弃）；优先有英文名的。
- 新条目 cat="more"，family/habitat/size 留空（前端显示 —）。
- 追加到 fish.js 尾部（幂等：若已存在 id>239 则拒绝重复追加）。
- 同时写 _harvest_imgmap.json {id: 图片URL}，供 download_harvest_imgs.py 下载。
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET = 1001

def load_curated():
    txt = open(os.path.join(ROOT, "fish.js"), encoding="utf-8").read()
    s, e = txt.index("["), txt.rindex("]")
    arr = re.sub(r"/\*.*?\*/", "", txt[s:e+1], flags=re.S)
    return json.loads(arr), txt

def has_cjk(s):
    return any("一" <= c <= "鿿" for c in s)

def main():
    curated, txt = load_curated()
    maxid = max(f["id"] for f in curated)
    if maxid > 239:
        print("fish.js 已含 id>239（当前 max=%d），疑似已追加，终止以免重复。" % maxid)
        sys.exit(1)
    have_sci = {f["sci"].lower() for f in curated}
    have_zh = {f["name"] for f in curated}

    raw = json.load(open(os.path.join(ROOT, "_harvest_raw.json"), encoding="utf-8"))
    # 质量过滤 + 去重
    seen = set()
    cand = []
    for r in raw:
        sci = (r.get("sci") or "").strip()
        zh = (r.get("zh") or "").strip()
        if not sci or not zh or not r.get("img"):
            continue
        if not has_cjk(zh):            # 中文名必须是真中文
            continue
        if zh == sci:                  # 中文名就是拉丁名，弃
            continue
        key = sci.lower()
        if key in have_sci or key in seen or zh in have_zh:
            continue
        seen.add(key)
        cand.append(r)
    # 优先有英文名的（notability 代理），其次按中文名排序，稳定
    cand.sort(key=lambda r: (r.get("en", "") == "", r["zh"]))

    need = TARGET - len(curated)
    picked = cand[:need]
    print("原料 %d，去重过滤后可用 %d，需补 %d，实取 %d" %
          (len(raw), len(cand), need, len(picked)))

    entries, imgmap = [], {}
    nid = maxid
    for r in picked:
        nid += 1
        en = (r.get("en") or "").strip()
        entries.append({
            "id": nid, "name": r["zh"], "name_en": en or r["zh"],
            "sci": r["sci"], "family": "", "family_en": "",
            "cat": "more", "habitat": "", "habitat_en": "", "size": "",
        })
        imgmap[str(nid)] = r["img"]

    body = ",\n".join(json.dumps(e, ensure_ascii=False) for e in entries)
    idx = txt.rindex("]")
    head = txt[:idx]
    j = head.rindex("}")
    newtxt = (head[:j+1] +
              ",\n\n/* ==== 第 3 批：Wikidata 自动补齐（cat=more 世界鱼类图鉴） ==== */\n" +
              body + "\n\n]" + txt[idx+1:])
    open(os.path.join(ROOT, "fish.js"), "w", encoding="utf-8").write(newtxt)
    json.dump(imgmap, open(os.path.join(ROOT, "_harvest_imgmap.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=0)
    print("已追加 %d 条到 fish.js，总计 %d 条。imgmap 写入 %d 条。" %
          (len(entries), len(curated) + len(entries), len(imgmap)))

if __name__ == "__main__":
    main()
