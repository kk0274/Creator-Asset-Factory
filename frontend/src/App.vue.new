<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand-lockup">
        <span class="brand-kicker">素材管理系统</span>
        <div class="brand-name">视频素材管理</div>
        <div class="workspace-note">达人视频素材拆分与分类，智能镜头分割与 AI 标注。</div>
      </div>

      <div class="nav-group">
        <div class="nav-label">工作区</div>
        <button
          class="nav-item"
          :class="{ active: activeTab === 'upload' }"
          @click="activeTab = 'upload'"
        >
          <span class="nav-copy">
            <span class="nav-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
            </span>
            <span>视频上传</span>
          </span>
          <span class="nav-meta">上传</span>
        </button>
        <button
          class="nav-item"
          :class="{ active: activeTab === 'browse' }"
          @click="activeTab = 'browse'"
        >
          <span class="nav-copy">
            <span class="nav-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
            </span>
            <span>素材浏览</span>
          </span>
          <span class="nav-meta">浏览</span>
        </button>
      </div>

      <div class="sidebar-footer">
        <span class="eyebrow">当前工作区</span>
        <strong>达人视频素材库</strong>
        <span class="muted">上传视频后自动拆分镜头，AI 智能分类标注。</span>
      </div>
    </aside>

    <main class="main-area">
      <header class="topbar">
        <div class="topbar-copy">
          <h1 class="page-title">{{ activeTab === 'upload' ? '视频上传' : '素材浏览' }}</h1>
          <div class="page-subtitle">{{ activeTab === 'upload' ? '上传达人视频，自动拆分镜头并智能分类标注' : '浏览已处理的视频素材，按分类筛选和管理' }}</div>
        </div>
        <div class="topbar-actions">
          <label class="field-wrap" aria-label="搜索">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input class="field" type="text" placeholder="搜索素材..." />
          </label>
        </div>
      </header>

      <div class="view-frame" :key="activeTab">
        <UploadPanel v-if="activeTab === 'upload'" />
        <BrowsePanel v-else-if="activeTab === 'browse'" @view-detail="showDetail" />
      </div>
    </main>

    <Teleport to="body">
      <div v-if="detailVisible" class="detail-overlay" @click.self="detailVisible = false">
        <SceneDetail :scene="selectedScene" @close="detailVisible = false" />
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import UploadPanel from './components/UploadPanel.vue'
import BrowsePanel from './components/BrowsePanel.vue'
import SceneDetail from './components/SceneDetail.vue'

const activeTab = ref('upload')
const detailVisible = ref(false)
const selectedScene = ref(null)

const showDetail = (scene) => {
  selectedScene.value = scene
  detailVisible.value = true
}
</script>

<style scoped>
.app-shell {
  display: grid;
  grid-template-columns: 280px 1fr;
  min-height: 100vh;
  background: var(--background);
}

.sidebar {
  background: var(--sidebar);
  color: var(--sidebar-foreground);
  border-right: 1px solid var(--sidebar-border);
  padding: calc(var(--spacing) * 6);
  display: flex;
  flex-direction: column;
  gap: calc(var(--spacing) * 5);
}

.brand-lockup {
  display: grid;
  gap: calc(var(--spacing) * 1.3);
  padding-bottom: calc(var(--spacing) * 2);
  border-bottom: 1px solid var(--sidebar-border);
}

.brand-kicker {
  color: var(--muted-foreground);
  font-size: 0.76rem;
  text-transform: uppercase;
  letter-spacing: 0.14em;
}

.brand-name {
  font-size: 1.65rem;
  line-height: 1;
}

.workspace-note {
  color: var(--muted-foreground);
  font-size: 0.95rem;
  max-width: 18rem;
  line-height: 1.5;
}

.nav-group {
  display: grid;
  gap: calc(var(--spacing) * 1.5);
}

.nav-label {
  color: var(--muted-foreground);
  font-size: 0.74rem;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  padding-left: calc(var(--spacing) * 1.5);
}

