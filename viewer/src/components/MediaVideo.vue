<template>
  <div ref="containerRef" class="media-video-container rounded border overflow-hidden bg-black position-relative">
    <video
      v-if="mediaUrl"
      :src="mediaUrl"
      controls
      preload="metadata"
      class="embedded-video"
      playsinline
    ></video>
    <div v-else class="video-placeholder d-flex flex-column align-center justify-center">
      <v-progress-circular v-if="isLoading" indeterminate size="28" width="2" color="primary"></v-progress-circular>
      <v-icon v-else icon="mdi-video-outline" color="medium-emphasis" size="40"></v-icon>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps<{
  filename: string
  getMediaUrl: (filename: string) => Promise<string>
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
    console.error('Failed to load video:', props.filename, err)
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
.media-video-container {
  width: 100%;
  height: 220px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.embedded-video {
  width: 100%;
  height: 100%;
  object-fit: contain;
  outline: none;
  background: #000;
}

.video-placeholder {
  width: 100%;
  height: 100%;
  min-height: 200px;
  background-color: rgba(0, 0, 0, 0.2);
}
</style>
