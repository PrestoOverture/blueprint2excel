# Roadmap

## 范围说明

Sprint 1-4（矢量PDF解析引擎，`drawing_inspector`库）已完成，经过深度人工验证（含泛化性测试，发现并修复了1个真实bug）。**Sprint 5（Web UI）已于2026-07-23启动**，用户明确批准。仍然没有独立CLI（见`architecture.md` ADR-005）。Sprint 5内部也要按Step 5.1→5.2→5.3顺序来，每层独立验证完再加下一层，不要一次性把后端+前端+Electron都搭起来再测试。

## 实施顺序（TDD，每步红→绿→重构）

### Sprint 1: 骨架 + 检测 + 基础提取（Day 1-2）

**Step 1.1** — 项目初始化
- uv init, 依赖安装, ruff/mypy配置
- 测试夹具: 将`blueprints/HJMZ01-01-01 板面.pdf`作为测试用例放入tests/fixtures/

**Step 1.2** — 矢量PDF检测 (`detector.py`)
- 输入: PDF路径
- 输出: `is_vector: bool`
- 实现: 用PyMuPDF的`page.get_fonts()`检查字体列表是否非空
- 测试: 矢量PDF返回True；人工创建的纯图片PDF返回False

**Step 1.3** — 文字对象提取 (`extractor.py`)
- 输入: PDF路径
- 输出: `list[TextObject]`（含内容、坐标、旋转角度、字体信息）
- 实现: pdfplumber提取words + PyMuPDF提取旋转矩阵，合并
- 测试: 对板面图提取结果应包含"920"、"M3 - 6H"、"技术要求"等关键文字

**Real Test**: 对`blueprints/`下全部8张图纸依次跑`is_vector`检测，全部应返回True（均为CAD导出的矢量PDF）。

### Sprint 2: 重组层——核心难点（Day 3-5）

**Step 2.1** — 旋转文字还原 (`reassembler.py`)
- 将旋转90°/270°的文字（如竖排的"448"）标记旋转方向
- 测试: "844"碎片应被还原为"448"旋转90°

**Step 2.2** — 公差叠排重组 (`reassembler.py`)
- 识别上下排列的偏差碎片，重组为完整公差标注
- 规则: 在同一水平位置±字号宽度内，垂直间距<2倍字号的数字碎片视为同一公差标注
- 上方为上偏差（正值或0），下方为下偏差（负值或0）
- 测试: 碎片["15", "+0", ".01", "8", "0"] → Dimension(nominal=15, upper=+0.018, lower=0)
- 测试: "60 ±0.05" → Dimension(nominal=60, upper=+0.05, lower=-0.05)

**Step 2.3** — 标注类型识别
- ⌀前缀 → diameter
- R前缀 → radius
- 角度符号° → angle
- 其余 → linear
- 测试: "⌀15" → type=diameter, nominal=15

**Real Test**: 人工核对板面图上5-8处已知公差标注（含碎片化案例）的重组结果，逐一对比原图确认数值和上下偏差正确。

### Sprint 3: 结构化解析（Day 6-8）

**Step 3.1** — 区域分类
- 用pdfplumber的`find_tables()`定位表格区域
- 剩余区域按坐标分: 左下=技术要求, 右下=标题栏, 中间=图面标注
- 测试: 孔位表的边界框应覆盖标签A-L所有行

**Step 3.2** — 孔位表解析 (`parser/hole_table.py`)
- 从表格区域提取结构化行
- 解析每行的标签、孔径/螺纹、深度、数量
- 处理多行描述（如"⌀12 ▽19.75 / 背面⌀30 ▽10"）
- 测试: 完整提取12行A-L，字段全部正确

**Step 3.3** — 标题栏解析 (`parser/title_block.py`)
- 提取图号、材料、名称、比例、日期
- 测试: 图号="HJMZ01-01-01", 材料="6061 合金"

**Step 3.4** — 技术要求提取 (`parser/tech_requirements.py`)
- 按行号前缀（"1."、"2."...）分割技术要求条目
- 提取未注公差标准（"GB-1804-M"）
- 测试: 5条技术要求完整提取

**Step 3.5** — 图面尺寸提取 (`parser/dimensions.py`)
- 从图面区域提取所有Dimension对象
- 区分: 轮廓尺寸 vs 定位尺寸 vs 精密公差尺寸
- 测试: 920, 440, 880, 448, 60±0.05, 160±0.05, 对角2X⌀15+0.018/0 等全部提取

**Real Test**: 跑`blueprints/`下另外2-3张不同零件图纸（非板面图），人工核对孔位表和标题栏提取结果与原图一致，确认区域分类逻辑不是只对板面图过拟合。

### Sprint 4: 公差计算 + 输出（Day 9-11）