.nav-item {
  width: 100%;
  border: 1px solid transparent;
  border-radius: calc(var(--radius) * 0.72);
  background: transparent;
  color: inherit;
  font-family: inherit;
  letter-spacing: inherit;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: calc(var(--spacing) * 2);
  padding: calc(var(--spacing) * 2.3) calc(var(--spacing) * 2.8);
  text-align: left;
  cursor: pointer;
  transition: background-color .18s ease, border-color .18s ease, transform .18s ease;
}

.nav-item:hover {
  background: hsl(var(--sidebar-accent) / 0.42);
  color: var(--sidebar-accent-foreground);
  transform: translateY(-1px);
}

.nav-item:focus-visible {
  outline: 2px solid var(--ring);
  outline-offset: 2px;
}

.nav-item.active {
  background: var(--sidebar-primary);
  color: var(--sidebar-primary-foreground);
}

.nav-copy {
  display: flex;
  align-items: center;
  gap: calc(var(--spacing) * 2);
  min-width: 0;
}

.nav-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.85rem;
  height: 1.85rem;
  border-radius: 999px;
  background: hsl(var(--accent) / 0.22);
  color: inherit;
  font-size: 0.95rem;
  flex: 0 0 auto;
}

.nav-item.active .nav-icon {
  background: hsl(var(--sidebar-primary-foreground) / 0.16);
}

.nav-meta {
  color: var(--muted-foreground);
  font-size: 0.8rem;
  white-space: nowrap;
}

.nav-item.active .nav-meta {
  color: inherit;
  opacity: 0.82;
}

.sidebar-footer {
  margin-top: auto;
  padding: calc(var(--spacing) * 3);
  border: 1px solid var(--sidebar-border);
  border-radius: calc(var(--radius) * 0.82);
  display: grid;
  gap: calc(var(--spacing) * 1.1);
  background: var(--card);
}

.eyebrow {
  color: var(--muted-foreground);
  font-size: 0.73rem;
  text-transform: uppercase;
  letter-spacing: 0.14em;
}

.muted {
  color: var(--muted-foreground);
  font-size: 0.88rem;
  line-height: 1.5;
}

.main-area {
  display: grid;
  grid-template-rows: auto 1fr;
  min-width: 0;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: calc(var(--spacing) * 3);
  padding: calc(var(--spacing) * 5) calc(var(--spacing) * 6);
  border-bottom: 1px solid var(--border);
  background: hsl(var(--background) / 0.94);
  position: sticky;
  top: 0;
  z-index: 1;
}

.topbar-copy {
  display: grid;
  gap: calc(var(--spacing) * 1);
}

.page-title {
  margin: 0;
  font-size: 2rem;
  line-height: 1;
}

.page-subtitle {
  color: var(--muted-foreground);
  max-width: 38rem;
  font-size: 0.98rem;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: calc(var(--spacing) * 2);
}

.field-wrap {
  display: flex;
  align-items: center;
  gap: calc(var(--spacing) * 2);
  min-width: 16rem;
  padding: 0 calc(var(--spacing) * 2.6);
  background: var(--card);
  border: 1px solid var(--input);
  border-radius: calc(var(--radius) * 0.76);
  box-shadow: var(--shadow-xs);
  color: var(--muted-foreground);
}

.field {
  width: 100%;
  min-height: 2.8rem;
  border: 0;
  background: transparent;
  color: var(--foreground);
  font-family: inherit;
  font-size: 0.95rem;
  letter-spacing: inherit;
}

.field::placeholder {
  color: var(--muted-foreground);
}

.view-frame {
  padding: calc(var(--spacing) * 5) calc(var(--spacing) * 6) calc(var(--spacing) * 7);
  display: grid;
  gap: calc(var(--spacing) * 4);
  animation: viewIn .28s ease;
  overflow-y: auto;
}

@keyframes viewIn {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.detail-overlay {
  position: fixed;
  inset: 0;
  background: rgba(59, 53, 43, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  backdrop-filter: blur(4px);
}

@media (max-width: 1100px) {
  .app-shell { grid-template-columns: 1fr; }
  .sidebar { border-right: 0; border-bottom: 1px solid var(--sidebar-border); }
}
</style>
