# 县城浮世绘 · 隐藏属性测试

从 32 道县城生活题里随机抽 6 道，答一道就能翻开一张隐藏属性卡。结果来自县城人物图鉴的 427 位在册人物。可以把手机交给身边的朋友，也可以把同一条邀请链接或海报发给多位好友。每位好友完成测评后，都会与你生成一张双人卡。

[打开测试](https://quiz.yuxuan.wiki/) · [试试领卡处](https://card.yuxuan.wiki/) · [翻阅人物图鉴](https://xian.yuxuan.wiki/)

## 本地预览

使用 Python 3.13，在仓库根目录运行以下命令。

```sh
git clone https://github.com/yuxuan6426/CountyUkiyoe.git .gallery-source
git -C .gallery-source checkout --detach 6c4154d4f5bf903d3ce6e944507a6106e23bc854
python build.py --output dist --site-url http://127.0.0.1:8104/
python -m http.server 8104 --bind 127.0.0.1 --directory dist
```

打开 [本地测试](http://127.0.0.1:8104/)。构建使用空目录，重新构建时为 `--output` 指定另一个空目录。已有这版公开图鉴也可通过 `--gallery-source` 传入。用 Node.js 22 或以上运行 `node --test tests/quiz.test.mjs` 验证抽题、计分、进度和双人链接。

## 发布

GitHub Actions 运行计分测试，生成静态 `dist/` 并部署到 Pages。发布包可以直接放到普通静态服务器，完整步骤见 [部署说明](DEPLOY.md)。

新版题目和人物分组在 [题库](src/questions.json) 和 [人物分组](src/pools.json)。分组根据图鉴档案中体现的行为整理，构建会校验每位在册人物都能抽到。答题在浏览器完成，分享链接只携带结果版本和公开人物编号。v1 结果由 [旧版题库](src/deck.json) 保留。肖像来源及使用许可见 [内容许可](ASSET-LICENSE.md)。

## 部署入口

| 站点 | GitHub Pages | 独立域名 |
| --- | --- | --- |
| 县城浮世绘人物图鉴 | [Pages](https://yuxuan6426.github.io/CountyUkiyoe/) | [Wiki](https://xian.yuxuan.wiki/) |
| 县城隐藏属性测试 | [Pages](https://yuxuan6426.github.io/CountyUkiyoe-Quiz/) | [Wiki](https://quiz.yuxuan.wiki/) |
| 县城浮世绘 AI 领卡处 | [Pages](https://yuxuan6426.github.io/CountyUkiyoe-Play/) | [Wiki](https://card.yuxuan.wiki/) |

## 目录与维护

```text
src/              题库、人物分组、模板与交互
vendor/           构建时的二维码编码器
tests/            抽题、进度、计分及链接回归
docs/             使用指引与开发记录
artifacts/        本地验收与发布暂存
dist/             构建输出
```

```sh
python build.py --gallery-source .gallery-source
node --test tests/quiz.test.mjs
```

生成目录为本次构建产物。代码遵循 [代码许可](LICENSE)，图鉴原创资产适用[图文许可](ASSET-LICENSE.md)。另见 [维护代理指引](AGENTS.md)、[AI 使用指引](docs/agent-guide.md)及[安全政策](SECURITY.md)。

## English overview

A browser-based quiz with early results and reusable invitations. Each guest completes a quiz independently and receives a pair card.
