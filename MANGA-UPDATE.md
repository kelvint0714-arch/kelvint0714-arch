# 黑白漫画 / 哥特体更新包

## 安装目标

`kelvint0714-arch/kelvint0714-arch` 的 main 分支。不是 `.github.io` 网站仓库。

这是增量更新包，依赖原仓库中未改动的 `garden.json`、`scripts/garden/data.py` 和 `data/snapshot.json`。不是一个替代完整仓库的独立工程。

## 网页上传

1. 解压 ZIP；进入原个人资料仓库的根目录。
2. 选择 Add file → Upload files。
3. 同时上传解压后的 `assets/`、`scripts/`、`README.md`、`MAINTENANCE.md`、`MANGA-UPDATE.md`。
4. 不要上传 ZIP 本身，也不要将最外层文件夹套进去；不要把整包拖到仓库的 assets/ 目录里。
5. 提交到 main，提交信息建议 `Restyle profile in monochrome manga and blackletter`。
6. 等 Actions 中 Tend the garden 运行成功后，再刷新个人主页。

README 必须更新，新的仓库分镜图片和手机版本才会被引用。scripts 必须更新，后续每日刷新才会继续使用漫画样式。assets 包含全部 28 张图。

## 不包含、也不应被覆盖的内容

视频横幅与静态封面、banners/、原数据快照、garden.json、.github/、字体文件、旧花卉模块和纪念碑谷独立网站。上方横幅的 README 区域已逐字比对，保持不变。

## 检查记录

- 保留的原 7 项测试通过；新增 20 项测试通过，共 27 项。
- Python 编译检查通过，28 份 SVG 均为合法 XML。
- 浅深色、桌面/手机的四份日历均核对了 371 个日期的计数与等级。
- 320、390、600、601、900、1440 宽度 × 浅深色，共 12 组本地 Chromium 布局检查；图片均载入，四种图片源选择正确，没有整页横向溢出。
- 两项仓库分镜外部链接与文字索引链接一致；索引可展开。
- 28 张 SVG 的文字边界均位于其 viewBox 内。
- 当前工作没有向远程仓库写入；没有执行 GitHub 线上渲染验证或手机实机测试。
- 头像图片链接未读取成功；视觉方向依据用户描述，不声称已经逐项匹配头像。

## 回滚

在 GitHub 中撤销本次上传提交即可恢复旧的 README 与生成脚本。已有旧版绘图模块没有删除；不需要恢复上方视频，因为本包没有动它。
