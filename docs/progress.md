# Progress

## 当前状态: 规划完成，待实施

## 已完成

- [x] 可行性验证：用pdfplumber对HJMZ01-01-01_板面.pdf做了完整文字提取，确认矢量路线可行
- [x] OCR路线对比测试：Tesseract对同一图纸扫描件测试，确认通用OCR不可用（12项中3项丢失/乱码）
- [x] Excel输出原型：生成了包含32项检测项的检查基准书（4个sheet），验证了输出格式
- [x] 技术选型确认：pdfplumber + PyMuPDF + openpyxl
- [x] 项目文档：prd.md, tech_stacks.md, architecture.md, project_plan.md

## 待开始

- [x] Sprint 1: 骨架 + 检测 + 基础提取 —— Codex实现，Claude review通过（2026-07-23）：`uv sync`/`pytest`/`mypy --strict`/`ruff`全绿；Real Test通过（`blueprints/`全部8张图纸`is_vector_pdf`均返回True，均为SolidWorks导出）；旋转文字提取验证正确（如"448"的90°旋转片段被正确标记，重组留给Sprint 2）
- [x] Sprint 2: 重组层 —— Codex实现，Claude review通过（2026-07-23）：`pytest`/`mypy --strict`/`ruff`全绿。旋转文字还原规则（升序y拼接后整体反转字符串）用真实图纸7个案例验证；⌀/Φ/Ø均未在真实PDF中以文字形式出现（图形绘制），Sprint 3孔位表/尺寸解析需注意；对角旋转标注（50.7°/60°/315°/320.2°，共46个碎片）明确排除在外，留待后续
  - **发现的风险（需在Sprint 3处理）**：`reassemble_dimensions`未做区域过滤时，会把孔位表内不相关的相邻单元格误聚类成虚假公差标注——实测复现：表格区"12"(B行沉孔深度)+"9"(A行数量，上方)+"0"(B行螺纹深度，下方)被误组装成`Dimension(nominal=12, upper=9, lower=0)`。这正是`architecture.md` ADR-003预判的失效模式，Sprint 3 Step 3.1区域分类必须先于Step 3.5尺寸提取执行，且孔位表区域要从尺寸提取的输入中排除
- [x] Sprint 3: 结构化解析 —— 全部完成（2026-07-23）
  - [x] Step 3.1/3.3/3.4（区域分类+标题栏+技术要求）—— Codex实现，Claude review通过：`pytest`/`mypy --strict`/`ruff`全绿，标题栏/技术要求提取值与真实图纸逐字匹配。采用锚点文本定位（非固定比例、非`find_tables()` bbox，后者在此图纸上不可用，详见`architecture.md` ADR-003更新）。已知限制：`drawing_bbox`是矩形会与`table_bbox`几何重叠，Step 3.5尺寸提取必须显式排除`table_bbox`内文字
  - [x] Step 3.2 孔位表解析 —— Codex实现，Claude review通过：`pytest`/`mypy --strict`/`ruff`全绿，11行A-L（跳过I）与真实图纸逐字段核对全部匹配。已知信息丢失：B行螺纹线自身的深度"0"因`HoleFeature`无对应字段被丢弃，接受此限制不新增字段。`HoleFeature` dataclass已从`architecture.md`落地到`models.py`
  - [x] Step 3.5 图面尺寸提取 —— Codex实现，Claude review通过：`pytest`/`mypy --strict`/`ruff`全绿。真实图纸提取出18个Dimension：9个未旋转（含2组60±0.05）+ 9个旋转90°（448×2/410/205/20/190×2/160×2）。对角旋转标注（对角2X⌀15+0.018/0）正确排除，未泄漏为虚假标注。表格区域回归测试通过——不再产生虚假的`Dimension(12,+9,0)`
    - **已知限制（后续可补）**：旋转90°的公差叠加尚未打通——两个"160"实例都没能匹配上各自的"±0.05"搭档（附近的合并簇几何范围超出了现有的水平/垂直阈值，这些阈值是为单行未旋转文字设计的），目前落地为无公差的裸标注`Dimension(nominal=160, upper=None, lower=None)`。修复需要专门针对"合并后的旋转簇"重新设计间距阈值，不在当前范围内，留作后续小任务
    - `reassemble_dimensions`已扩展支持0°/90°/270°三种旋转角度的标称值识别（此前只接受0°），旋转匹配要求公差碎片与标称值同角度，不允许跨角度匹配
