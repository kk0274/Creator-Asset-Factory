<template>
  <div>
    <div class="filter-bar">
      <div class="filter-pills">
        <button
          class="pill"
          :class="{ active: activeCategory === '' }"
          @click="setCategory('')"
        >全部</button>
        <button
          class="pill"
          :class="{ active: activeCategory === cat }"
          v-for="cat in categories"
          :key="cat"
          @click="setCategory(cat)"
        >{{ cat }}</button>
      </div>
      <div class="filter-right">
        <span class="result-count muted">共 {{ total }} 个素材</span>
      </div>
    </div>

    <div v-if="scenes.length === 0" class="empty-state">
      <article class="panel">
        <div class="eyebrow">暂无素材</div>
        <h2 class="panel-title">请先上传视频</h2>
        <p class="muted">上传达人视频后，系统会自动拆分镜头并分类标注。</p>
      </article>
    </div>

    <div v-else class="gallery-grid">
      <article
        class="scene-card"
        v-for="scene in scenes"
        :key="scene.id"
        @click="$emit('view-detail', scene)"
      >
        <div class="card-thumb" :style="thumbStyle(scene)">
          <div class="thumb-overlay">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="white" stroke="none"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          </div>
          <span class="duration-badge">{{ formatDuration(scene.duration) }}</span>
        </div>
        <div class="card-body">
          <div class="card-title">{{ scene.scene_name }}</div>
          <div class="card-tags">
            <span class="tag" v-for="tag in scene.tags.slice(0, 3)" :key="tag">{{ tag }}</span>
          </div>
          <div class="card-meta">
            <span class="muted">{{ scene.category }}</span>
            <span class="muted" v-if="scene.creator_name">{{ scene.creator_name }}</span>
          </div>
        </div>
      </article>
    </div>

    <div v-if="total > pageSize" class="pagination">
      <button class="btn ghost" :disabled="page <= 1" @click="page--; loadScenes()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
        上一页
      </button>
      <span class="page-info muted">第 {{ page }} / {{ totalPages }} 页</span>
      <button class="btn ghost" :disabled="page >= totalPages" @click="page++; loadScenes()">
        下一页
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'

const emit = defineEmits(['view-detail'])

const scenes = ref([])
const categories = ref([])
const activeCategory = ref('')
const page = ref(1)
const pageSize = 20
const total = ref(0)

const totalPages = computed(() => Math.ceil(total.value / pageSize))

const thumbColors = [
  'hsl(0 15% 32%)', 'hsl(55 24% 49%)', 'hsl(70 10% 67%)',
  'hsl(35 25% 40%)', 'hsl(200 15% 35%)', 'hsl(120 15% 38%)',
  'hsl(290 10% 45%)', 'hsl(45 60% 50%)'
]

const thumbStyle = (scene) => {
  const idx = scene.id % thumbColors.length
  const hasThumb = scene.thumbnail_path && !scene.thumbnail_path.includes('undefined')
  if (hasThumb) {
    return { backgroundImage: `url(${scene.thumbnail_path.replace(/\\/g, '/')})` }
  }
  return { background: thumbColors[idx] }
}

const setCategory = (cat) => {
  activeCategory.value = cat
  page.value = 1
  loadScenes()
}

const loadScenes = async () => {
  try {
    const params = { page: page.value, page_size: pageSize }
    if (activeCategory.value) params.category = activeCategory.value
    const res = await axios.get('/api/scenes', { params })
    scenes.value = res.data.data
    total.value = res.data.total
  } catch (e) {
    console.error('加载素材失败:', e)
  }
}

const loadCategories = async () => {
  try {
    const res = await axios.get('/api/categories')
    categories.value = res.data
  } catch (e) {
    console.error('加载分类失败:', e)
  }
}

