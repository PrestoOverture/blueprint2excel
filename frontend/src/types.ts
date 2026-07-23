export interface Dimension {
  nominal: number
  upper_deviation: number | null
  lower_deviation: number | null
  tolerance_grade: string | null
  dimension_type: string
  x: number
  y: number
  bubble_id: number | null
}

export interface HoleFeature {
  label: string
  hole_type: string
  primary_diameter: number | string
  depth: number | string
  counterbore_diameter: number | null
  counterbore_depth: number | null
  thread_spec: string | null
  pilot_hole: number | null
  quantity: number
  back_side: boolean
}

export interface InspectionResult {
  job_id: string
  drawing_number: string
  part_name: string
  material: string
  scale: string
  date: string
  tolerance_standard: string
  tech_requirements: string[]
  dimensions: Dimension[]
  hole_features: HoleFeature[]
  excel_download_url: string
  bubble_diagram_download_url: string
}

export interface ApiError {
  detail?: string
}
