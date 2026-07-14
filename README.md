# 1001 种鱼 · 1001 Fishes

精选并展示世界上的 1001 种鱼类，从珊瑚礁的斑斓到深海的幽光。
A curated bilingual gallery of 1001 fishes, from coral reefs to the glow of the deep sea.

**在线浏览 / Live:** https://xujiann.github.io/1001fish/

## 内容

- **1001 个真实物种**：239 条手工精选（分 7 个主题类别：珊瑚礁 / 淡水观赏 / 大洋洄游 / 深海奇异 / 温带常见 / 特殊体型 / 珍稀活化石）+ 762 条来自 Wikidata 的补充（"世界鱼类图鉴"）。
- 每条含：中文名 · 英文俗名 · 拉丁学名 · 科 · 栖息水域 · 最大体长。
- 真实鱼类照片来自 Wikimedia Commons / Wikipedia。
- 中英双语切换、分类筛选、按科筛选、搜索、随机、键盘快捷键。

## 技术

纯静态单页（`index.html` + `style.css` + `app.js` + `fish.js`），无构建依赖。
图片经 jsDelivr CDN 分发（`xujiann/1001fish-img`），主仓不含图片。

## 数据管线（`*.py`）

- `harvest_wikidata.py` — 从 Wikidata SPARQL 采集有中文名 + 图片的鱼类物种。
- `build_from_harvest.py` — 去重、质量过滤，补齐到 1001。
- `fetch_images.py` / `download_harvest_imgs.py` — 按学名从 Wikipedia/Commons 取图，三级兜底 + 非照片过滤。

图片版权归各自作者所有（Wikimedia Commons，多为 CC 许可）。本站仅作教育/科普展示。
