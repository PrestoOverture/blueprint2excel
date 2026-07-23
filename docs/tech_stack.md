# Tech Stacks

## 当前阶段范围

`drawing_inspector`解析引擎（Sprint 1-4）已完成并深度验证。**Sprint 5+已启动（2026-07-23，用户明确批准）**：Web UI（Electron壳 + FastAPI后端 + React前端）。

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

## Web UI技术栈（Sprint 5+，2026-07-23起）

| 层 | 技术 | 为什么选它 |
|---|---|---|
| 后端API | FastAPI + uvicorn | 直接复用`drawing_inspector`库；async支持好；自带OpenAPI文档方便前端对接；生态成熟 |
| 前端 | React + TypeScript + Vite | Electron生态里最常见的组合，生态/文档/排错资源最多；Vite开发体验快；TypeScript配合FastAPI的OpenAPI schema能生成类型安全的API client |
| 桌面壳 | Electron | 主进程管理FastAPI子进程生命周期，渲染进程加载前端页面（见`architecture.md` ADR-005） |
| 打包分发 | electron-builder（暂不需要，等功能验证完再做） | P2范畴，见`prd.md` |

**实施顺序**：先把FastAPI后端在本地跑通（无UI，用curl/httpx测试），再做React前端在浏览器里跑通并对接后端（无Electron），最后才套Electron壳把两者串起来——每一层先独立验证，不要一次性把三层都搭起来再测试。这个顺序是`architecture.md` ADR-005本来就定好的（"方便先做Web版再套壳"）。

## 开发工具

- Python测试：pytest
- Python类型检查：mypy（严格模式）
- Python格式化：ruff
- Python包管理：uv
- 前端：npm（Node.js v24已装好）
- 前端类型检查：TypeScript编译器（`tsc --noEmit`）

## 运行环境

纯CPU，无GPU需求。可在普通办公电脑运行。
