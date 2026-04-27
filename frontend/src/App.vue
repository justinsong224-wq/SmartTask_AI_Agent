<template>
  <div class="app-container">
    <!-- ── 顶部导航 ── -->
    <header class="app-header">
      <div class="header-left">
        <el-icon class="header-icon"><cpu-icon /></el-icon>
        <span class="header-title">SmartTask AI Agent</span>
        <el-tag :type="isOnline ? 'success' : 'danger'" size="small">
          {{ isOnline ? '在线' : '离线' }}
        </el-tag>
      </div>
      <div class="header-right">
        <el-button size="small" @click="showMemoryPanel = !showMemoryPanel">
          <el-icon><Collection /></el-icon> 记忆管理
        </el-button>
      </div>
    </header>

    <div class="main-layout">
      <!-- ── 左侧：对话区域 ── -->
      <div class="chat-panel">
        <!-- 消息列表 -->
        <div class="message-list" ref="messageListRef">
          <!-- 欢迎消息 -->
          <div v-if="messages.length === 0" class="welcome">
            <el-icon style="font-size: 48px; color: #409EFF"><Cpu /></el-icon>
            <h2>SmartTask AI Agent</h2>
            <p>支持多步骤任务执行 · 工具调用 · 记忆管理</p>
            <div class="example-tasks">
              <p>试试这些任务：</p>
              <el-tag
                v-for="task in exampleTasks"
                :key="task"
                class="example-tag"
                @click="inputText = task"
              >{{ task }}</el-tag>
            </div>
          </div>

          <!-- 消息列表 -->
          <div
            v-for="msg in messages"
            :key="msg.id"
            class="message-item"
            :class="msg.role"
          >
            <!-- 用户消息 -->
            <template v-if="msg.role === 'user'">
              <div class="message-bubble user-bubble">
                <el-icon><User /></el-icon>
                {{ msg.content }}
              </div>
            </template>

            <!-- Agent 响应 -->
            <template v-else>
              <div class="agent-response">
                <!-- 执行状态 -->
                <div v-if="msg.loading" class="loading-steps">
                  <el-icon class="rotating"><Loading /></el-icon>
                  <span>{{ msg.loadingText }}</span>
                </div>

                <!-- 执行步骤卡片（默认折叠）-->
                <div v-if="msg.executionLog && msg.executionLog.length" class="steps-card">
                 <div class="steps-header" @click="msg.showSteps = !msg.showSteps" style="cursor:pointer">
                  <el-icon><List /></el-icon>
                  执行过程（{{ msg.executionLog.length }} 步）
                  <el-icon style="margin-left:auto">
                    <ArrowDown v-if="!msg.showSteps" />
                    <ArrowUp v-else />
                  </el-icon>
                 </div>
                 <template v-if="msg.showSteps">
                  <div
                    v-for="step in msg.executionLog"
                    :key="step.step_id"
                    class="step-item"
                    :class="{ 'step-failed': !step.success }"
                  >
                    <div class="step-header">
                      <el-tag size="small" :type="step.success ? 'success' : 'danger'">
                        步骤 {{ step.step_id }}
                      </el-tag>
                      <el-tag v-if="step.tool_used" size="small" type="warning">
                        🔧 {{ step.tool_used }}
                      </el-tag>
                      <span class="step-desc">{{ step.description }}</span>
                    </div>
                    <div class="step-conclusion">{{ step.conclusion }}</div>
                  </div>
                 </template>
                </div>
                <!-- 最终报告 -->
                <div v-if="msg.finalReport" class="final-report">
                  <div class="report-header">
                    <el-icon><Document /></el-icon> 最终报告
                  </div>
                  <div class="report-content" v-html="renderMarkdown(msg.finalReport)"></div>
                </div>

                <!-- 记忆决策 -->
                <div v-if="msg.memoryDecision" class="memory-badge">
                  <el-icon><Coin /></el-icon>
                  <span v-if="msg.memoryDecision.should_save">
                    已存入长期记忆
                    <el-tag size="small" type="success">
                      {{ msg.memoryDecision.importance }}
                    </el-tag>
                  </span>
                  <span v-else class="memory-skip">未存入记忆：{{ msg.memoryDecision.reason }}</span>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="input-area">
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="3"
            placeholder="输入任务，例如：搜索今天的比特币价格并分析趋势..."
            :disabled="isLoading"
            @keydown.ctrl.enter="sendTask"
          />
          <div class="input-footer">
            <span class="input-hint">Ctrl + Enter 发送</span>
            <div class="input-actions">
              <el-input
                v-model="sessionId"
                placeholder="会话ID"
                size="small"
                style="width: 120px; margin-right: 8px"
              />
              <el-button
                type="primary"
                :loading="isLoading"
                @click="sendTask"
                :disabled="!inputText.trim()"
              >
                <el-icon><Position /></el-icon>
                {{ isLoading ? '执行中...' : '发送任务' }}
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- ── 右侧：记忆管理面板 ── -->
      <div class="memory-panel" v-show="showMemoryPanel">
        <div class="panel-header">
          <span>记忆管理</span>
          <el-button size="small" text @click="showMemoryPanel = false">✕</el-button>
        </div>

        <!-- 统计 -->
        <div class="memory-stats">
          <div class="stat-item">
            <div class="stat-value">{{ memoryStats.total_records || 0 }}</div>
            <div class="stat-label">长期记忆</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ sessionCount }}</div>
            <div class="stat-label">活跃会话</div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="memory-actions">
          <el-button size="small" @click="loadMemoryStats">
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
          <el-popconfirm
            title="确认清空所有长期记忆？"
            @confirm="clearLongTermMemory"
          >
            <template #reference>
              <el-button size="small" type="danger">
                <el-icon><Delete /></el-icon> 清空长期记忆
              </el-button>
            </template>
          </el-popconfirm>
        </div>

        <!-- 记忆列表 -->
        <div class="memory-list">
          <div class="memory-list-header">最近记忆</div>
          <div
            v-for="record in memoryRecords"
            :key="record.id"
            class="memory-record"
          >
            <div class="record-task">{{ record.task }}</div>
            <div class="record-meta">
              <el-tag size="small">{{ record.session_id }}</el-tag>
              <span class="record-time">{{ record.created_at }}</span>
            </div>
          </div>
          <el-empty v-if="memoryRecords.length === 0" description="暂无记忆" :image-size="60" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { agentApi } from './api/agent.js'

