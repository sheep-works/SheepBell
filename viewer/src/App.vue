<template>
  <v-app>
    <!-- App Bar -->
    <v-app-bar color="surface" elevation="1" density="comfortable">
      <v-app-bar-title class="font-weight-bold d-flex align-center">
        <span class="text-primary text-h6 mr-2">🔔 SheepBell</span>
        <span class="text-subtitle-1 text-medium-emphasis">LQA Issues Editor</span>
        <v-chip v-if="folderName" size="small" color="primary" variant="tonal" class="ml-3 font-weight-medium">
          <v-icon start icon="mdi-folder-open-outline"></v-icon>
          {{ folderName }}
        </v-chip>
        <v-chip v-if="loadedFileName" size="x-small" color="secondary" variant="outlined" class="ml-2 font-mono">
          {{ loadedFileName }}
        </v-chip>
      </v-app-bar-title>

      <v-spacer></v-spacer>

      <!-- 最終保存ログ / ステータス -->
      <span v-if="lastSavedTime" class="text-caption text-medium-emphasis mr-3">
        最終保存: {{ lastSavedTime }}
      </span>

      <!-- 未保存インジケーター -->
      <v-chip
        v-if="hasUnsavedChanges"
        color="warning"
        variant="flat"
        size="small"
        class="mr-3 animate-pulse"
      >
        <v-icon start icon="mdi-alert-circle-outline"></v-icon>
        未保存の変更あり
      </v-chip>

      <!-- フォルダを開くボタン -->
      <v-btn
        variant="tonal"
        color="primary"
        class="mr-2"
        prepend-icon="mdi-folder-open"
        @click="handleOpenDirectoryClick"
        :loading="isLoading"
      >
        フォルダを開く
      </v-btn>

      <!-- 保存ボタン (Ctrl+S) -->
      <v-btn
        v-if="issues.length > 0"
        variant="flat"
        color="primary"
        class="mr-2"
        prepend-icon="mdi-content-save"
        @click="() => saveIssues({ reason: 'manual' })"
        :disabled="!isFileSystemAccessSupported && !currentDirHandle"
      >
        保存 <span class="text-caption ml-1 opacity-75">(Ctrl+S)</span>
      </v-btn>

      <!-- エクスポートメニュー (登録済みエクスポーターから選択可能) -->
      <v-menu v-if="issues.length > 0">
        <template v-slot:activator="{ props }">
          <v-btn
            v-bind="props"
            variant="outlined"
            color="primary"
            class="mr-2"
            prepend-icon="mdi-export-variant"
          >
            エクスポート
          </v-btn>
        </template>
        <v-list density="compact">
          <v-list-item
            v-for="exporter in availableExporters"
            :key="exporter.id"
            :prepend-icon="exporter.fileExtension === 'csv' ? 'mdi-file-delimited' : 'mdi-code-json'"
            :title="exporter.name"
            :subtitle="exporter.description"
            @click="handleExport(exporter)"
          ></v-list-item>
        </v-list>
      </v-menu>

      <!-- テーマ切替 -->
      <v-btn
        icon
        variant="text"
        @click="toggleTheme"
        :title="theme.global.current.value.dark ? 'ライトモードに切替' : 'ダークモードに切替'"
      >
        <v-icon>{{ theme.global.current.value.dark ? 'mdi-weather-sunny' : 'mdi-weather-night' }}</v-icon>
      </v-btn>
    </v-app-bar>

    <v-main class="bg-background">
      <v-container fluid class="pa-4 pa-md-6">
        <!-- 未読み込み時のウェルカム表示 -->
        <v-sheet
          v-if="issues.length === 0 && !isLoading"
          class="d-flex flex-column align-center justify-center rounded-xl pa-8 pa-md-16 mx-auto text-center border"
          max-width="700"
          elevation="0"
          color="surface"
        >
          <v-avatar color="primary" variant="tonal" size="96" class="mb-4">
            <v-icon icon="mdi-folder-video-outline" size="56"></v-icon>
          </v-avatar>
          <h2 class="text-h5 font-weight-bold mb-2">issues フォルダを開いてください</h2>
          <p class="text-body-1 text-medium-emphasis mb-6" style="max-width: 500px">
            SheepBell で出力された <code>lqa_issues.json</code>（または保存済み <code>lqa_issues_review.json</code>）や動画・画像が入っているフォルダを選択します。
          </p>
          <v-btn
            color="primary"
            size="large"
            prepend-icon="mdi-folder-open"
            @click="handleOpenDirectoryClick"
            elevation="2"
          >
            フォルダを選択
          </v-btn>

          <input
            ref="fallbackFolderInput"
            type="file"
            webkitdirectory
            directory
            style="display: none"
            @change="handleFallbackFolderSelect"
          />

          <div v-if="!isFileSystemAccessSupported" class="mt-4 text-caption text-warning">
            ※ お使いのブラウザは File System Access API に直接対応していませんが、ファイル選択で読み込みとダウンロード保存が利用できます。
          </div>
        </v-sheet>

        <!-- ロード中のプログレス -->
        <v-sheet
          v-else-if="isLoading"
          class="d-flex flex-column align-center justify-center rounded-xl pa-12 text-center"
          elevation="0"
          color="surface"
        >
          <v-progress-circular indeterminate color="primary" size="64" width="6" class="mb-4"></v-progress-circular>
          <div class="text-h6 font-weight-medium">フォルダを読み込み中...</div>
          <div class="text-body-2 text-medium-emphasis mt-1">{{ loadingMessage }}</div>
        </v-sheet>

        <!-- メインデータテーブルビュー -->
        <div v-else>
          <!-- ツールバー / 検索フィルタ & 一括メディア切替 -->
          <v-card class="mb-4 pa-4" elevation="1" rounded="lg">
            <v-row align="center" density="comfortable">
              <v-col cols="12" sm="5" md="3">
                <v-text-field
                  v-model="searchFilter"
                  prepend-inner-icon="mdi-magnify"
                  label="Description / Comment / ID を検索..."
                  density="compact"
                  variant="outlined"
                  hide-details
                  clearable
                ></v-text-field>
              </v-col>

              <v-col cols="6" sm="3" md="2">
                <v-select
                  v-model="commentFilter"
                  :items="[
                    { title: 'すべて', value: 'all' },
                    { title: 'コメントあり', value: 'has_comment' },
                    { title: 'コメント未記入', value: 'no_comment' }
                  ]"
                  density="compact"
                  variant="outlined"
                  label="コメント状態"
                  hide-details
                ></v-select>
              </v-col>

              <v-col cols="6" sm="3" md="2" v-if="availableTags.length > 0">
                <v-select
                  v-model="selectedTag"
                  :items="['すべて', ...availableTags]"
                  density="compact"
                  variant="outlined"
                  label="タグ絞り込み"
                  hide-details
                ></v-select>
              </v-col>

              <!-- 全行一括メディア表示切替 -->
              <v-col cols="12" sm="auto" class="d-flex align-center">
                <span class="text-caption text-medium-emphasis mr-2">全表示切替:</span>
                <v-btn-toggle
                  v-model="globalMediaView"
                  mandatory
                  density="compact"
                  color="primary"
                  variant="outlined"
                  @update:model-value="setAllMediaView"
                >
                  <v-btn value="image" size="small" prepend-icon="mdi-image-outline">
                    画像
                  </v-btn>
                  <v-btn value="video" size="small" prepend-icon="mdi-video-outline">
                    動画
                  </v-btn>
                </v-btn-toggle>
              </v-col>

              <v-spacer></v-spacer>

              <v-col cols="12" sm="auto" class="d-flex align-center justify-end">
                <span class="text-body-2 text-medium-emphasis mr-2">
                  表示中: <strong>{{ filteredIssues.length }}</strong> / 全 {{ issues.length }} 件
                </span>
                <v-btn
                  size="small"
                  variant="text"
                  icon="mdi-refresh"
                  title="メディアキャッシュをリフレッシュ"
                  @click="clearMediaCaches"
                ></v-btn>
              </v-col>
            </v-row>
          </v-card>

          <!-- DataTable -->
          <v-card elevation="1" rounded="lg" class="overflow-hidden">
            <v-data-table
              v-model:page="currentPage"
              v-model:items-per-page="itemsPerPage"
              :headers="headers"
              :items="filteredIssues"
              :items-per-page-options="[
                { value: 10, title: '10' },
                { value: 20, title: '20' },
                { value: 50, title: '50' },
                { value: 100, title: '100' },
                { value: -1, title: 'すべて' }
              ]"
              hover
              class="lqa-table"
            >
              <!-- ID & タイムスタンプ列 -->
              <template v-slot:item.id="{ item }">
                <div class="d-flex flex-column align-start py-2">
                  <v-tooltip location="top" content-class="custom-tooltip">
                    <template v-slot:activator="{ props }">
                      <v-chip
                        v-bind="props"
                        size="small"
                        color="primary"
                        variant="elevated"
                        class="font-weight-bold font-mono mb-1"
                      >
                        #{{ item.id }}
                      </v-chip>
                    </template>
                    <div class="tooltip-body text-caption font-mono text-white">
                      <div class="font-weight-bold text-teal-lighten-3 mb-1">Issue #{{ item.id }} ({{ item.file_prefix || '-' }})</div>
                      <div><strong>Start:</strong> {{ formatTime(item.timestamp_start) }} ({{ item.timestamp_start }}s)</div>
                      <div><strong>End:</strong> {{ formatTime(item.timestamp_end) }} ({{ item.timestamp_end }}s)</div>
                      <div><strong>Duration:</strong> {{ getDuration(item.timestamp_start, item.timestamp_end) }}s</div>
                    </div>
                  </v-tooltip>

                  <div class="text-caption font-mono text-medium-emphasis" style="font-size: 0.75rem;">
                    {{ formatTime(item.timestamp_start) }}
                  </div>
                  <div class="text-caption font-mono text-disabled" style="font-size: 0.7rem;">
                    ({{ getDuration(item.timestamp_start, item.timestamp_end) }}s)
                  </div>
                </div>
              </template>

              <!-- 統合メディア列 (画像 / 動画 トグル切り替え) -->
              <template v-slot:item.media="{ item }">
                <div class="integrated-media-cell py-2 px-1">
                  <!-- 上部トグルボタンバー -->
                  <div class="d-flex align-center justify-space-between mb-1">
                    <div class="text-caption font-mono text-medium-emphasis text-truncate" style="max-width: 250px;">
                      <v-icon size="14" class="mr-1">
                        {{ getRowMediaMode(item.id) === 'video' ? 'mdi-video-outline' : 'mdi-image-outline' }}
                      </v-icon>
                      {{ getRowMediaMode(item.id) === 'video' ? (item.clip_path || '動画なし') : (item.snapshot_path || '画像なし') }}
                    </div>

                    <!-- 行ごとの切り替えトグル -->
                    <v-btn-toggle
                      :model-value="getRowMediaMode(item.id)"
                      mandatory
                      density="compact"
                      color="primary"
                      variant="tonal"
                      class="row-toggle"
                      @update:model-value="(val: 'image' | 'video') => setRowMediaMode(item.id, val)"
                    >
                      <v-btn
                        value="image"
                        size="x-small"
                        icon="mdi-image-outline"
                        :disabled="!item.snapshot_path"
                        title="スナップショット画像を表示"
                      ></v-btn>
                      <v-btn
                        value="video"
                        size="x-small"
                        icon="mdi-video-outline"
                        :disabled="!item.clip_path"
                        title="動画クリップを表示"
                      ></v-btn>
                    </v-btn-toggle>
                  </div>

                  <!-- メディア表示エリア -->
                  <div class="media-display-box">
                    <!-- 動画プレイヤー -->
                    <media-video
                      v-if="getRowMediaMode(item.id) === 'video' && item.clip_path"
                      :filename="item.clip_path"
                      :get-media-url="getMediaUrl"
                    />

                    <!-- スナップショット画像 -->
                    <media-image
                      v-else-if="item.snapshot_path"
                      :filename="item.snapshot_path"
                      :get-media-url="getMediaUrl"
                      @click="openImageModal(item)"
                    />

                    <div v-else class="text-caption text-disabled text-center py-8">
                      メディアファイルがありません
                    </div>
                  </div>
                </div>
              </template>

              <!-- タグ列 -->
              <template v-slot:item.issue_tag="{ item }">
                <v-chip
                  v-if="item.issue_tag"
                  size="x-small"
                  color="secondary"
                  variant="outlined"
                >
                  {{ item.issue_tag }}
                </v-chip>
                <span v-else class="text-disabled text-caption">-</span>
              </template>

              <!-- Description (編集可能 textarea) -->
              <template v-slot:item.description="{ item }">
                <v-textarea
                  v-model="item.description"
                  variant="outlined"
                  density="compact"
                  rows="5"
                  auto-grow
                  hide-details
                  class="my-2 edit-textarea"
                  placeholder="バグや指摘内容..."
                  @update:model-value="markChanged"
                ></v-textarea>
              </template>

              <!-- Comment (編集可能 textarea) -->
              <template v-slot:item.comment="{ item }">
                <v-textarea
                  v-model="item.comment"
                  variant="outlined"
                  density="compact"
                  rows="5"
                  auto-grow
                  hide-details
                  class="my-2 edit-textarea comment-input"
                  placeholder="ユーザーコメントを入力..."
                  @update:model-value="markChanged"
                ></v-textarea>
              </template>
            </v-data-table>
          </v-card>
        </div>
      </v-container>
    </v-main>

    <!-- 画像拡大ダイアログ (Lightbox) -->
    <v-dialog v-model="imageDialog" max-width="1100px">
      <v-card v-if="activeItem" color="surface" class="rounded-lg overflow-hidden">
        <v-card-title class="d-flex justify-space-between align-center py-2 px-4 bg-surface-light">
          <span class="text-subtitle-1 font-weight-bold">
            #{{ activeItem.id }} スナップショット ({{ activeItem.snapshot_path }})
          </span>
          <v-btn icon="mdi-close" variant="text" size="small" @click="imageDialog = false"></v-btn>
        </v-card-title>
        <v-card-text class="pa-2 d-flex justify-center bg-black">
          <img
            :src="activeMediaUrl"
            alt="Snapshot"
            style="max-width: 100%; max-height: 80vh; object-fit: contain;"
          />
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- スナックバー通知 -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000" location="bottom right">
      {{ snackbar.text }}
      <template v-slot:actions>
        <v-btn variant="text" @click="snackbar.show = false">閉じる</v-btn>
      </template>
    </v-snackbar>
  </v-app>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useTheme } from 'vuetify'
