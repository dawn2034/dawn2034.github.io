---
title: DailyEpoch
icon: fas fa-newspaper
order: 1
permalink: /DailyEpoch/
---

每日 AI 技术简报，面向资深 AI／推荐算法从业者，聚焦 LLM、Agent、RL、RAG、量化、长上下文、推荐系统与基础设施。

{% assign daily_posts = site.categories.DailyEpoch %}
{% for post in daily_posts %}
- [{{ post.date | date: "%Y-%m-%d" }}｜{{ post.title }}]({{ post.url | relative_url }})
{% endfor %}
