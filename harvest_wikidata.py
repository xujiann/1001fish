#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 Wikidata 采集"有中文名 + 有图片"的真实鱼类物种，累积合并进 _harvest_raw.json。

⚠️ 历史教训：最初版本用了错误的 QID（Q127595 其实是"鲈形目"，Q83367 是《塔纳赫》，
   Q129604 是一张音乐专辑，Q599909 是法国村庄），导致只采到鲈形目、其余类群全返回 0。
   下面的 QID 已用 P225(taxon name) 反查校验过。

用法: python harvest_wikidata.py [taxon名...]   不带参数=全部
"""
import json, os, sys, time, urllib.parse, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "_harvest_raw.json")
UA = "1001fish/1.0 (educational bilingual fish gallery; popstudy@gmail.com)"
ENDPOINT = "https://query.wikidata.org/sparql"

# 已校验的正确 QID（P225 反查）
TAXA = {
    "Chondrichthyes": "Q25371",    # 软骨鱼纲（鲨、鳐、银鲛）
    "Sarcopterygii":  "Q160830",   # 肉鳍鱼超纲（腔棘鱼、肺鱼）
    "Agnatha":        "Q161095",   # 无颌类（七鳃鳗、盲鳗）
    "Cyclostomata":   "Q500266",   # 圆口纲
    "Actinopterygii": "Q127282",   # 辐鳍鱼超纲（最大，最后跑）
}

def sparql(query, tries=6, timeout=300):
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": query, "format": "json"})
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA, "Accept": "application/sparql-results+json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))["results"]["bindings"]
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and a < tries - 1:
                print("    HTTP %d, 等 65s 重试..." % e.code); sys.stdout.flush()
                time.sleep(65); continue
            raise
        except Exception as e:
            if a < tries - 1:
                print("    %s, 等 30s 重试..." % type(e).__name__); sys.stdout.flush()
                time.sleep(30); continue
            raise

def harvest(qid, limit=None, offset=0):
    lim = ("LIMIT %d OFFSET %d" % (limit, offset)) if limit else ""
    q = """
    SELECT ?item ?sci ?zh (SAMPLE(?en) AS ?enName) (SAMPLE(?img) AS ?image) WHERE {
      ?item wdt:P171* wd:%s ;
            wdt:P105 wd:Q7432 ;
            wdt:P225 ?sci ;
            wdt:P18 ?img ;
            rdfs:label ?zh . FILTER(LANG(?zh)="zh")
      OPTIONAL { ?item rdfs:label ?en . FILTER(LANG(?en)="en") }
    } GROUP BY ?item ?sci ?zh %s
    """ % (qid, lim)
    return sparql(q)

def load_existing():
    if os.path.exists(RAW):
        data = json.load(open(RAW, encoding="utf-8"))
        return {d["qid"]: d for d in data}
    return {}

def main():
    want = sys.argv[1:] or list(TAXA.keys())
    out = load_existing()
    print("已有 %d 条，开始采集: %s" % (len(out), ", ".join(want)))
    for name in want:
        qid = TAXA.get(name)
        if not qid:
            print("跳过未知类群 %s" % name); continue
        before = len(out)
        try:
            rows = harvest(qid)
        except Exception as e:
            print("%-16s 失败: %s" % (name, str(e)[:70])); continue
        for r in rows:
            qidv = r["item"]["value"].rsplit("/", 1)[-1]
            if qidv in out: continue
            out[qidv] = {"qid": qidv, "sci": r["sci"]["value"], "zh": r["zh"]["value"],
                         "en": r.get("enName", {}).get("value", ""),
                         "img": r.get("image", {}).get("value", ""), "cls": name}
        json.dump(list(out.values()), open(RAW, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=0)
        print("%-16s 返回 %5d 行，新增 %5d 条（累计 %d）" % (name, len(rows), len(out)-before, len(out)))
        sys.stdout.flush()
        time.sleep(20)
    print("=== 完成，_harvest_raw.json 共 %d 条 ===" % len(out))

if __name__ == "__main__":
    main()