import MediaImage from './components/MediaImage.vue'
import MediaVideo from './components/MediaVideo.vue'
import { useIssueManager } from './composables/useIssueManager'
import { availableExporters, downloadExportedFile } from './exporters'
import type { LqaIssueReview, IssueExporter } from './types/issue'

// テーマ
const theme = useTheme()
const toggleTheme = () => {
  theme.global.name.value = theme.global.current.value.dark ? 'light' : 'dark'
}

// Issue 管理 Composable
const {
  issues,
  folderName,
  loadedFileName,
  currentDirHandle,
  hasUnsavedChanges,
  isLoading,
  loadingMessage,
  lastSavedTime,
  snackbar,
  showToast,
  markChanged,
  getMediaUrl,
  clearMediaCaches,
  saveIssues,
  openDirectory,
  loadFallbackFiles,
} = useIssueManager()

// メディア表示モード管理 (行ごとのモード保持 & 全体モード: デフォルト動画)
const globalMediaView = ref<'image' | 'video'>('video')
const rowMediaModes = ref<Record<number, 'image' | 'video'>>({})

const getRowMediaMode = (id: number): 'image' | 'video' => {
  return rowMediaModes.value[id] || globalMediaView.value
}

const setRowMediaMode = (id: number, mode: 'image' | 'video') => {
  rowMediaModes.value[id] = mode
}

