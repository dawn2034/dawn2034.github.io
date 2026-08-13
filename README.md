# dawn2034.github.io

个人技术博客的 GitHub Pages 发布仓库。

## 目录

- `DailyEpoch/`：每日 AI 技术简报 Markdown 源文件。
- `_layouts/dailyepoch.html`：DailyEpoch 的 NexT 风格页面布局。
- `css/dailyepoch.css`：日报与新首页的响应式样式。
- `js/dailyepoch.js`：旧页面兼容、导航、引用标识与代码复制。
- `2018/`、`2019/`：历史 Hexo 静态文章。

## 发布方式

GitHub Pages 从 `master` 分支根目录构建，使用 Jekyll 处理带 Front Matter 的 Markdown 页面，同时保留历史静态 HTML。

## 内容约定

新增日报时放入：

```text
DailyEpoch/YYYY-MM-DD.md
```

并至少包含 `title`、`date`、`permalink`。`_config.yml` 会自动应用 `dailyepoch` 布局；首页、搜索索引和 sitemap 会自动发现日期格式的日报页面。
