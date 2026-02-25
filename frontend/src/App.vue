<template>
  <div class="app" :class="themeClass">
    <header class="topbar">
      <div class="brand">
        <span class="brand-dot"></span>
        <span class="brand-text">PaperResearch</span>
      </div>
      <button class="settings-btn" @click="settingsVisible = true">设置</button>
    </header>

    <main class="hero">
      <div class="hero-content">
        <h1 class="hero-title">论文智能获取与总结</h1>
        <p class="hero-subtitle">
          一站式 PubMed 检索与整理，自动提取关键字与摘要，快速输出结构化文档。
        </p>

        <section class="input-section">
          <label class="section-title">检索需求</label>
          <textarea
            v-model="query"
            class="query-input"
            placeholder="2024-2026 年 糖尿病 机器学习 治疗"
            rows="4"
          ></textarea>
          <div class="input-actions">
            <div class="count-box">
              <label>数量</label>
              <input type="number" min="1" max="50" v-model.number="count" />
            </div>
            <button class="primary" @click="onCrawl" :disabled="loading">
              {{ loading ? "处理中..." : "开始爬取" }}
            </button>
            <button class="ghost" @click="clearOutput">清空输出</button>
          </div>
          <div class="hint" v-if="hint">{{ hint }}</div>
        </section>
      </div>
    </main>

    <section class="output-section">
      <div class="section-title">输出示例（前 2 篇）</div>
      <div class="cards">
        <article v-for="paper in samplePapers" :key="paper.title" class="paper-card">
          <h3 v-html="highlightText(paper.title)"></h3>
          <p class="keywords">关键字：{{ paper.keywords.join(", ") }}</p>
          <p><strong>匹配维度：</strong>{{ paper.match_dimension }}</p>
          <p><strong>发表时间：</strong>{{ paper.published_date }}</p>
          <p class="abstract" v-html="highlightText(paper.abstract)"></p>
        </article>
      </div>

      <div class="section-title">完整输出</div>
      <div class="output-box">
        <article v-for="paper in papers" :key="paper.title" class="paper-item">
          <h4 v-html="highlightText(paper.title)"></h4>
          <p class="keywords">关键字：{{ paper.keywords.join(", ") }}</p>
          <p><strong>匹配维度：</strong>{{ paper.match_dimension }}</p>
          <p><strong>发表时间：</strong>{{ paper.published_date }}</p>
          <p class="abstract" v-html="highlightText(paper.abstract)"></p>
        </article>
      </div>

      <div class="output-actions">
        <button class="primary" @click="exportDoc" :disabled="papers.length === 0">导出文档</button>
        <button class="ghost" @click="copyOutput" :disabled="papers.length === 0">复制内容</button>
      </div>
    </section>

    <div class="settings" v-if="settingsVisible">
      <div class="settings-card">
        <div class="settings-header">
          <h3>设置</h3>
          <button class="ghost" @click="settingsVisible = false">关闭</button>
        </div>
        <div class="settings-body">
          <div class="field">
            <label>AI 模型</label>
            <input v-model="config.ai_model" />
          </div>
          <div class="field">
            <label>API 地址</label>
            <input v-model="config.api_base" />
          </div>
          <div class="field">
            <label>API Key</label>
            <input v-model="config.api_key" type="password" />
          </div>
          <div class="field checkbox-field">
            <label>
              <input type="checkbox" v-model="config.auto_translate" />
              中文自动翻译（建议优先使用英文关键词以节省 tokens）
            </label>
          </div>
          <div class="field">
            <label>主题颜色</label>
            <select v-model="config.theme_color">
              <option>默认蓝</option>
              <option>浅灰</option>
              <option>深蓝</option>
            </select>
          </div>
          <div class="field">
            <label>字体大小</label>
            <select v-model="config.font_size">
              <option>小</option>
              <option>中</option>
              <option>大</option>
            </select>
          </div>
          <div class="field">
            <label>输出区背景色</label>
            <select v-model="config.output_bg">
              <option>白色</option>
              <option>浅米色</option>
            </select>
          </div>
        </div>
        <div class="settings-actions">
          <button class="ghost" @click="resetConfig">恢复默认</button>
          <button class="primary" @click="saveConfig">保存配置</button>
        </div>
      </div>
    </div>

    <div class="toast" v-if="toast">{{ toast }}</div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import axios from "axios";

