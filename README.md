# 每日阅读 Feed

用于个人订阅的公开站点。文章与 Feed 均公开访问，不要提交个人隐私或凭据。

## 状态

已准备内容目录、全文 RSS/JSON Feed 生成器、GitHub Actions 构建和 Pages 发布配置。每日 ChatGPT 内容写入尚待接通并验证。定时构建只重建已有文章，不会生成新闻或自动读取 ChatGPT 历史。

## 地址（部署成功后有效）

- 首页：https://shuke711.github.io/daily-reading-feed/
- 合并 RSS：https://shuke711.github.io/daily-reading-feed/feed.xml
- 新闻 RSS：https://shuke711.github.io/daily-reading-feed/news.xml
- 长文 RSS：https://shuke711.github.io/daily-reading-feed/reads.xml
- JSON Feed：以上 `.xml` 换成 `.json`

Reeder 中选择添加订阅，粘贴 RSS 地址并确认；只订阅合并 Feed，或分别订阅新闻和长文，避免重复。

## 内容格式

新闻存入 `content/news/YYYY-MM-DD.json`，独立长读可以共用目录，存入 `content/news/YYYY-MM-DD-reads.json`，也兼容原有 `content/reads/` 目录。Feed 按 `category` 分类，不按所在目录分类。每个 JSON 是一篇文章，字段参照测试文章。`id` 永久不变，日期须包含时区。正文 `content_text` 是纯文本，用空行分段，可包含完整来源网址。全文直接嵌入 Feed，所有历史文章保留。测试文章明确标注，不冒充真实日报。

### 新闻版式与图片

新简报使用 `news_items` 结构生成 HTML，而不是从纯文本猜标题或把英文词加粗。生成器输出编号 `h2` 标题、正文段落、`h3` 关注理由和可点击的来源；新闻之间用分隔线。旧文章没有 `news_items` 时继续按原纯文本格式构建，无需迁移或删除。

```json
{
  "intro": ["今天的导读。"],
  "news_items": [
    {
      "title": "新闻标题",
      "body": ["发生了什么。", "必要背景。"],
      "why_it_matters": "为什么值得关注。",
      "sources": [{"name": "媒体名称", "url": "https://example.org/news"}],
      "image": {
        "url": "https://example.org/photo.jpg",
        "alt": "图片的具体内容",
        "caption": "图片说明",
        "credit": "摄影师 / 媒体",
        "source_url": "https://example.org/news"
      }
    }
  ],
  "afterword": ["可选编后说明。"],
  "sections": [
    {"title": "今日长读", "paragraphs": ["长读正文。"],
     "sources": [{"name": "阅读原文", "url": "https://example.org/read"}]}
  ],
  "date_modified": "2026-10-06T17:00:00+08:00"
}
```

以上字段与原有必填字段一起使用。`image` 完全可选，无图时省略整个字段；图片必须是公开、可直接加载的绝对 HTTPS 地址，并填写替代文本、说明和署名。不使用网站页面地址作为图片地址。8 条新闻通常选择 2–4 张有信息价值的原文图片；没有可靠配图时允许无图，不凑图。生成器不抓图、不根据来源网站猜图，也不强制每条配图。

结构化字段是正文的依据，构建时同时生成一致的 `content_text` 和 `content_html`。源文件的 `content_text` 保留纯文本备用，发布时应同步更新。所有文本均转义，不能直接插入 HTML；不输出 `strong`/`b` 标签，不对英文词逐个添加视觉强调。标题的层级由阅读器显示。

### 阅读器兼容与更新

RSS 2.0 的 `content:encoded` 和 `description` 都包含完整 HTML，兼顾只读取其中一个字段的阅读器；JSON Feed 1.1 提供 `content_html`、纯文本和摘要。图片使用普通 `img`，不依赖脚本、懒加载或站点 CSS，宽度自适应。Feed URL、文章 URL、GUID 和 JSON Feed ID 保持不变。

编辑当天文章时保留 `date_published`，更新带时区的 `date_modified`。RSS 提供 `atom:updated` 和更新后的 `lastBuildDate`，JSON Feed 提供 `date_modified`。客户端缓存更新策略不同，这些字段不能保证 Reeder 自动替换已经缓存的旧正文。验收应分别确认 Actions 成功、公开 Feed 的实际正文，以及 Reeder 刷新后的显示；只有真实客户端显示确认后才称为 Reeder 实机验收通过。

## 云端发布

新建公开仓库 `shuke711/daily-reading-feed`，默认分支 main。上传本目录（含隐藏的 `.github` 目录）。Settings → Pages → Source 选择 GitHub Actions，然后运行工作流。新文章提交后自动构建发布；每六小时重建一次作为补偿，也可手动运行。运行完全在 GitHub 云端，不需要本地电脑开机。GitHub 定时任务可能延迟，长期不活跃的公开仓库可能停用定时运行；新增文章的 push 仍会触发发布。

## 接入 ChatGPT

参照 `docs/task-publishing.md`。必须在实际云端定时任务中验证仓库写入权限；本次交互可写仓库不代表已有定时任务自动获得权限。不要把本地 Codex 自动化当作云端方案。若现有任务无法自动写入，需另选云端执行方式；OpenAI API 路线需要单独授权及计费。

## 本地验证（仅供维护）

Python 3.12，无第三方依赖：

```sh
python -m unittest discover -s scripts -p 'test_*.py'
python scripts/build.py --base-url https://shuke711.github.io/daily-reading-feed
```

本地验证并非日常运行所必需。
