# Architecture

## 系统总览

```
Electron桌面应用
  │
  ├─ Main进程 ──→ 启动/管理本地FastAPI子进程（localhost，随机端口）
  │
  ├─ Renderer(前端页面) ──→ 拖拽上传PDF / 结果预览 / 导出触发
  │                          通过HTTP调用FastAPI后端
  │
  └─ FastAPI后端 ──→ 复用下方解析引擎（drawing_inspector库）
        │
        ├─ 1. 检测层 ──→ pdffonts检查 → 有字体=矢量，无字体=拒绝
        │
        ├─ 2. 提取层 ──→ 文字对象提取（内容+坐标+旋转角度）
        │
        ├─ 3. 重组层 ──→ 空间聚类，碎片文字→完整标注
        │                 旋转文字还原
        │                 公差叠排重组（上偏差/下偏差识别）
        │
        ├─ 4. 结构化层 → 区域分类（图面标注 / 孔位表 / 技术要求 / 标题栏）
        │                 孔位表解析为结构化数据
        │                 公差查表（GB/T 1804）
        │
        ├─ 5. 输出层
        │     ├─ Excel检查基准书
        │     └─ 气泡图PDF（原图+叠加标注）
        │
        输出: .xlsx + .pdf（供前端下载/预览）
```

## 模块划分

当前阶段只实现`drawing_inspector/`本体（矢量PDF解析引擎）。下方的`backend/`、`frontend/`、`electron/`是最终交付形态的目标结构，**在解析引擎跑通、结果在`blueprints/`全部测试图纸上验证准确之前不动工**。

```
drawing_inspector/          # 当前阶段的全部工作范围
├── detector.py             # 矢量PDF检测
├── extractor.py            # 文字对象提取（pdfplumber + PyMuPDF）
├── reassembler.py          # 空间聚类 + 公差重组（核心难点）
├── parser/
│   ├── regions.py          # 区域分类（锚点文本定位，非find_tables()的bbox——见ADR-006）
│   ├── hole_table.py       # 孔位表解析
│   ├── title_block.py      # 标题栏解析
│   ├── tech_requirements.py# 技术要求提取
│   └── dimensions.py       # 尺寸/公差标注解析
├── tolerance/
│   ├── gb1804.py           # GB/T 1804 未注公差查表
│   ├── iso286.py           # ISO 286 孔轴公差查表
│   └── thread.py           # 螺纹底孔标准表
├── output/
│   ├── excel_report.py     # Excel检查基准书生成
│   └── bubble_diagram.py   # 气泡图PDF渲染
├── models.py               # 数据模型（dataclass）
├── constants.py            # 公差表常量、螺纹标准
└── pipeline.py             # 整合入口：assemble_drawing_data(pdf_path) -> DrawingData
```

`pipeline.py`不在最初的模块划分里，是Sprint 4实施中新增的整合点：串联检测→提取→重组→区域分类→各parser→GB/T1804查表补全，供后续Excel/气泡图导出、以及未来Web UI后端复用。

**目标形态（暂不实施）**：解析引擎完成后，会新增`backend/`（FastAPI，暴露`POST /inspect`等接口，供Electron子进程启动）、`frontend/`（Electron渲染进程页面，上传/预览/导出交互）、`electron/`（主进程，管理FastAPI子进程生命周期）。技术选型待Web UI阶段启动时再定（见`tech_stack.md`）。

## 核心数据模型

```python
@dataclass
class TextObject:
    """PDF中的一个文字对象"""
    text: str
    x: float           # PDF坐标系x
    y: float           # PDF坐标系y
    width: float
    height: float
    rotation: float     # 旋转角度（度）
    font_name: str
    font_size: float

@dataclass
class Dimension:
    """一个完整的尺寸标注"""
    nominal: float              # 标称值
    upper_deviation: float | None  # 上偏差
    lower_deviation: float | None  # 下偏差
    tolerance_grade: str | None    # 公差等级（如H7）
    dimension_type: str            # "linear" | "diameter" | "radius" | "angle"
    x: float                       # 标注在图面的位置
    y: float
    bubble_id: int | None          # 气泡编号（输出时赋值）

@dataclass
class PageRegions:
    """区域分类结果，各区域为PDF坐标系bbox (x0, top, x1, bottom)"""
    table_bbox: tuple[float, float, float, float] | None
    title_block_bbox: tuple[float, float, float, float] | None
    tech_requirements_bbox: tuple[float, float, float, float] | None
    drawing_bbox: tuple[float, float, float, float]  # 矩形，可能与table_bbox重叠——见ADR-006

@dataclass
class TitleBlock:
    """标题栏结构化字段"""
    drawing_number: str
    part_name: str
    material: str
    scale: str
    date: str

@dataclass
class TechRequirements:
    """技术要求条目 + 未注公差标准"""
    items: list[str]
    tolerance_standard: str | None

@dataclass
class HoleFeature:
    """孔位表中的一行"""
    label: str              # A, B, C...
    hole_type: str          # "through" | "blind" | "threaded" | "counterbore"
    primary_diameter: float | str   # 孔径或螺纹规格
    depth: float | str             # 深度或"贯穿"
    counterbore_diameter: float | None
    counterbore_depth: float | None
    thread_spec: str | None        # M3-6H等
    pilot_hole: float | None       # 底孔直径
    quantity: int
    back_side: bool                # 是否背面加工

@dataclass
class DrawingData:
    """整张图纸的完整结构化数据"""
    drawing_number: str
    part_name: str
    material: str
    scale: str
    date: str
    tech_requirements: list[str]
    dimensions: list[Dimension]
    hole_features: list[HoleFeature]
    tolerance_standard: str         # "GB-1804-M" 等
```

