import type { IssueExporter, LqaIssueReview } from '../types/issue'

/**
 * ユーティリティ: CSV セルのエスケープ
 */
export function escapeCsvCell(val: unknown): string {
  if (val == null) return '""'
  const str = String(val).replace(/"/g, '""')
  return `"${str}"`
}

/**
 * 標準 UTF-8 BOM 付き CSV エクスポーター
 */
export const defaultCsvExporter: IssueExporter = {
  id: 'standard-csv',
  name: '標準 CSV (Excel互換 UTF-8 BOM)',
  description: 'SheepBell 標準の CSV 形式',
  fileExtension: 'csv',
  mimeType: 'text/csv;charset=utf-8;',
  export(issues: LqaIssueReview[]): string {
    const headers = [
      'id',
      'file_prefix',
      'clip_path',
      'snapshot_path',
      'timestamp_start',
      'timestamp_end',
      'issue_tag',
      'description',
      'comment',
    ]

    const rows = issues.map((item) => {
      return headers
        .map((h) => escapeCsvCell(item[h as keyof LqaIssueReview]))
        .join(',')
    })

    return '\uFEFF' + [headers.join(','), ...rows].join('\r\n')
  },
}

/**
 * 標準 JSON エクスポーター
 */
export const defaultJsonExporter: IssueExporter = {
  id: 'standard-json',
  name: '標準 JSON',
  description: '編集後のレビュー済み JSON 形式',
  fileExtension: 'json',
  mimeType: 'application/json',
  export(issues: LqaIssueReview[]): string {
    return JSON.stringify(issues, null, 2)
  },
}

/**
 * 登録済みエクスポーターのリスト（将来ここに追加するだけでUIにも反映可能）
 */
export const availableExporters: IssueExporter[] = [
  defaultCsvExporter,
  defaultJsonExporter,
]

/**
 * エクスポーターを実行してブラウザダウンロードを行うヘルパー
 */
export async function downloadExportedFile(
  exporter: IssueExporter,
  issues: LqaIssueReview[],
  baseFilename = 'lqa_issues_review'
) {
  const result = await exporter.export(issues)
  let blob: Blob
  if (result instanceof Blob) {
    blob = result
  } else {
    blob = new Blob([result], { type: exporter.mimeType })
  }

  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${baseFilename}.${exporter.fileExtension}`
  a.click()
  URL.revokeObjectURL(url)
}
