# 隐藏属性测试部署

## GitHub Pages

仓库 Pages 的发布源选 GitHub Actions。推送 `main` 或手动运行 `Deploy quiz to GitHub Pages`，工作流会测试计分、构建并发布 `dist/`。默认公开地址是 `https://yuxuan6426.github.io/CountyUkiyoe-Quiz/`。

## 自有服务器

用计划对外公布的 HTTPS 地址重新构建，确保海报和网页卡片指向同一个地址。

```sh
python build.py --output dist-server --site-url https://your-host.example/quiz/
```

将 `dist-server/` 的内容放到对应的静态目录。服务器需为带尾部斜杠的页面返回其 `index.html`，并可将站点的 `404.html` 配为该路径下的自定义 404。切换到域名根路径时，把 `--site-url` 改为 `https://your-host.example/`。若领卡处也已迁移，用 `--play-url` 设置新地址。

部署后打开首页、任一个 `r/v1/<编号>/` 及任一个 `duo/v1/<编号>-<编号>/`，打开一张单人及双人海报，用手机扫码确认都返回当前域名。保留旧的 `v1` 路径或以相同路径重定向，让此前发出的二维码和结果链接继续可用。

当前版本的页面、样式、脚本、肖像和海报处理均可由同一静态服务器提供。中国大陆各地区的实际访问效果应在目标服务器上线后检测。
