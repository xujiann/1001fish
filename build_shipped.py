#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从母版 fish.full.js 生成上线版 fish.js —— 只保留本地已有图片的物种。
   图片是慢变量（跨境下载 17-68 秒/张），所以数据先到 5000，图片下多少就上多少。
   每次补完图重跑本脚本即可增量上线。同时重生成 credits.json。"""
import json, os, re, sys, urllib.parse

ROOT = os.path.dirname(os.path.abspath(__file__))

def load(path):
    txt = open(os.path.join(ROOT, path), encoding="utf-8").read()
    arr = re.sub(r"/\*.*?\*/", "", txt[txt.index("["):txt.rindex("]")+1], flags=re.S)
    return json.loads(arr)

def have_images():
    have = set()
    d = os.path.join(ROOT, "images")
    for f in os.listdir(d):
        if f.endswith(".jpg"):
            n = f[:-4]
            if n.isdigit() and os.path.getsize(os.path.join(d, f)) > 1500:
                have.add(int(n))
    return have

def commons_name(v):
    for key in ("src", "orig"):
        u = v.get(key) or ""
        if not u: continue
        u = urllib.parse.unquote(u.split("?")[0])
        for pat in (r"/commons/(?:thumb/)?[0-9a-f]/[0-9a-f]{2}/([^/]+)$",
                    r"/commons/thumb/[0-9a-f]/[0-9a-f]{2}/([^/]+)/",
                    r"Special:FilePath/(.+)$"):
            m = re.search(pat, u)
            if m: return m.group(1)
    t = v.get("title") or ""
    return t[5:] if t.startswith("File:") else ""

def main():
    full = load("fish.full.js")
    have = have_images()
    ship = [f for f in full if f["id"] in have]
    print("母版 %d 条 | 本地图 %d 张 | 上线 %d 条" % (len(full), len(have), len(ship)))

    header = ("/* 1001+ 种鱼 — 上线数据集（%d 条，均有真实照片）\n"
              "   由 build_shipped.py 从母版 fish.full.js 生成：只含本地已下载图片的物种。\n"
              "   母版共 %d 条，其余待图片下载完成后增量上线。 */\n" % (len(ship), len(full)))
    body = ",\n".join(json.dumps(e, ensure_ascii=False) for e in ship)
    open(os.path.join(ROOT, "fish.js"), "w", encoding="utf-8").write(
        header + "window.FISH_DATA = [\n" + body + "\n];\n")

    # credits：只给上线的物种
    man_path = os.path.join(ROOT, "_images.json")
    credits = {}
    if os.path.exists(man_path):
        man = json.load(open(man_path, encoding="utf-8"))
        for f in ship:
            v = man.get(str(f["id"]))
            if v and v.get("ok"):
                n = commons_name(v)
                if n: credits[str(f["id"])] = n
    # 补齐：新采集的图来自 imgmap（P18 URL），从中提取文件名
    for mapfile in ("_expand2_imgmap.json", "_harvest_imgmap.json"):
        p = os.path.join(ROOT, mapfile)
        if not os.path.exists(p): continue
        mp = json.load(open(p, encoding="utf-8"))
        for f in ship:
            k = str(f["id"])
            if k in credits: continue
            u = mp.get(k)
            if u:
                n = commons_name({"src": u})
                if n: credits[k] = n
    json.dump(credits, open(os.path.join(ROOT, "credits.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    print("credits.json: %d 条（覆盖 %.0f%%）" % (len(credits), 100*len(credits)/max(len(ship),1)))

    fams = len({f["family"] for f in ship if f.get("family")})
    print("上线科数: %d | 有科条目: %d" % (fams, sum(1 for f in ship if f.get("family"))))

if __name__ == "__main__":
    main()
