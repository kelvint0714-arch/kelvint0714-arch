# 全部黑白漫画版 · INK V2

适用仓库：kelvint0714-arch/kelvint0714-arch
不适用于独立的 kelvint0714-arch.github.io 网站。

## 上传

1. 解压本更新包，进入看到 README.md、assets、scripts 的那一层。
2. 打开个人资料仓库的根目录，使用 Add file → Upload files。
3. 同时拖入 assets、scripts 两个文件夹，以及 README.md、MAINTENANCE.md、MANGA-INK-V2.md 三个文件。不要直接上传 ZIP，不要拖入最外层解压文件夹，不要在 assets 目录内再上传整个 assets 文件夹。
4. 提交到 main。提交说明可写 “Apply full monochrome ink edition”。
5. 查看 Actions 中 Tend the garden 的结果。此包不修改工作流；新脚本继续使用仓库已有的采集模块与数据快照。

必须同时更新 README、assets 和 scripts：只上传图片不一定会改变页面引用；只上传图片和 README 而遗漏脚本，会使下一次自动生成使用旧逻辑。

## 范围

已统一：Project Garden、Bloom Log、每个仓库展示卡片、Bloom Calendar、Language Bouquet、Garden Notes、花枝、蝴蝶结、图标、进度条、日期标记、分镜边框和页脚。标题保留哥特字形，正文保留可读字体。

浅色和深色都保留白纸黑墨。无粉紫色、彩色渐变、柔光、立体阴影；不是只给旧图去色。所有新图片统一放在 assets/ink-v2/，避免页面继续引用旧目录中的彩色卡片。旧文件不需要删除。

不包含视频文件、头像文件、字体文件或数据快照。README 的 BANNER 块保持原样。用户的头像、视频、真实仓库名称、仓库描述和独立网站均不修改。

## 识别新版本

README 源码中应有 MANGA-EDITION: ink-v2。Language Bouquet 的花束应当是白底墨线、黑色缎带和排线进度条；Garden Notes 应当是带花枝的黑白对白框。每个 source/img 的非视频图片路径都应以 ./assets/ink-v2/ 开头。

如果仍显示旧图，先检查这三个层次是否都在正确目录上传成功，再刷新页面。不要反复覆盖 banner.webp 来排查下方卡片。

## 预览与数据

提供的预览是新源码本地渲染，不是线上发布截图。预览中的统计基于先前项目快照（2026-10-17T09:47:03Z）；本更新包不会覆盖 data/snapshot.json。原自动采集成功后，新图会显示当前数据。

26 项本地单元测试、32 张 SVG 结构/颜色检查、四版日历逐日核对及 12 组浏览器尺寸/主题组合检查通过。在线采集、GitHub 发布及手机实机效果仍应以实际执行为准。

## 回滚

使用 GitHub 对这次提交执行 Revert，或从这次提交之前恢复 README 和本包修改的 scripts 文件。旧的 assets/metrics、assets/sections、assets/repos 未删除，视频和数据不受影响。不要只恢复 README 而保留新脚本，否则下一次自动刷新会再次输出新目录卡片。
