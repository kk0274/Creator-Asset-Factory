<template>
  <div class="detail-panel" @click.stop>
    <div class="detail-header">
      <div>
        <div class="eyebrow">素材详情</div>
        <h2 class="detail-title">{{ scene?.scene_name || '' }}</h2>
      </div>
      <button class="btn-icon" @click="$emit('close')" aria-label="关闭">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </button>
    </div>

    <div class="detail-body">
      <div class="detail-video" v-if="scene?.scene_path">
        <video
          :src="scene.scene_path.replace(/\\/g, '/')"
          controls
          preload="metadata"
          style="width:100%; border-radius: calc(var(--radius) * 0.5);"
        ></video>
      </div>

      <div class="detail-meta-grid">
        <div class="meta-card">
          <span class="meta-label">分类</span>
          <span class="meta-value">{{ scene?.category || '--' }}</span>
        </div>
        <div class="meta-card">
          <span class="meta-label">产品分类</span>
          <span class="meta-value">{{ scene?.product_category || '--' }}</span>
        </div>
        <div class="meta-card">
          <span class="meta-label">时长</span>
          <span class="meta-value">{{ formatDuration(scene?.duration) }}</span>
        </div>
        <div class="meta-card">
          <span class="meta-label">镜头编号</span>
          <span class="meta-value">{{ scene?.scene_number ?? '--' }}</span>
        </div>
        <div class="meta-card">
          <span class="meta-label">达人</span>
          <span class="meta-value">{{ scene?.creator_name || '--' }}</span>
        </div>
        <div class="meta-card">
          <span class="meta-label">来源视频</span>
          <span class="meta-value">{{ scene?.video_name || '--' }}</span>
        </div>
      </div>

      <div class="detail-tags" v-if="scene?.tags?.length">
        <span class="meta-label">标签</span>
        <div class="tag-list">
          <span class="tag" v-for="tag in scene.tags" :key="tag">{{ tag }}</span>
        </div>
      </div>

      <div class="detail-actions">
        <button class="btn primary" @click="downloadScene">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          下载素材
        </button>
        <button class="btn destructive" @click="deleteScene">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          删除
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import axios from 'axios'

const props = defineProps({
  scene: Object
})

const emit = defineEmits(['close'])

const formatDuration = (dur) => {
  if (!dur) return '--:--'
  const m = Math.floor(dur / 60)
  const s = Math.floor(dur % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

const downloadScene = () => {
  if (!props.scene?.scene_path) return
  const link = document.createElement('a')
  link.href = props.scene.scene_path.replace(/\\/g, '/')
  link.download = props.scene.scene_name
  link.click()
}

const deleteScene = async () => {
  if (!props.scene?.id) return
  if (!confirm('确定要删除这个素材吗？此操作不可撤销。')) return

  try {
    await axios.delete(`/api/scenes/${props.scene.id}`)
    emit('close')
  } catch (e) {
    console.error('删除失败:', e)
    alert('删除失败')
  }
}
</script>

<style scoped>
.detail-panel {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: calc(var(--radius) * 0.82);
  box-shadow: var(--shadow-sm);
  width: 90%;
  max-width: 720px;
  max-height: 85vh;
  overflow-y: auto;
  display: grid;
  gap: calc(var(--spacing) * 3);
  animation: slideUp .25s ease;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.detail-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: calc(var(--spacing) * 2);
  padding: calc(var(--spacing) * 4);
  border-bottom: 1px solid var(--border);
}

.eyebrow {
  color: var(--muted-foreground);
  font-size: 0.73rem;
  text-transform: uppercase;
  letter-spacing: 0.14em;
}

.detail-title {
  margin: calc(var(--spacing) * 0.5) 0 0;
  font-size: 1.35rem;
  line-height: 1.08;
}

.btn-icon {
  width: 2.9rem;
  height: 2.9rem;
  border: 1px solid var(--border);
  border-radius: calc(var(--radius) * 0.76);
  background: var(--card);
  color: var(--foreground);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: transform .18s ease, background-color .18s ease;
  flex-shrink: 0;
}

.btn-icon:hover {
  transform: translateY(-1px);
  background: var(--muted);
}

.detail-body {
  padding: calc(var(--spacing) * 4);
  display: grid;
  gap: calc(var(--spacing) * 3);
}

.detail-video {
  border-radius: calc(var(--radius) * 0.5);
  overflow: hidden;
}

.detail-meta-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: calc(var(--spacing) * 2);
}

.meta-card {
  background: var(--muted);
  border-radius: calc(var(--radius) * 0.65);
  padding: calc(var(--spacing) * 2.4);
  display: grid;
  gap: calc(var(--spacing) * 1);
}

.meta-label {
  color: var(--muted-foreground);
  font-size: 0.73rem;
  text-transform: uppercase;
  letter-spacing: 0.14em;
}

.meta-value {
  font-size: 0.95rem;
  font-weight: 500;
}

.detail-tags {
  display: grid;
  gap: calc(var(--spacing) * 1.5);
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: calc(var(--spacing) * 1);
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

.detail-actions {
  display: flex;
  gap: calc(var(--spacing) * 2);
  padding-top: calc(var(--spacing) * 2);
  border-top: 1px solid var(--border);
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
  transition: transform .18s ease, background-color .18s ease;
  font-size: 0.95rem;
}

.btn:hover {
  transform: translateY(-1px);
}

.btn:active {
  transform: scale(0.98);
}

.btn.primary {
  background: var(--primary);
  color: var(--primary-foreground);
}

.btn.destructive {
  background: var(--destructive);
  color: var(--destructive-foreground);
}

@media (max-width: 600px) {
  .detail-meta-grid { grid-template-columns: repeat(2, 1fr); }
  .detail-actions { flex-direction: column; }
}
</style>