const setAllMediaView = (mode: 'image' | 'video') => {
  globalMediaView.value = mode
  issues.value.forEach(item => {
    rowMediaModes.value[item.id] = mode
  })
}

// ページネーション (デフォルト 20件)
const currentPage = ref<number>(1)
const itemsPerPage = ref<number>(20)
const fallbackFolderInput = ref<HTMLInputElement | null>(null)

const handleOpenDirectoryClick = () => {
  openDirectory(fallbackFolderInput.value)
}

// フィルタ
const searchFilter = ref<string>('')
const commentFilter = ref<'all' | 'has_comment' | 'no_comment'>('all')
const selectedTag = ref<string>('すべて')

// モーダル
const imageDialog = ref<boolean>(false)
const activeItem = ref<LqaIssueReview | null>(null)
const activeMediaUrl = ref<string>('')

let autoSaveTimer: ReturnType<typeof setInterval> | null = null
const isFileSystemAccessSupported = typeof window !== 'undefined' && 'showDirectoryPicker' in window

// ページ移動時の自動保存
watch(currentPage, async (_newPage, oldPage) => {
  if (hasUnsavedChanges.value && oldPage !== undefined) {
    await saveIssues({ silent: false, reason: 'page_change' })
  }
})

// ページ件数変更時の自動保存
watch(itemsPerPage, async () => {
  if (hasUnsavedChanges.value) {
    await saveIssues({ silent: true, reason: 'page_change' })
  }
})