**已实现（Sprint 4b）**：`pipeline.assemble_drawing_data(pdf_path)`产出`DrawingData`。对没有显式公差的`Dimension`，用`tolerance_standard`解析出的等级（如"GB-1804-M"→等级"m"）查`tolerance/gb1804.py`补全`upper_deviation`/`lower_deviation`，并把该`Dimension.tolerance_grade`设为解析出的标准字符串（如"GB-1804-M"），作为"公差来源"标记——`tolerance_grade`非空且有偏差值 = GB1804查表补全（**当前多数格未经核实，见Step 4.1风险**），`tolerance_grade`为空但有偏差值 = 图纸原始标注。非矢量PDF输入会抛出`NotVectorPDFError`。

## ADR

### ADR-001: 双库提取策略

**决策**: 用pdfplumber做主提取，PyMuPDF做补充（旋转矩阵+PDF写入）。

**原因**: pdfplumber的`extract_words()`API更直观，直接给出聚类后的词和坐标。但pdfplumber不支持读取文字对象的旋转变换矩阵（rotation matrix），也不支持PDF写入。PyMuPDF的`page.get_text("dict")`能拿到完整的变换矩阵，且支持在PDF上叠加标注（气泡图需要）。

**代价**: 两个库对同一个PDF的坐标系可能有细微差异（pdfplumber的y轴原点在页面顶部，PyMuPDF在底部），需要做坐标转换。

### ADR-002: 空间聚类策略

**决策**: 用简单的距离阈值聚类，不用DBSCAN等复杂算法。

**原因**: 工程图纸的标注文字排布有明确规律——公差上下偏差的垂直间距通常在2-5个字号高度内，同一标注的水平间距在1-2个字号宽度内。基于字号的动态阈值足够，不需要引入sklearn依赖。

**风险**: 密集标注区域可能误聚类。缓解方案：聚类结果过公差格式正则校验，不合法的拆开重试。

### ADR-003: 区域分类策略

**决策**: 用PDF坐标的固定比例划分区域（图面区、表格区、标题栏区、技术要求区），不用布局分析模型。

**原因**: 工程图纸的布局高度标准化——标题栏在右下角、技术要求在左下角、孔位表在右侧。用PDF页面尺寸的百分比做粗分区，再在分区内做细解析，足够可靠。SolidWorks导出的图纸布局尤其规整。

**风险**: 非标布局（如表格在左侧）会分区错误。缓解方案：先找表格线（pdfplumber的`find_tables()`），用表格实际位置覆盖默认分区。

**实施更新（Sprint 3a，2026-07-23）**: 固定比例分区在真实图纸上不可靠（`find_tables()`在此图纸上返回的表格bbox基本是整个页面——外框线被误判为表格网格线，`(8.5, 6.58, 835.67, 589.08)` vs 页面`841.89×595.276`）。最终采用**锚点文本定位**替代固定比例/`find_tables()` bbox：定位"图号"/"材料"/"名称"（标题栏）、"技术要求"+编号条目（技术要求区）、"标签"/"大小"/"数量"表头（孔位表）的真实文字位置，再从锚点推导各区域bbox。`drawing_bbox`是矩形，因此在孔位表所在的右侧区域会与`table_bbox`发生几何重叠（孔位表不是从页面顶部延伸的矩形区域）——下游消费者（尺寸提取等）必须显式排除`table_bbox`内的文字对象，不能只依赖`drawing_bbox`本身。见`models.py`的`PageRegions`。

### ADR-004: 气泡图渲染方案

**决策**: 用PyMuPDF在原PDF上叠加标注，输出新PDF。

**原因**: 保留原图的矢量清晰度。替代方案是渲染成图片再画标注，但会损失矢量精度且文件变大。PyMuPDF的`page.insert_text()`和`page.draw_circle()`可以在指定坐标处画气泡编号。

**实现细节**: 气泡编号放在对应标注旁边，用红色圆圈+白底+编号数字。如果位置拥挤，气泡偏移到最近的空白区域并画引线连接。

### ADR-005: 交付形态——Electron壳 + 本地FastAPI子进程（暂缓实施）

**决策**: 最终用户交付物是Electron桌面应用，不做独立CLI。Electron主进程启动本地FastAPI子进程（localhost随机端口），渲染进程页面通过HTTP调用该后端；后端直接复用`drawing_inspector`解析引擎库。

**原因**: 用户是制造业质检工程师，命令行不是合适的交互方式；Electron能打包成桌面安装包，FastAPI子进程模式让前后端解耦，方便先做Web版再套壳。

**代价**: 打包体积和分发链路比纯CLI复杂（需要打包Python运行时或用PyInstaller），且需要多维护一套前端代码。

**状态**: 未启动。当前阶段的全部工作是`drawing_inspector`解析引擎（对应`roadmap.md` Sprint 1-4），Web UI相关的具体技术选型、目录结构和实现在解析引擎验证通过`blueprints/`下全部测试图纸之前不展开。
