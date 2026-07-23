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
- [ ] Sprint 3: 结构化解析
- [ ] Sprint 4: 公差计算 + 输出
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
