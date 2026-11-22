# 县城浮世绘 · 隐藏属性测试

八道熟人局情境题，从县城人物图鉴里测一张隐藏属性卡。把链接发给朋友，对方答完就能领一张双人搭档卡。单人卡和搭档卡都能生成带二维码的分享海报。

[打开测试](https://quiz.yuxuan.wiki/) · [试试领卡处](https://card.yuxuan.wiki/) · [翻阅人物图鉴](https://xian.yuxuan.wiki/)

## 本地预览

使用 Python 3.13，在仓库根目录运行以下命令。

```sh
python build.py --output dist --site-url http://127.0.0.1:8104/
python -m http.server 8104 --bind 127.0.0.1 --directory dist
```

打开 [本地测试](http://127.0.0.1:8104/)。构建使用空目录，重新构建时为 `--output` 指定另一个空目录。用 Node.js 22 或以上运行 `node --test tests/score.test.mjs` 验证计分和两人组合。

## 发布

GitHub Actions 运行计分测试，生成静态 `dist/` 并部署到 Pages。发布包可以直接放到普通静态服务器，完整步骤见 [部署说明](DEPLOY.md)。

题目、人物对照和搭档文案集中在 [题库](src/deck.json)。答题在浏览器完成，分享链接携带题库版本及公开角色编号。肖像来源及使用许可见 [内容许可](ASSET-LICENSE.md)。
