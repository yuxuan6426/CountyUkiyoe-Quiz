# 隐藏属性测试部署

## GitHub Pages

仓库 Pages 的发布源选 GitHub Actions。推送 `main` 或手动运行 `Deploy quiz to GitHub Pages`，工作流会检出固定版本的公开图鉴、执行测试并发布 `dist/`。正式入口为 `https://quiz.yuxuan.wiki/`。

## 自有服务器

用计划对外公布的 HTTPS 地址重新构建，确保海报和网页卡片指向同一个地址。

```sh
python build.py --gallery-source .gallery-source --output dist-server --site-url https://quiz.yuxuan.wiki/
```

将 `dist-server/` 的内容放到对应的静态目录。服务器需为带尾部斜杠的页面返回其 `index.html`，并可将站点的 `404.html` 配为该路径下的自定义 404。切换到域名根路径时，把 `--site-url` 改为 `https://your-host.example/`。默认领卡入口为 `https://card.yuxuan.wiki/`，另行部署时可用 `--play-url` 指定目标。

在新发布目录放置构建产物，先预览首页、`r/v2/0055/`、`duo/v2/?a=0055&b=1190`，以及已有的 `r/v1/0055/` 和 `duo/v1/0055-0055/`。切换后核验提前翻卡、好友邀请和两种海报码的回流，保留上个目录以便回退。

页面、样式、脚本与海报处理都由静态站提供。新版结果按需展示公开图鉴站的原肖像，旧版结果继续使用随站发布的肖像。
