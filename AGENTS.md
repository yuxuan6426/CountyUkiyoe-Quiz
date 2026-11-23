# 县城隐藏属性测试维护指引

`catalog.py` 固定公开图鉴版本。保留原有结果、邀请及二维码地址。变更抽题和分享功能时，均运行测评测试并核对两个环境的站际链接。

## 构建和验收

- `python build.py --gallery-source .gallery-source`
- `node --test tests/quiz.test.mjs`

在空目录构建，以 `release.sha256` 核对产物，并通过 HTTP 验证桌面和移动端。Pages 与 Wiki 入口分别生成本站址和站际链接。只将公开数据和列入构建规则的文件放进发布目录。许可及第三方依赖见 README。