**Step 4.1** — GB/T 1804公差查表 (`tolerance/gb1804.py`)
- 硬编码GB/T 1804-m/f/c/v的公差表
- 输入: 标称值 + 公差等级 → 输出: 上偏差, 下偏差
- 测试: 标称值920, 等级m → ±0.8; 标称值20, 等级m → ±0.2（**2026-07-23更正**：原写的±0.4/±0.1经核实是错的，已用多个独立信源交叉核对ISO2768-1/GB-T1804数值表更正，见`progress.md`）

**Step 4.2** — Excel检查基准书 (`output/excel_report.py`)
- Sheet 1: 图纸基本信息
- Sheet 2: 检查基准书（序号、气泡号、检查项目、标称值、公差、测量工具、空白结果列）
- Sheet 3: 孔位汇总
- Sheet 4: 公差明细
- 测试: 打开生成的Excel，验证数据完整性

**Step 4.3** — 气泡图PDF (`output/bubble_diagram.py`)
- 在原PDF上用PyMuPDF叠加红色圆圈编号
- 编号与Excel检查基准书的序号对应
- 拥挤区域的气泡偏移+引线
- 测试: 输出PDF中气泡数量 = 检测项数量

**Real Test**: 对板面图跑全流程生成Excel+气泡图PDF，人工打开两个文件，核对气泡编号位置与原图标注偏差<2mm（按比例尺换算），Excel字段无缺失。

### Sprint 5: Web UI（Electron壳 + FastAPI后端）—— 已启动（2026-07-23，用户批准）

启动条件已满足：解析引擎在`blueprints/`全部8张图纸上跑通，做过深度人工核对（不只是冒烟测试），发现并修复了一个真实的公差堆叠误判bug（见`progress.md`）。技术选型见`tech_stack.md`：FastAPI+uvicorn后端、React+TypeScript+Vite前端、Electron桌面壳。

**Step 5.1** — FastAPI后端 (`backend/main.py`, `backend/routes/inspect.py`)
- `POST /inspect`：接收PDF上传，调用`pipeline.assemble_drawing_data()`，同时生成Excel和气泡图PDF到临时目录，返回结构化JSON（DrawingData的字段）+ 两个文件的下载token/链接
- 非矢量PDF输入：返回明确的错误响应（对应`NotVectorPDFError`），不是500
- 测试：用httpx/curl直接测试API，不需要前端
- **先只做这一步**，不做前端，不做Electron

**Step 5.2** — React前端骨架 (`frontend/`)
- 拖拽/选择PDF上传区、调用Step 5.1的API、结果预览（标题栏信息、尺寸列表、孔位表、技术要求）、下载按钮（Excel/气泡图PDF）、错误提示（非矢量PDF）
- 用`npm run dev`本地跑，浏览器里手动测试，后端用`uvicorn`本地跑，先不套Electron壳
- 测试：至少手动走一遍完整流程（上传板面图→看到解析结果→下载Excel和气泡图PDF能打开且内容对）

**Step 5.3** — Electron桌面壳 (`electron/`)
- 主进程启动/管理FastAPI子进程（随机端口、生命周期跟主进程绑定，主进程退出时子进程也退出）
- 渲染进程加载Step 5.2的前端（开发模式指向Vite dev server，生产模式待打包分发阶段再定）
- 测试：双击/命令行启动Electron应用，走一遍完整流程

**Real Test（Sprint 5）**：在Electron应用里，对板面图跑一遍完整流程——上传→预览结果→下载Excel和气泡图PDF，人工确认整个体验顺畅、没有明显bug。这是主观判断，需要用户亲自试用确认。

## 测试数据

`blueprints/`目录下已有8张真实CAD导出的矢量PDF：

| 文件 | 用途 |
|---|---|
| HJMZ01-01-01 板面.pdf | 主测试用例（Sprint 1-2核心开发） |
| HJMZ01-03-02/03/04 气缸座板1/2/3.pdf | 同类零件变体，验证泛化性 |
| HJMZ01-04-01 手控器治具.pdf | 不同零件类型 |
| HJMZ01-04-02 探针座.pdf | 不同零件类型 |
| HJMZ05-03-01 面罩外形治具.pdf | 不同零件类型 |
| 滑块推板1.pdf | 不同零件类型 |

**待确认**: 这8张是否都是SolidWorks导出（需在Sprint 1检测层验证时顺带确认，因为不同CAD软件的文字碎片化方式可能不同，见下方风险）。

## 风险 & 缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| 不同CAD软件导出的PDF文字碎片化方式不同 | 重组层规则失效 | 先只适配SolidWorks，拿到其他格式样本后迭代 |
| 密集标注区域气泡重叠 | 气泡图不可读 | 实现碰撞检测+偏移算法，拥挤时画引线 |
| pdfplumber和PyMuPDF坐标系差异 | 气泡位置偏移 | 统一转换为PyMuPDF坐标系（原点左下角） |
| 非标图框布局 | 区域分类错误 | 先用find_tables()定位表格，再推断其他区域 |