- [~] Sprint 4: 公差计算 + 输出 —— 进行中
  - [x] Step 4.1 GB/T1804公差查表 —— Codex实现，Claude review通过（2026-07-23）：`pytest`/`mypy --strict`/`ruff`全绿。**重要风险，非小事**：整张公差表（8个尺寸区间×4个等级=32格）里只有roadmap.md给出的2个值经过确认（6-30mm/m级=0.1，400-1000mm/m级=0.4）——这两个值本身还和我记忆中的ISO2768-1标准对不上（我记得的是0.2和0.8），已问过用户，用户决定先按roadmap.md的值实现并标记待核实。其余30格全部是未经核实的占位数值，`constants.py`和`gb1804.py`里都有醒目警告。**在这个查表结果被用于任何真实检验决策之前，必须找到GB/T 1804官方标准文本逐格核对**
  - [x] Step 4.1b pipeline.py整合（新增，不在原模块划分里）—— Codex实现，Claude review通过（2026-07-23）：`pytest`/`mypy --strict`/`ruff`全绿。`assemble_drawing_data()`串联全部已实现模块产出`DrawingData`；真实图纸装配出18个尺寸+11个孔位，GB1804补全逻辑正确（60±0.05等2个显式公差保持`tolerance_grade=None`不被覆盖，16个裸尺寸如920被填入`tolerance_grade="GB-1804-M"`）；`NotVectorPDFError`正确抛出。已记录进`architecture.md`
  - [x] Step 4.2 Excel检查基准书导出 —— Codex实现，Claude review通过（2026-07-23）：`pytest`/`mypy --strict`/`ruff`全绿。4个sheet核对：图纸基本信息、检查基准书（18行，气泡号1-18无重复）、孔位汇总（11行）、公差明细（18行）。"公差来源"列正确区分"图纸标注"vs"GB-1804-M查表（未核实）"，把Step4.1的公差表风险直接暴露在交付物里而非掩盖。`bubble_id`原地写入`Dimension`对象，供Step 4.3气泡图复用同一编号
  - [ ] Step 4.3 气泡图PDF
- [ ] Sprint 5+: Web UI（Electron壳 + FastAPI后端）—— 未启动，见`roadmap.md`

## 范围决定（2026-07-23）

- 最终交付物是Web UI（Electron桌面壳 + 本地FastAPI子进程），不做独立CLI（见`architecture.md` ADR-005）
- 当前阶段严格只做矢量PDF解析引擎（Sprint 1-4），Web UI等其它功能暂不启动
- `docs/project_plan.md`、`docs/tech_stacks.md`已重命名为`roadmap.md`、`tech_stack.md`，对齐`CLAUDE.md`引用的文件名

## 已知问题

1. **坐标系差异**: pdfplumber y轴原点在顶部，PyMuPDF在底部，需要在extractor.py中统一
2. **旋转文字**: 板面图中"448"等竖排标注在pdfplumber中读出为"844"（字符反序），需要结合旋转矩阵还原
3. **公差碎片化**: "+0.018"在PDF中被拆成"+0"、".01"、"8"三个独立文字对象，重组逻辑是核心难点

## 测试图纸

`blueprints/`目录下已有8张真实图纸（原先只有板面图1张，现已补充7张）：

| 文件 | 状态 | 用途 |
|---|---|---|
| HJMZ01-01-01 板面.pdf | ✅ 已有 | 主测试用例 |
| HJMZ01-03-02/03/04 气缸座板1/2/3.pdf | ✅ 已有 | 同类零件变体，泛化性验证 |
| HJMZ01-04-01 手控器治具.pdf | ✅ 已有 | 不同零件类型 |
| HJMZ01-04-02 探针座.pdf | ✅ 已有 | 不同零件类型 |
| HJMZ05-03-01 面罩外形治具.pdf | ✅ 已有 | 不同零件类型 |
| 滑块推板1.pdf | ✅ 已有 | 不同零件类型 |

CAD来源待Sprint 1检测层验证时确认（见`roadmap.md`）。
