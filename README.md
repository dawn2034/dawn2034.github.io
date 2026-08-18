# dawn2034.github.io

个人技术博客的 GitHub Pages 发布仓库，正式主题为 **Jekyll Chirpy**。

## 目录

- `DailyEpoch/`：每日 AI 技术简报 Markdown 源文件，继续使用 `YYYY-MM-DD.md` 命名。
- `DailyEpoch/CONTENT_GUIDE.md`：AI 日报内容、Markdown、LaTeX 与来源引用规范。
- `chirpy-src/`：Chirpy 站点配置、页面、样式及历史文章源文件。
- `chirpy-src/legacy-posts/`：迁移后的历史文章 Markdown 源文件。
- `.github/workflows/chirpy-site.yml`：整站构建、校验与静态发布工作流。

## 发布方式

`master` 同时保留内容源文件与 GitHub Pages 静态产物。

当以下内容发生变化时，GitHub Actions 会自动重新构建 Chirpy：

- `DailyEpoch/*.md`
- `chirpy-src/**`
- `Gemfile`

构建过程会：

1. 将所有 `DailyEpoch/YYYY-MM-DD.md` 临时复制为 Chirpy posts；
2. 合并 `chirpy-src/legacy-posts/` 中的历史文章；
3. 使用 `jekyll-theme-chirpy` 构建完整站点；
4. 校验日报数量、历史文章、CSS/JS 与旧预览 URL；
5. 将静态结果发布到 `master` 根目录，并使用 `.nojekyll` 由 GitHub Pages 直接提供静态文件。

因此，新增日报仍只需要提交：

```text
DailyEpoch/YYYY-MM-DD.md
```

无需手工维护首页、归档、分类、标签、搜索索引或 sitemap，它们由 Chirpy 自动生成。

## URL 约定

日报永久链接保持：

```text
/DailyEpoch/YYYY-MM-DD/
```

历史文章尽量保留原 permalink，避免旧链接失效。

生成、整理和提交日报前，必须按照 [`DailyEpoch/CONTENT_GUIDE.md`](DailyEpoch/CONTENT_GUIDE.md) 执行 Markdown 内容规范化与来源检查。
