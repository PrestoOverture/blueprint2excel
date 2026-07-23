# blueprint2excel

矢量PDF工程图纸解析器：输入CAD导出的矢量PDF，提取尺寸/公差/孔位/标题栏信息，输出Excel检查基准书 + 气泡图标注PDF。桌面应用（Electron + 本地FastAPI后端 + React前端）。

详细设计文档见 `docs/`（`prd.md`产品需求、`architecture.md`架构决策、`tech_stack.md`技术选型、`roadmap.md`实施步骤、`progress.md`当前进度和已知问题）。

## 环境要求

- [uv](https://docs.astral.sh/uv/)（Python包/项目管理器，会自动装好Python 3.11+，不需要单独装Python）
- Node.js v20+（含npm）

## 安装

```bash
git clone https://github.com/PrestoOverture/blueprint2excel.git
cd blueprint2excel

uv sync                          # 装Python依赖（解析引擎+后端）
npm install --prefix frontend    # 装前端依赖
npm install --prefix electron    # 装Electron依赖
```

## 运行（桌面应用）

```bash
npm run build --prefix frontend  # 构建前端（每次改了frontend/代码都要重新build）
npm start --prefix electron      # 启动桌面应用
```

会自动在本地启动后端服务（端口8000）并打开桌面窗口。关闭窗口会自动清理后端进程。

## 运行（开发模式，前后端分开跑，方便看日志/调试）

需要两个终端：

```bash
# 终端1：后端
uv run uvicorn backend.main:app

# 终端2：前端（默认 http://localhost:5173，已配置代理转发API请求到后端）
npm run dev --prefix frontend
```

## 测试

```bash
uv run pytest                    # Python测试（解析引擎+后端）
uv run mypy src backend --strict # 类型检查
uv run ruff check .              # 代码规范检查

npx tsc --noEmit --prefix frontend  # 前端类型检查
```

测试用的真实图纸样例在 `tests/fixtures/`，更多原始样例图纸在 `blueprints/`。

## 已知问题 / 待验证

见 `docs/progress.md`的"已知限制"部分。其中与本次分发相关、需要重点反馈的一条：

- **Electron的后端子进程清理逻辑在Windows上未经真实环境验证**。关闭桌面应用窗口后，请用任务管理器（或命令行 `tasklist | findstr python`）确认没有残留的`uvicorn`/`python`进程。如果有残留，请反馈。
