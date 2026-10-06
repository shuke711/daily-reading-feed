# 每日任务发布要求（待应用到现有云端任务）

保留两个原任务的选题要求、时间和时区。在原任务完成正文后追加以下发布要求，先手动试运行验证，再依赖定时执行。

将本次最终文章发布到 GitHub 仓库 shuke711/daily-reading-feed 的 main 分支。新闻路径为 content/news/YYYY-MM-DD.json，独立长文路径为 content/news/YYYY-MM-DD-reads.json，日期使用 Asia/Shanghai。兼容历史 content/reads/ 目录；已存在的文章继续更新原路径，不挪动或新建副本。新闻和长读保持独立文章，由 category 分类。JSON 包含 id、title、date_published、category、summary、content_text。category 分别为 news 或 reads。id 分别为 YYYY-MM-DD-news 或 YYYY-MM-DD-reads，重试时不得改变 id。日期使用带 +08:00 时区的 ISO 8601 值。content_text 包含完整可发布正文和来源网址，不使用 ChatGPT 内部引用标记。

新闻必须另外写入结构化 `news_items`：每条包含 `title`、正文段落数组 `body`、`why_it_matters`、来源对象数组 `sources`（`name`、绝对 HTTPS `url`）。导读用 `intro` 段落数组，编后说明用 `afterword`，附带长读用 `sections`（`title`、`paragraphs`、可选 `sources`）。不要把全部内容只写成 `content_text`。源文件的纯文本与结构化正文同步保持完整。具体示例见 README。

图片按条目选择：8 条新闻通常配 2–4 张有帮助的原文图片，不要求每条都有。每张图填写 `image.url`（公开直接图片地址）、`alt`、`caption`、`credit`、`source_url`；没有可靠图片就省略 `image`。发布前检查图片成功响应并确认为图片，保留署名，勿冒用无关图片或把推测图当现场照片。不传原始 HTML、Markdown 加粗或对英文单词逐个强调。

修改当天已发布文章时保留稳定 ID 和 `date_published`，新增或更新 `date_modified` 为实际修改时间；不要新建重复文章以规避客户端缓存。

发布前检查当天文件：存在时读取并更新，不新建另一篇重复文章。不允许删除历史文章、修改工作流或访问其他仓库。不发布私密信息。版权受限材料仅发布原创精读与少量必要引用。

若缺少连接、写入权限、需要审批或提交失败，明确报告失败；不得声称已更新 RSS。成功时报告提交链接。首次验收须确认：文件已入库、GitHub Actions 成功、RSS 中出现对应稳定 id 和完整正文、Reeder 抓取成功。
