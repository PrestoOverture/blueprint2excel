import { type ChangeEvent, type DragEvent, useMemo, useState } from 'react'
import type { ApiError, Dimension, InspectionResult } from './types'

const titleFields: Array<[keyof InspectionResult, string]> = [
  ['drawing_number', '图号'],
  ['part_name', '零件名称'],
  ['material', '材料'],
  ['scale', '比例'],
  ['date', '日期'],
  ['tolerance_standard', '公差标准'],
]

function toleranceSource(dimension: Dimension): string {
  if (dimension.tolerance_grade) return dimension.tolerance_grade
  if (
    dimension.upper_deviation !== null ||
    dimension.lower_deviation !== null
  ) {
    return '图纸标注'
  }
  return '无'
}

function display(value: number | string | null): string {
  return value === null ? '' : String(value)
}

function App() {
  const [result, setResult] = useState<InspectionResult | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [dragging, setDragging] = useState(false)

  const sortedDimensions = useMemo(
    () =>
      [...(result?.dimensions ?? [])].sort(
        (a, b) => (a.bubble_id ?? Number.MAX_SAFE_INTEGER) - (b.bubble_id ?? Number.MAX_SAFE_INTEGER),
      ),
    [result],
  )

  async function inspect(file: File) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('请选择 PDF 文件。')
      setResult(null)
      return
    }

    setLoading(true)
    setError('')
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('/inspect', {
        method: 'POST',
        body: formData,
      })

      if (response.status === 422) {
        const body = (await response.json()) as ApiError
        setError(body.detail || '该文件无法作为矢量 PDF 处理。')
        return
      }

      if (!response.ok) {
        setError(`检查失败（HTTP ${response.status}），请稍后重试。`)
        return
      }

      setResult((await response.json()) as InspectionResult)
    } catch {
      setError('无法连接到检查服务，请确认后端已启动后重试。')
    } finally {
      setLoading(false)
    }
  }

  function onFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (file) void inspect(file)
    event.target.value = ''
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setDragging(false)
    const file = event.dataTransfer.files[0]
    if (file) void inspect(file)
  }

  return (
    <main>
      <h1>图纸检查</h1>
      <section className="upload-section" aria-labelledby="upload-title">
        <h2 id="upload-title">上传 PDF 图纸</h2>
        <label className="file-button">
          选择 PDF 文件
          <input type="file" accept=".pdf,application/pdf" onChange={onFileChange} />
        </label>
        <div
          className={`drop-zone${dragging ? ' dragging' : ''}`}
          onDragEnter={(event) => {
            event.preventDefault()
            setDragging(true)
          }}
          onDragOver={(event) => event.preventDefault()}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
        >
          或将 PDF 文件拖放到这里
        </div>
      </section>

      {loading && (
        <div className="status loading" role="status">
          <span className="spinner" aria-hidden="true" />
          正在检查图纸…
        </div>
      )}
      {error && <div className="status error" role="alert">{error}</div>}

      {result && (
        <div className="results">
          <section>
            <h2>标题栏信息</h2>
            <dl className="metadata">
              {titleFields.map(([key, label]) => (
                <div key={key}>
                  <dt>{label}</dt>
                  <dd>{String(result[key])}</dd>
                </div>
              ))}
            </dl>
          </section>

          <section>
            <h2>技术要求</h2>
            {result.tech_requirements.length > 0 ? (
              <ol>{result.tech_requirements.map((item, index) => <li key={index}>{item}</li>)}</ol>
            ) : (
              <p>无</p>
            )}
          </section>

          <section>
            <h2>尺寸列表</h2>
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>标称值</th><th>上偏差</th><th>下偏差</th>
                    <th>公差来源</th><th>类型</th><th>气泡号</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedDimensions.map((dimension, index) => (
                    <tr key={`${dimension.bubble_id ?? 'none'}-${index}`}>
                      <td>{dimension.nominal}</td>
                      <td>{display(dimension.upper_deviation)}</td>
                      <td>{display(dimension.lower_deviation)}</td>
                      <td>{toleranceSource(dimension)}</td>
                      <td>{dimension.dimension_type}</td>
                      <td>{display(dimension.bubble_id)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {result.hole_features.length > 0 && (
            <section>
              <h2>孔位汇总</h2>
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>标签</th><th>类型</th><th>孔径</th><th>深度</th>
                      <th>沉孔径</th><th>沉孔深度</th><th>螺纹规格</th>
                      <th>底孔</th><th>数量</th><th>背面加工</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.hole_features.map((hole, index) => (
                      <tr key={`${hole.label}-${index}`}>
                        <td>{hole.label}</td>
                        <td>{hole.hole_type}</td>
                        <td>{hole.primary_diameter}</td>
                        <td>{hole.depth}</td>
                        <td>{display(hole.counterbore_diameter)}</td>
                        <td>{display(hole.counterbore_depth)}</td>
                        <td>{display(hole.thread_spec)}</td>
                        <td>{display(hole.pilot_hole)}</td>
                        <td>{hole.quantity}</td>
                        <td>{hole.back_side ? '是' : '否'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          <div className="downloads">
            <a href={result.excel_download_url}>下载检查基准书(Excel)</a>
            <a href={result.bubble_diagram_download_url}>下载气泡图(PDF)</a>
          </div>
        </div>
      )}
    </main>
  )
}

export default App