// ── 状态 ────────────────────────────────────────────
const inputText      = ref('')
const sessionId      = ref('session-' + Date.now())
const isLoading      = ref(false)
const isOnline       = ref(false)
const showMemoryPanel = ref(false)
const messages       = ref([])
const messageListRef = ref(null)
const memoryStats    = ref({})
const memoryRecords  = ref([])
const sessionCount   = ref(0)

const exampleTasks = [
  '搜索今天比特币价格',
  '计算 2的32次方',
  '搜索最新的 AI 新闻',
  '查询今天多伦多天气',
]

let msgIdCounter = 0

// ── 发送任务 ─────────────────────────────────────────
async function sendTask() {
  const task = inputText.value.trim()
  if (!task || isLoading.value) return

  // 添加用户消息
  messages.value.push({
    id:      ++msgIdCounter,
    role:    'user',
    content: task,
  })

  // 添加 Agent 占位消息
  const agentMsg = {
    id:           ++msgIdCounter,
    role:         'agent',
    loading:      true,
    loadingText:  '🧠 规划任务中...',
    executionLog: [],
    finalReport:  '',
    memoryDecision: null,
    showSteps:    false,
  }
  messages.value.push(agentMsg)

  inputText.value = ''
  isLoading.value = true
  scrollToBottom()

  try {
    // 模拟加载状态文字变化
    const loadingTexts = [
      '🧠 规划任务中...',
      '⚙️ 执行步骤中...',
      '🔧 调用工具中...',
      '📝 生成报告中...',
    ]
    let textIndex = 0
    const textTimer = setInterval(() => {
      textIndex = (textIndex + 1) % loadingTexts.length
      agentMsg.loadingText = loadingTexts[textIndex]
    }, 2000)

    const response = await agentApi.runTask(task, sessionId.value)
    clearInterval(textTimer)

    const data = response.data.data

    // 更新 Agent 消息
    agentMsg.loading        = false
    agentMsg.executionLog   = data.execution_log   || []
    agentMsg.finalReport    = data.final_report    || ''
    agentMsg.memoryDecision = data.memory_decision || null

    scrollToBottom()

    // 刷新记忆统计
    if (showMemoryPanel.value) loadMemoryStats()

  } catch (error) {
    agentMsg.loading     = false
    agentMsg.finalReport = `❌ 执行失败：${error.response?.data?.detail || error.message}`
    ElMessage.error('任务执行失败')
  } finally {
    isLoading.value = false
  }
}

