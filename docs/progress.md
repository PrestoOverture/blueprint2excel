# Progress

## 当前状态: 规划完成，待实施

## 已完成

- [x] 可行性验证：用pdfplumber对HJMZ01-01-01_板面.pdf做了完整文字提取，确认矢量路线可行
- [x] OCR路线对比测试：Tesseract对同一图纸扫描件测试，确认通用OCR不可用（12项中3项丢失/乱码）
- [x] Excel输出原型：生成了包含32项检测项的检查基准书（4个sheet），验证了输出格式
- [x] 技术选型确认：pdfplumber + PyMuPDF + openpyxl
- [x] 项目文档：prd.md, tech_stacks.md, architecture.md, project_plan.md

## 待开始

- [ ] Sprint 1: 骨架 + 检测 + 基础提取
- [ ] Sprint 2: 重组层
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