// DataTable ヘッダー定義 (統合メディア列)
const headers = [
  { title: 'ID', key: 'id', align: 'start' as const, sortable: true, width: '90px' },
  { title: 'メディア (画像 / 動画)', key: 'media', sortable: false, width: '440px' },
  { title: 'タグ', key: 'issue_tag', sortable: true, width: '90px' },
  { title: 'Description (検出内容・文字起こし)', key: 'description', sortable: false },
  { title: 'Comment (作業メモ・フィードバック)', key: 'comment', sortable: false },
]

// タグ一覧
const availableTags = computed<string[]>(() => {
  const tags = new Set<string>()
  issues.value.forEach(item => {
    if (item.issue_tag) tags.add(item.issue_tag)
  })
  return Array.from(tags)
})

// フィルタリング処理
const filteredIssues = computed<LqaIssueReview[]>(() => {
  return issues.value.filter(item => {
    if (searchFilter.value) {
      const q = searchFilter.value.toLowerCase()
      const desc = (item.description || '').toLowerCase()
      const comm = (item.comment || '').toLowerCase()
      const idStr = String(item.id)
      if (!desc.includes(q) && !comm.includes(q) && !idStr.includes(q)) {
        return false
      }
    }

    if (commentFilter.value === 'has_comment') {
      if (!item.comment || item.comment.trim() === '') return false
    } else if (commentFilter.value === 'no_comment') {
      if (item.comment && item.comment.trim() !== '') return false
    }

    if (selectedTag.value && selectedTag.value !== 'すべて') {
      if (item.issue_tag !== selectedTag.value) return false
    }

    return true
  })
})

