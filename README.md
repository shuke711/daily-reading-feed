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

新闻存入 `content/news/YYYY-MM-DD.json`，长文存入 `content/reads/YYYY-MM-DD.json`。每个 JSON 是一篇文章，字段参照测试文章。`id` 永久不变，日期须包含时区。正文 `content_text` 是纯文本，用空行分段，可包含完整来源网址。全文直接嵌入 Feed，所有历史文章保留。测试文章明确标注，不冒充真实日报。

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