const formatDuration = (dur) => {
  if (!dur) return '--:--'
  const m = Math.floor(dur / 60)
  const s = Math.floor(dur % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

onMounted(() => {
  loadScenes()
  loadCategories()
})
</script>

<style scoped>
.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: calc(var(--spacing) * 3);
  flex-wrap: wrap;
}

.filter-pills {
  display: flex;
  gap: calc(var(--spacing) * 1.5);
  flex-wrap: wrap;
}

.pill {
  border: 1px solid var(--border);
  border-radius: 999px;
  background: transparent;
  color: var(--muted-foreground);
  font-family: inherit;
  letter-spacing: inherit;
  padding: calc(var(--spacing) * 1.2) calc(var(--spacing) * 2.4);
  font-size: 0.88rem;
  cursor: pointer;
  transition: background-color .18s ease, border-color .18s ease, transform .18s ease, color .18s ease;
}

.pill:hover {
  background: hsl(var(--accent) / 0.3);
  transform: translateY(-1px);
}

.pill.active {
  background: var(--primary);
  color: var(--primary-foreground);
  border-color: var(--primary);
}

.filter-right {
  display: flex;
  align-items: center;
}

.result-count {
  font-size: 0.88rem;
}

.muted {
  color: var(--muted-foreground);
}

.empty-state {
  display: grid;
  justify-items: center;
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
  text-align: center;
  max-width: 28rem;
}

.eyebrow {
  color: var(--muted-foreground);
  font-size: 0.73rem;
  text-transform: uppercase;
  letter-spacing: 0.14em;
}

.panel-title {
  margin: 0;
  font-size: 1.35rem;
  line-height: 1.08;
}

.gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: calc(var(--spacing) * 3);
}

.scene-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: calc(var(--radius) * 0.82);
  box-shadow: var(--shadow-xs);
  overflow: hidden;
  cursor: pointer;
  transition: transform .18s ease, box-shadow .18s ease;
}

.scene-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.card-thumb {
  position: relative;
  width: 100%;
  height: 160px;
  background-size: cover;
  background-position: center;
  display: flex;
  align-items: center;
  justify-content: center;
}

.thumb-overlay {
  position: absolute;
  inset: 0;
  background: rgba(59, 53, 43, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity .2s ease;
}

.scene-card:hover .thumb-overlay {
  opacity: 1;
}

.duration-badge {
  position: absolute;
  bottom: calc(var(--spacing) * 1.5);
  right: calc(var(--spacing) * 1.5);
  background: rgba(59, 53, 43, 0.8);
  color: #fbfaf9;
  padding: calc(var(--spacing) * 0.5) calc(var(--spacing) * 1.2);
  border-radius: calc(var(--radius) * 0.3);
  font-size: 0.78rem;
}

.card-body {
  padding: calc(var(--spacing) * 2.5);
  display: grid;
  gap: calc(var(--spacing) * 1.5);
}

.card-title {
  font-size: 0.95rem;
  font-weight: 500;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: calc(var(--spacing) * 0.8);
}

.tag {
  display: inline-flex;
  align-items: center;
  gap: calc(var(--spacing) * 1);
  width: fit-content;
  padding: calc(var(--spacing) * 0.6) calc(var(--spacing) * 1.4);
  border-radius: 999px;
  background: var(--muted);
  color: var(--muted-foreground);
  font-size: 0.74rem;
}

.card-meta {
  display: flex;
  gap: calc(var(--spacing) * 2);
  font-size: 0.82rem;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: calc(var(--spacing) * 3);
  padding-top: calc(var(--spacing) * 3);
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
  transition: transform .18s ease, background-color .18s ease, border-color .18s ease, opacity .18s ease;
  font-size: 0.95rem;
}

.btn:hover {
  transform: translateY(-1px);
}

.btn:active {
  transform: scale(0.98);
}

.btn:disabled {
  opacity: 0.52;
  cursor: not-allowed;
  pointer-events: none;
}

.btn.ghost {
  background: transparent;
  color: var(--accent-foreground);
  border-color: var(--border);
  box-shadow: none;
}

.page-info {
  font-size: 0.88rem;
}

@media (max-width: 1100px) {
  .gallery-grid { grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); }
}
</style>