// タイムスタンプのフォーマット (秒 -> MM:SS.mmm)
const formatTime = (seconds?: number): string => {
  if (seconds == null || isNaN(seconds)) return '00:00.000'
  const min = Math.floor(seconds / 60)
  const sec = Math.floor(seconds % 60)
  const ms = Math.floor((seconds % 1) * 1000)
  return `${String(min).padStart(2, '0')}:${String(sec).padStart(2, '0')}.${String(ms).padStart(3, '0')}`
}

const getDuration = (start?: number, end?: number): string | number => {
  if (start == null || end == null) return 0
  return Math.max(0, (end - start)).toFixed(2)
}

// フォールバック用のディレクトリ選択
const handleFallbackFolderSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  loadFallbackFiles(target.files)
}

// エクスポーター実行
const handleExport = async (exporter: IssueExporter) => {
  if (issues.value.length === 0) return
  try {
    await downloadExportedFile(exporter, issues.value)
    showToast(`${exporter.name} をエクスポートしました`)
  } catch (err) {
    const error = err as Error
    showToast(`エクスポート失敗: ${error.message}`, 'error')
  }
}

// 画像拡大モーダル
const openImageModal = async (item: LqaIssueReview) => {
  activeItem.value = item
  activeMediaUrl.value = await getMediaUrl(item.snapshot_path)
  imageDialog.value = true
}

// キーボードショートカット (Ctrl+S) のハンドラ
const handleKeyDown = (e: KeyboardEvent) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault()
    saveIssues({ reason: 'manual' })
  }
}

// 離脱・更新のインターセプト (Dirty検知)
const handleBeforeUnload = (e: BeforeUnloadEvent) => {
  if (hasUnsavedChanges.value) {
    e.preventDefault()
    e.returnValue = '未保存の変更があります。ページを離れてもよろしいですか？'
    return e.returnValue
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
  window.addEventListener('beforeunload', handleBeforeUnload)

  // 5分ごとの自動保存タイマー (300,000ms)
  autoSaveTimer = setInterval(() => {
    if (hasUnsavedChanges.value && currentDirHandle.value) {
      saveIssues({ silent: true, reason: 'interval' })
    }
  }, 5 * 60 * 1000)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
  window.removeEventListener('beforeunload', handleBeforeUnload)
  if (autoSaveTimer) {
    clearInterval(autoSaveTimer)
  }
  clearMediaCaches()
})
</script>

<style>
/* ツールチップのグローバルスタイル */
.custom-tooltip {
  background-color: #0f172a !important;
  color: #ffffff !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5) !important;
  padding: 8px 12px !important;
  border-radius: 6px !important;
  opacity: 1 !important;
}
</style>

<style scoped>
.font-mono {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
}

.cursor-pointer {
  cursor: pointer;
}

/* 統合メディアセル */
.integrated-media-cell {
  width: 440px;
  min-width: 360px;
}

.row-toggle {
  height: 24px !important;
}

.row-toggle :deep(.v-btn) {
  height: 24px !important;
  min-width: 32px !important;
  padding: 0 6px !important;
}

.media-display-box {
  width: 100%;
}

/* テキストエリア */
.edit-textarea :deep(textarea) {
  font-size: 0.9rem;
  line-height: 1.45;
}

.comment-input :deep(.v-field) {
  background-color: rgba(20, 184, 166, 0.05);
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}
</style>
