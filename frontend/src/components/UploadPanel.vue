<template>
  <div>
    <section class="hero-band">
      <article class="panel upload-panel">
        <div class="panel-head">
          <div>
            <div class="eyebrow">上传视频</div>
            <h2 class="panel-title">拖拽或选择视频文件</h2>
          </div>
        </div>
        <div
          class="drop-zone"
          :class="{ dragging: isDragging, uploading: isUploading }"
          @click="triggerFileInput"
          @dragover.prevent="isDragging = true"
          @dragleave="isDragging = false"
          @drop.prevent="handleDrop"
        >
          <div class="drop-content">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="drop-icon"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
            <p class="drop-text">拖拽视频文件到此处</p>
            <p class="drop-hint">或点击选择文件</p>
          </div>
        </div>
        <input ref="fileInputRef" type="file" accept="video/*" multiple style="display:none" @change="handleFileSelect" />

        <div class="format-row">
          <span class="format-label">支持格式</span>
          <span class="format-tag" v-for="fmt in formats" :key="fmt">{{ fmt }}</span>
        </div>

        <div v-if="isUploading" class="progress-section">
          <div class="progress-header">
            <span>{{ uploadStatus }}</span>
            <span>{{ uploadProgress }}%</span>
          </div>
          <div class="progress">
            <span :style="{ width: uploadProgress + '%' }"></span>
          </div>
        </div>
      </article>

      <article class="panel">
        <div class="eyebrow">上传须知</div>
        <div class="info-list">
          <div class="info-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
            <span>支持 MP4、MOV、AVI、MKV 格式</span>
          </div>
          <div class="info-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
            <span>上传后自动拆分镜头片段</span>
          </div>
          <div class="info-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
            <span>AI 自动识别分类并添加标签</span>
          </div>
          <div class="info-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
            <span>处理时间取决于视频长度</span>
          </div>
        </div>
      </article>
    </section>

    <section class="recent-section">
      <article class="panel">
        <div class="panel-head">
          <div>
            <div class="eyebrow">最近上传</div>
            <h2 class="panel-title">上传记录</h2>
          </div>
          <button class="btn ghost" @click="loadVideos">刷新</button>
        </div>

        <div v-if="videos.length === 0" class="empty-state">
          <span class="muted">暂无上传记录，请上传视频文件</span>
        </div>

        <div v-else class="video-list">
          <div class="list-item" v-for="video in videos" :key="video.id">
            <div class="row-between">
              <div class="item-info">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>
                <strong>{{ video.video_name }}</strong>
              </div>
              <span class="tag" :class="statusClass(video.status)">{{ statusText(video.status) }}</span>
            </div>
            <div class="item-meta">
              <span class="muted">{{ formatTime(video.upload_time) }}</span>
              <span class="muted" v-if="video.creator_name">{{ video.creator_name }}</span>
            </div>
          </div>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const fileInputRef = ref(null)
const isDragging = ref(false)
const isUploading = ref(false)
const uploadProgress = ref(0)
const uploadStatus = ref('')
const videos = ref([])
const formats = ['MP4', 'MOV', 'AVI', 'MKV']

const triggerFileInput = () => {
  fileInputRef.value?.click()
}

const handleDrop = (e) => {
  isDragging.value = false
  const files = Array.from(e.dataTransfer.files)
  uploadFiles(files)
}

const handleFileSelect = (e) => {
  const files = Array.from(e.target.files)
  uploadFiles(files)
}

const uploadFiles = async (files) => {
  if (files.length === 0) return

  isUploading.value = true
  uploadProgress.value = 0
  uploadStatus.value = '正在上传...'

  for (let i = 0; i < files.length; i++) {
    const file = files[i]
    const formData = new FormData()
    formData.append('file', file)

    try {
      uploadStatus.value = `正在处理: ${file.name}`
      await axios.post('/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 600000
      })
      uploadProgress.value = Math.round(20 + ((i + 1) / files.length) * 80)
    } catch (error) {
      console.error('上传错误:', error)
    }
  }

  uploadProgress.value = 100
  uploadStatus.value = '处理完成'

  setTimeout(() => {
    isUploading.value = false
    uploadProgress.value = 0
    if (fileInputRef.value) fileInputRef.value.value = ''
    loadVideos()
  }, 1500)
}

const loadVideos = async () => {
  try {
    const res = await axios.get('/api/videos')
    videos.value = res.data
  } catch (e) {
    console.error('加载视频列表失败:', e)
  }
}

const statusText = (status) => {
  const map = { processing: '处理中', completed: '已完成', failed: '失败' }
  return map[status] || status
}

const statusClass = (status) => {
  const map = { processing: 'processing', completed: 'completed', failed: 'failed' }
  return map[status] || ''
}

