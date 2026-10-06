# 每日任务发布要求（待应用到现有云端任务）

保留两个原任务的选题要求、时间和时区。在原任务完成正文后追加以下发布要求，先手动试运行验证，再依赖定时执行。

将本次最终文章发布到 GitHub 仓库 shuke711/daily-reading-feed 的 main 分支。新闻路径为 content/news/YYYY-MM-DD.json，长文路径为 content/reads/YYYY-MM-DD.json，日期使用 Asia/Shanghai。JSON 包含 id、title、date_published、category、summary、content_text。category 分别为 news 或 reads。id 分别为 YYYY-MM-DD-news 或 YYYY-MM-DD-reads，重试时不得改变 id。日期使用带 +08:00 时区的 ISO 8601 值。content_text 包含完整可发布正文和来源网址，不使用 ChatGPT 内部引用标记。

发布前检查当天文件：存在时读取并更新，不新建另一篇重复文章。不允许删除历史文章、修改工作流或访问其他仓库。不发布私密信息。版权受限材料仅发布原创精读与少量必要引用。

若缺少连接、写入权限、需要审批或提交失败，明确报告失败；不得声称已更新 RSS。成功时报告提交链接。首次验收须确认：文件已入库、GitHub Actions 成功、RSS 中出现对应稳定 id 和完整正文、Reeder 抓取成功。
