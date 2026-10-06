<template>
  <div ref="containerRef" class="media-image-container rounded border cursor-pointer position-relative">
    <img
      v-if="mediaUrl"
      :src="mediaUrl"
      :alt="filename"
      class="media-img rounded"
      @click="$emit('click')"
    />
    <div v-else class="media-placeholder d-flex align-center justify-center">
      <v-progress-circular v-if="isLoading" indeterminate size="28" width="2" color="primary"></v-progress-circular>
      <v-icon v-else icon="mdi-image-outline" color="medium-emphasis" size="36"></v-icon>
    </div>
    
    <!-- 拡大アイコンバッジ -->
    <div v-if="mediaUrl" class="zoom-badge" @click.stop="$emit('click')" title="大画面で拡大">
      <v-icon size="14" color="white" icon="mdi-magnify-plus-outline"></v-icon>
      <span class="text-caption ml-1 text-white" style="font-size: 0.7rem;">拡大</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps<{
  filename: string
  getMediaUrl: (filename: string) => Promise<string>
}>()

defineEmits<{
  (e: 'click'): void
}>()

const containerRef = ref<HTMLElement | null>(null)
const mediaUrl = ref<string>('')
const isLoading = ref<boolean>(false)
let observer: IntersectionObserver | null = null

const loadMedia = async () => {
  if (mediaUrl.value || !props.filename) return
  isLoading.value = true
  try {
    mediaUrl.value = await props.getMediaUrl(props.filename)
  } catch (err) {
    console.error('Failed to load image:', props.filename, err)
  } finally {
    isLoading.value = false
  }
}

watch(() => props.filename, () => {
  mediaUrl.value = ''
  loadMedia()
})

onMounted(() => {
  observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) {
      loadMedia()
      if (observer && containerRef.value) {
        observer.unobserve(containerRef.value)
      }
    }
  }, { rootMargin: '250px' })

  if (containerRef.value) {
    observer.observe(containerRef.value)
  }
})

onUnmounted(() => {
  if (observer) {
    observer.disconnect()
  }
})
</script>

<style scoped>
.media-image-container {
  width: 100%;
  height: 220px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(0, 0, 0, 0.25);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.media-image-container:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
}

.media-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

.media-placeholder {
  width: 100%;
  height: 100%;
  min-height: 200px;
}

.zoom-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.75);
  padding: 3px 8px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  opacity: 0.85;
  transition: opacity 0.15s ease;
}

.media-image-container:hover .zoom-badge {
  opacity: 1;
}
</style>
