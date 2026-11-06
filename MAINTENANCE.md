# 维护说明 · Ink & Petals

这个仓库就是 GitHub 个人资料页 `kelvint0714-arch/kelvint0714-arch`（不是 `kelvint0714-arch.github.io` 网站）。README 里除了顶部视频横幅，每一张图都是 `scripts/` 生成的 SVG。**改图请改脚本，不要手改 SVG**：自动刷新每 15 分钟会把 `assets/` 重画一遍。

## 目录

```
README.md            个人资料页；GARDEN-REPOS 区域由脚本改写，其余手写
garden.json          用户名、时区、两个章节的标题文字
assets/
  banner*.webp       视频横幅（build_banner.py 生成，不参与自动刷新）
  sections/          章节标题与页脚           ← build_sections.py
  metrics/           花暦、言語の花束、花便り   ← build_metrics.py
  repos/             每个公开仓库一张卡片       ← update_repositories.py
data/snapshot.json   最近一次公开数据；网络失败时的回退
banners/             横幅的原视频（不提交）和 config.json
fonts/               Great Vibes（OFL），只给 build_lettering.py 用
scripts/
  build_*.py, update_repositories.py   入口脚本
  garden/data.py         从 GitHub 读取公开数据
  garden/manga.py        共用绘图：颜色、线宽、网点、花、卡片、标题
  garden/calendar3d.py   立体花床日历
  garden/vignettes.py    仓库卡片上的八幅小场景
  garden/manga_lettering.json   排好的花体标题轮廓（build_lettering.py 生成）
  test_*.py              测试
```

## 常用命令

```bash
make test      # 运行全部测试
make offline   # 用 data/snapshot.json 重画全部图，不联网
make build     # 联网取最新数据后重画
make format    # 用 black 统一 Python 格式（需先 pip install black）
```

日常绘图只用 Python 标准库。`make lettering` 需要 `fonttools`，`make banner` 需要 ffmpeg 和 Pillow。

## 视觉规则

彩色漫画分镜：紫黑墨线 `#2a2330` 加平涂（赛璐璐式）颜色，配色取自头像——樱花粉、头发高光的淡紫、眼睛的蓝、肤色的桃色、叶子的绿。没有渐变、模糊、滤镜、外部字体、脚本或图片；层次靠墨线、排线和网点。浅色和深色主题用同一张暖白纸面。

- **颜色**：全部集中在 `manga.py` 的 `COLOURS`。`petals` 是四组花色（填色、网点、深色），`levels` 是日历 1–4 级的花色，`bars` 是语言条的颜色；网点和排线的默认颜色在 `TONE_INK` / `TONE_WASH`。
- **线宽**：按 GitHub 上实际显示的大小来定（README 正文桌面约 830 px 宽，手机约 358 px）。`NIB` 规定三级线宽：轮廓 1.6、内线 1.1、细节 0.85，每个笔画用 `nib(k, 层级)` 换算，`k` 是该图在屏幕上的累计缩放。几十像素的小图用 `taper()` 把线宽降到最低 60%。不要写死 `stroke-width`。
- **网点**：`tone()` 按同一缩放生成，屏幕上的间距固定，调整改 `TONES` 和 `HATCH`。
- **标题**：大标题是 Great Vibes 花体的固定轮廓路径（`manga_lettering.json`），不嵌字体。新增或修改标题文字后运行 `make lettering`；没有轮廓的标题会退回普通衬线字，不会缺字。仓库名、说明、日期、语言和百分比都是普通文字。
- **尺寸**：每张图有浅/深 × 桌面/手机四个版本（`manga.variants()`），README 的 `<picture>` 以 600 px 为断点。

## 各张卡片

- **章节标题**：文字来自 `garden.json`。
- **仓库卡片**：每个公开仓库一张，带链接，下面还有可展开的文字索引。`repo_card()` 里的 `aliases` 给仓库起花体展示名（个人网站为 `A Quiet Valley`），没有别名的显示 `Repository`；真实仓库名始终完整显示。删除的仓库会自动清掉对应 SVG。
- **小场景**：`vignettes.assign()` 按仓库名、描述和语言里的关键词（`TOPICS`）挑场景，同分时按名字哈希稳定排序，八幅用完前不重复。新增场景在 `SCENES` 注册一个函数，坐标范围 290 × 215，右下角留给 OPEN 按钮。

  | 场景 | 内容 | 适合 |
  |---|---|---|
  | `valley` | 塔、阶梯和山谷 | 个人主页、网站、前端 |
  | `notebook` | 长出叶子的损失曲线 | 机器学习、数据、Python / Jupyter |
  | `clockwork` | 怀表齿轮里的玫瑰 | C / C++ / Rust / Go、系统 |
  | `teacup` | 热气化成樱花的茶杯 | 笔记、文档、博客 |
  | `fan` | 画着樱枝的折扇 | 应用、界面、游戏 |
  | `crane` | 浪上的纸鹤 | 算法、竞赛、题解、课程 |
  | `terminal` | 长出藤蔓的终端 | 命令行工具、脚本、dotfiles |
  | `seedling` | 浇水中的幼苗 | 其他（兜底） |

- **花暦（日历）**：一个日期一个花台，计数和等级与 GitHub 完全一致，等级只决定花台高度和花的大小。手机分成上下两个半年花床。
- **言語の花束**：按公开、非 fork 仓库的代码字节计算；超过六种时把尾部合并为 Other，分母仍是全部字节。
- **花便り**：最近 30 天内最多五条公开动态，同一天推到同一分支的合并成一条。

## 自动刷新

[Tend the garden](.github/workflows/garden.yml) 每 15 分钟运行一次，修改 `garden.json`、`scripts/` 或工作流后也会立即运行，也可以在 Actions 页面手动运行（可勾选 dry-run：只测试和绘制，不提交）。

每次都从最新的 `main` 开始：跑测试 → 重画全部图 → 只有公开数据真的变化时才提交 "Refresh the garden"（只换了获取时间的快照不算变化）。如果绘制期间 `main` 有新提交，它会丢弃自己的结果，在新的 `main` 上重画，最多重试三次。

所以修改绘图时，把 `scripts/` 和重新生成的 `assets/` 一起提交（先 `make offline`），否则在自动刷新之前页面会短暂显示旧图。

## 数据

脚本只改变呈现方式，不改动仓库描述、星标、语言、贡献计数或动态。`GITHUB_TOKEN` 只用来提高 API 限额；日历从公开主页读取，不需要登录。