const formatTime = (time) => {
  if (!time) return ''
  const d = new Date(time)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

onMounted(() => {
  loadVideos()
})
</script>

<style scoped>
.hero-band {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(18rem, 0.9fr);
  gap: calc(var(--spacing) * 3);
}

.panel {
  background: var(--card);
  color: var(--card-foreground);
  border: 1px solid var(--border);
  border-radius: calc(var(--radius) * 0.82);
  box-shadow: var(--shadow-xs);
  padding: calc(var(--spacing) * 4);
  display: grid;
  gap: calc(var(--spacing) * 2.6);
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: calc(var(--spacing) * 2);
}

.panel-title {
  margin: 0;
  font-size: 1.35rem;
  line-height: 1.08;
}

.eyebrow {
  color: var(--muted-foreground);
  font-size: 0.73rem;
  text-transform: uppercase;
  letter-spacing: 0.14em;
}

.muted {
  color: var(--muted-foreground);
}

.drop-zone {
  border: 2px dashed var(--accent);
  border-radius: calc(var(--radius) * 0.76);
  padding: calc(var(--spacing) * 8) calc(var(--spacing) * 4);
  text-align: center;
  cursor: pointer;
  transition: background-color .2s ease, border-color .2s ease, transform .18s ease;
}

.drop-zone:hover {
  background: hsl(var(--accent) / 0.12);
  transform: translateY(-1px);
}

.drop-zone.dragging {
  border-color: var(--secondary);
  background: hsl(var(--secondary) / 0.08);
}

.drop-zone.uploading {
  pointer-events: none;
  opacity: 0.6;
}

.drop-content {
  display: grid;
  gap: calc(var(--spacing) * 2);
  justify-items: center;
}

.drop-icon {
  color: var(--muted-foreground);
}

.drop-text {
  font-size: 1.1rem;
  color: var(--foreground);
}

.drop-hint {
  font-size: 0.88rem;
  color: var(--muted-foreground);
}

.format-row {
  display: flex;
  align-items: center;
  gap: calc(var(--spacing) * 1.5);
  flex-wrap: wrap;
}

.format-label {
  color: var(--muted-foreground);
  font-size: 0.88rem;
}

.format-tag {
  display: inline-flex;
  align-items: center;
  gap: calc(var(--spacing) * 1);
  width: fit-content;
  padding: calc(var(--spacing) * 0.8) calc(var(--spacing) * 1.6);
  border-radius: 999px;
  background: var(--muted);
  color: var(--muted-foreground);
  font-size: 0.78rem;
}

.progress-section {
  display: grid;
  gap: calc(var(--spacing) * 1.5);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  font-size: 0.88rem;
  color: var(--muted-foreground);
}

.progress {
  width: 100%;
  height: 0.55rem;
  background: var(--muted);
  border-radius: 999px;
  overflow: hidden;
}

.progress span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--secondary);
  transition: width 0.3s ease;
}

.info-list {
  display: grid;
  gap: calc(var(--spacing) * 2);
}

.info-item {
  display: flex;
  align-items: center;
  gap: calc(var(--spacing) * 2);
  font-size: 0.95rem;
  color: var(--accent-foreground);
}

.info-item svg {
  color: var(--muted-foreground);
  flex-shrink: 0;
}

.btn {
  border: 1px solid transparent;
  border-radius: calc(var(--radius) * 0.76);
  cursor: pointer;
  font-family: inherit;
  letter-spacing: inherit;
  min-height: 2.95rem;
  padding: calc(var(--spacing) * 2.1) calc(var(--spacing) * 4);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: calc(var(--spacing) * 1.6);
  box-shadow: var(--shadow-sm);
  transition: transform .18s ease, background-color .18s ease, border-color .18s ease;
  font-size: 0.95rem;
}

.btn:hover {
  transform: translateY(-1px);
}

.btn:active {
  transform: scale(0.98);
}

.btn.ghost {
  background: transparent;
  color: var(--accent-foreground);
  border-color: var(--border);
  box-shadow: none;
}

.recent-section {
  display: grid;
  gap: calc(var(--spacing) * 3);
}

.empty-state {
  text-align: center;
  padding: calc(var(--spacing) * 6) 0;
}

.video-list {
  display: grid;
  gap: 0;
}

.list-item {
  display: grid;
  gap: calc(var(--spacing) * 1.1);
  padding: calc(var(--spacing) * 2.3) 0;
  border-top: 1px solid var(--border);
}

.list-item:first-child {
  border-top: 0;
  padding-top: 0;
}

.row-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: calc(var(--spacing) * 2);
}

.item-info {
  display: flex;
  align-items: center;
  gap: calc(var(--spacing) * 2);
}

.item-info svg {
  color: var(--muted-foreground);
  flex-shrink: 0;
}

.item-meta {
  display: flex;
  gap: calc(var(--spacing) * 3);
  font-size: 0.88rem;
}

.tag {
  display: inline-flex;
  align-items: center;
  gap: calc(var(--spacing) * 1);
  width: fit-content;
  padding: calc(var(--spacing) * 0.8) calc(var(--spacing) * 1.6);
  border-radius: 999px;
  background: var(--muted);
  color: var(--muted-foreground);
  font-size: 0.78rem;
}

.tag.completed {
  background: hsl(120 30% 85%);
  color: hsl(120 30% 30%);
}

.tag.processing {
  background: hsl(45 80% 90%);
  color: hsl(45 60% 35%);
}

.tag.failed {
  background: hsl(0 70% 92%);
  color: hsl(0 70% 45%);
}

@media (max-width: 1100px) {
  .hero-band { grid-template-columns: 1fr; }
}
</style>