const apiBaseRaw = import.meta.env.VITE_API_BASE_URL || "";
const apiBase = apiBaseRaw.replace(/\/+$/, "");
const apiUrl = (path) => `${apiBase}${path}`;

const query = ref("");
const count = ref(10);
const hint = ref("");
const loading = ref(false);
const papers = ref([]);
const extractedKeywords = ref([]);
const settingsVisible = ref(false);
const toast = ref("");

const config = reactive({
  ai_model: "gpt-3.5-turbo",
  api_base: "https://api.openai.com/v1",
  api_key: "",
  auto_translate: true,
  theme_color: "默认蓝",
  font_size: "中",
  output_bg: "白色",
});

const samplePapers = computed(() => papers.value.slice(0, 2));

const themeClass = computed(() => {
  return `theme-${config.theme_color}`;
});

const showToast = (message) => {
  toast.value = message;
  setTimeout(() => (toast.value = ""), 2400);
};

const validateInput = () => {
  if (!query.value.trim()) {
    hint.value = "请输入检索需求，例如‘2024-2026 年 糖尿病 机器学习 治疗’";
    return false;
  }
  const yearPattern = /(19\d{2}|20\d{2})\s*[-到~至]\s*(19\d{2}|20\d{2})/;
  if (/\d{4}/.test(query.value) && !yearPattern.test(query.value)) {
    hint.value = "时间范围格式有误，建议修改为‘YYYY-YYYY’";
    return false;
  }
  hint.value = "";
  return true;
};

const onCrawl = async () => {
  if (!validateInput()) {
    return;
  }
  loading.value = true;
  try {
    const { data } = await axios.post(apiUrl("/api/crawl_paper"), {
      query: query.value,
      count: count.value,
    });
    if (data.code === 0) {
      papers.value = data.data.papers || [];
      const extracted = data.data.extracted || {};
      extractedKeywords.value =
        extracted.translated_keywords || extracted.keywords || [];
      showToast("爬取完成");
    } else {
      hint.value = data.message;
      showToast(data.message);
    }
  } catch (error) {
    showToast("网络连接失败，请稍后重试");
  } finally {
    loading.value = false;
  }
};

const clearOutput = () => {
  papers.value = [];
};

const normalizePapers = () => {
  return (papers.value || []).map((paper) => ({
    title: paper.title || "",
    keywords: Array.isArray(paper.keywords) ? [...paper.keywords] : [],
    abstract: paper.abstract || "",
    match_dimension: paper.match_dimension || "",
    published_date: paper.published_date || "",
    doi: paper.doi || "",
    authors: Array.isArray(paper.authors) ? [...paper.authors] : [],
  }));
};

const exportDoc = async () => {
  try {
    const exportPapers = normalizePapers();
    if (exportPapers.length === 0) {
      showToast("没有可导出的论文数据");
      return;
    }
    const { data } = await axios.post(apiUrl("/api/export_doc"), {
      papers: exportPapers,
      format: "markdown",
    });
    if (data.code === 0) {
      showToast(`导出成功：${data.data.file_path}`);
    } else {
      showToast(data.message);
    }
  } catch (error) {
    showToast("导出失败，请稍后重试");
  }
};

const copyOutput = async () => {
  const text = normalizePapers()
    .map(
      (p, idx) =>
        `${idx + 1}. ${p.title}\n关键字：${p.keywords.join(", ")}\n匹配维度：${
          p.match_dimension
        }\n发表时间：${p.published_date}\n摘要：\n${p.abstract}`
    )
    .join("\n\n");
  await navigator.clipboard.writeText(text);
  showToast("已复制到剪贴板");
};

const escapeHtml = (value) => {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
};

const escapeRegExp = (value) => {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
};

const highlightText = (text) => {
  const safeText = escapeHtml(text);
  const keywords = (extractedKeywords.value || []).filter(Boolean);
  if (keywords.length === 0) {
    return safeText;
  }
  const pattern = keywords.map((k) => escapeRegExp(String(k))).join("|");
  if (!pattern) {
    return safeText;
  }
  const regex = new RegExp(`(${pattern})`, "gi");
  return safeText.replace(regex, '<span class="highlight">$1</span>');
};

const loadConfig = async () => {
  try {
    const { data } = await axios.get(apiUrl("/api/get_config"));
    if (data.code === 0) {
      Object.assign(config, data.data);
    }
  } catch (error) {
    // ignore
  }
};

