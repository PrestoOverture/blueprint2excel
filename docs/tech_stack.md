# Tech Stacks

## 当前阶段范围

只做`drawing_inspector`解析引擎（纯Python库）。没有CLI，没有UI。引擎通过pytest直接测试，用`blueprints/`下的真实图纸做测试夹具。

## 语言

Python 3.11+

## 核心依赖

| 库 | 用途 | 为什么选它 |
|---|---|---|
| `pdfplumber` | PDF文字对象提取（含坐标、字体信息） | 比pypdf坐标信息更完整，比PyMuPDF API更友好 |
| `PyMuPDF (fitz)` | 气泡图渲染（在PDF上叠加标注） + 文字对象旋转矩阵读取 | pdfplumber不支持PDF写入，PyMuPDF支持；旋转矩阵信息PyMuPDF更完整 |
| `openpyxl` | Excel检查基准书生成 | 标准选择，支持样式、合并单元格、公式 |

## 不用的东西（当前阶段）

| 不用 | 原因 |
|---|---|
| Tesseract / PaddleOCR | 矢量PDF不需要OCR，文字层直读 |
| YOLO / 任何检测模型 | 不做图像识别，不需要GPU |
| 任何LLM/VLM API | 确定性解析，不需要概率推理 |
| `click` / 任何CLI框架 | 最终产品是Web UI + Electron桌面应用，不做独立CLI交付物 |
| Flask/FastAPI/前端框架/Electron | 当前阶段只做解析引擎；Web UI是既定的最终交付形态（见`architecture.md` ADR-005），但技术选型和实现留到解析引擎在`blueprints/`全部测试图纸上验证通过之后再定，避免在核心逻辑没做扎实前铺开范围 |

## 开发工具

- 测试：pytest
- 类型检查：mypy（严格模式）
- 格式化：ruff
- 包管理：uv

## 运行环境

纯CPU，无GPU需求。可在普通办公电脑运行。