// ── 记忆管理 ─────────────────────────────────────────
async function loadMemoryStats() {
  try {
    const [statsRes, listRes] = await Promise.all([
      agentApi.getMemoryStats(),
      agentApi.getLongTermMemory(10),
    ])
    memoryStats.value   = statsRes.data
    memoryRecords.value = listRes.data.records || []
  } catch (e) {
    console.error('加载记忆失败', e)
  }
}

async function clearLongTermMemory() {
  await agentApi.clearLongTermMemory()
  ElMessage.success('长期记忆已清空')
  loadMemoryStats()
}

// ── 工具函数 ─────────────────────────────────────────
function renderMarkdown(text) {
  // 简单 Markdown 渲染（不引入额外库）
  return text
    .replace(/## (.*)/g, '<h3>$1</h3>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
}

async function scrollToBottom() {
  await nextTick()
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}

async function checkOnline() {
  try {
    await agentApi.healthCheck()
    isOnline.value = true
  } catch {
    isOnline.value = false
  }
}

onMounted(() => {
  checkOnline()
})
</script>

<style scoped>
/* ── 整体布局 ── */
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}

.header-left { display: flex; align-items: center; gap: 10px; }
.header-icon { font-size: 22px; color: #409EFF; }
.header-title { font-size: 16px; font-weight: 600; color: #303133; }

.main-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* ── 对话面板 ── */
.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ── 欢迎页 ── */
.welcome {
  text-align: center;
  margin: auto;
  padding: 40px;
  color: #909399;
}
.welcome h2 { color: #303133; margin: 16px 0 8px; }
.example-tasks { margin-top: 20px; }
.example-tag {
  margin: 4px;
  cursor: pointer;
  transition: all 0.2s;
}
.example-tag:hover { transform: translateY(-1px); }

/* ── 消息气泡 ── */
.message-item { display: flex; flex-direction: column; }
.message-item.user { align-items: flex-end; }
.message-item.agent { align-items: flex-start; }

.user-bubble {
  background: #409EFF;
  color: white;
  padding: 10px 16px;
  border-radius: 18px 18px 4px 18px;
  max-width: 70%;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ── Agent 响应 ── */
.agent-response {
  max-width: 85%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.loading-steps {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #409EFF;
  padding: 12px 16px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.08);
}

.rotating { animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* ── 执行步骤卡片 ── */
.steps-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.08);
  overflow: hidden;
}

.steps-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  background: #f5f7fa;
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  border-bottom: 1px solid #e4e7ed;
}

.step-item {
  padding: 10px 16px;
  border-bottom: 1px solid #f5f7fa;
}
.step-item:last-child { border-bottom: none; }
.step-failed { background: #fff5f5; }

.step-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}

.step-desc { font-size: 13px; color: #303133; }
.step-conclusion { font-size: 12px; color: #606266; margin-top: 4px; }

/* ── 最终报告 ── */
.final-report {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.08);
  overflow: hidden;
}

.report-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  background: #f0f9ff;
  font-size: 13px;
  font-weight: 600;
  color: #409EFF;
  border-bottom: 1px solid #e4e7ed;
}

.report-content {
  padding: 16px;
  font-size: 14px;
  line-height: 1.8;
  color: #303133;
}

.report-content :deep(h3) {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin: 12px 0 6px;
}

/* ── 记忆标记 ── */
.memory-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #909399;
  padding: 4px 8px;
}
.memory-skip { color: #C0C4CC; }

/* ── 输入区域 ── */
.input-area {
  padding: 16px 20px;
  background: white;
  border-top: 1px solid #e4e7ed;
}

.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.input-hint { font-size: 12px; color: #C0C4CC; }
.input-actions { display: flex; align-items: center; }

/* ── 记忆面板 ── */
.memory-panel {
  width: 300px;
  background: white;
  border-left: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  font-weight: 600;
  border-bottom: 1px solid #e4e7ed;
}

.memory-stats {
  display: flex;
  padding: 16px;
  gap: 16px;
  border-bottom: 1px solid #f5f7fa;
}

.stat-item { text-align: center; flex: 1; }
.stat-value { font-size: 24px; font-weight: 700; color: #409EFF; }
.stat-label { font-size: 12px; color: #909399; margin-top: 2px; }

.memory-actions {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid #f5f7fa;
}

.memory-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.memory-list-header {
  font-size: 12px;
  color: #909399;
  padding: 8px;
  font-weight: 600;
}

.memory-record {
  padding: 10px;
  border-radius: 8px;
  margin-bottom: 6px;
  background: #f5f7fa;
}

.record-task {
  font-size: 13px;
  color: #303133;
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.record-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.record-time { font-size: 11px; color: #C0C4CC; }
</style>