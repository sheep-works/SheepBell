/**
 * SheepBell から出力されたオリジナルの Issue 型定義
 */
export interface LqaIssue {
  id: number
  file_prefix?: string
  clip_path?: string
  snapshot_path?: string
  timestamp_start?: number
  timestamp_end?: number
  issue_tag?: string
  description?: string
  [key: string]: unknown
}

/**
 * レビュー・編集後の Issue 型定義
 */
export interface LqaIssueReview extends LqaIssue {
  comment: string
  status?: 'open' | 'in_progress' | 'fixed' | 'won_t_fix' | string
  severity?: 'critical' | 'major' | 'minor' | 'trivial' | string
  category?: string
  assignee?: string
}

/**
 * クライアント別・用途別エクスポーター / パーサーのインターフェース
 * 今後、クライアントごとのカスタム出力フォーマットをここに追加・拡張できます
 */
export interface IssueExporter {
  id: string
  name: string
  description?: string
  fileExtension: string
  mimeType: string
  /**
   * Issue リストを対象フォーマットの文字列または Blob に変換
   */
  export(issues: LqaIssueReview[]): string | Blob | Promise<string | Blob>
}

/**
 * 保存オプション
 */
export interface SaveOptions {
  silent?: boolean
  reason?: 'manual' | 'interval' | 'page_change' | 'blur' | string
}