const saveConfig = async () => {
  try {
    const { data } = await axios.post(apiUrl("/api/save_config"), config);
    if (data.code === 0) {
      showToast("配置已保存");
      settingsVisible.value = false;
    } else {
      showToast(data.message);
    }
  } catch (error) {
    showToast("保存失败，请稍后重试");
  }
};

const resetConfig = () => {
  config.ai_model = "gpt-3.5-turbo";
  config.api_base = "https://api.openai.com/v1";
  config.api_key = "";
  config.auto_translate = true;
  config.theme_color = "默认蓝";
  config.font_size = "中";
  config.output_bg = "白色";
};

onMounted(loadConfig);
</script>

<style scoped>
.app {
  font-family: "Segoe UI", "PingFang SC", sans-serif;
  color: #1f2d3d;
  min-height: 100vh;
  background: linear-gradient(180deg, #f6f7fb 0%, #ffffff 42%);
  padding: 28px 28px 48px;
  box-sizing: border-box;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  color: #25324b;
}

.brand-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ff6f91, #5f6bff);
  box-shadow: 0 6px 12px rgba(95, 107, 255, 0.3);
}

.brand-text {
  letter-spacing: 0.4px;
}

.settings-btn {
  border: none;
  background: #2b6de0;
  color: #fff;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
}

.hero {
  display: grid;
  grid-template-columns: 1fr;
  gap: 28px;
  align-items: center;
  margin-bottom: 24px;
}

.hero-title {
  font-size: 40px;
  font-weight: 700;
  margin: 0 0 12px;
  color: #1f2d3d;
}

.hero-subtitle {
  font-size: 16px;
  line-height: 1.7;
  margin-bottom: 24px;
  color: #5a6b87;
}

.input-section {
  background: #ffffff;
  padding: 20px;
  border-radius: 16px;
  box-shadow: 0 16px 32px rgba(20, 30, 60, 0.08);
}

.output-section {
  background: #ffffff;
  padding: 20px;
  border-radius: 16px;
  box-shadow: 0 16px 32px rgba(20, 30, 60, 0.06);
  margin-bottom: 20px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 12px;
}

.query-input {
  width: 100%;
  border: 1px solid #e2e6ef;
  border-radius: 12px;
  padding: 12px 14px;
  font-size: 14px;
  background: #fbfcff;
}

.input-actions {
  margin-top: 12px;
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.count-box {
  display: flex;
  align-items: center;
  gap: 8px;
}

.primary {
  background: linear-gradient(135deg, #5f6bff, #3e8cff);
  color: white;
  border: none;
  padding: 10px 18px;
  border-radius: 999px;
  cursor: pointer;
  box-shadow: 0 10px 20px rgba(63, 123, 255, 0.25);
}

.ghost {
  background: transparent;
  border: 1px solid #d6dbe6;
  color: #5b6475;
  padding: 10px 18px;
  border-radius: 999px;
  cursor: pointer;
}

.hint {
  margin-top: 8px;
  color: #d93025;
}

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.paper-card,
.paper-item {
  border: 1px solid #ebeef5;
  border-radius: 10px;
  padding: 12px;
  background: #fefefe;
}

.keywords {
  color: #2b6de0;
}

.abstract {
  color: #606266;
}

.highlight {
  background: #fff3bf;
  color: #c0392b;
  padding: 0 2px;
  border-radius: 2px;
}

.output-box {
  max-height: 320px;
  overflow-y: auto;
  background: #f7f8fc;
  padding: 12px;
  border-radius: 8px;
}

.output-actions {
  display: flex;
  gap: 12px;
  margin-top: 12px;
}

.settings {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 20;
}

.settings-card {
  width: 480px;
  background: white;
  border-radius: 16px;
  padding: 20px;
}

.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.settings-body {
  margin-top: 12px;
  display: grid;
  gap: 12px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.checkbox-field {
  flex-direction: row;
  align-items: center;
}

.settings-actions {
  margin-top: 16px;
  display: flex;
  justify-content: space-between;
}

.toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  background: #1f2d3d;
  color: white;
  padding: 10px 16px;
  border-radius: 6px;
}

.theme-浅灰 .input-section,
.theme-浅灰 .output-section {
  background: #f6f6f6;
}

.theme-深蓝 .settings-btn,
.theme-深蓝 .primary {
  background: #163c7a;
}

.theme-浅灰 .settings-btn,
.theme-浅灰 .primary {
  background: #6c757d;
}
</style>
