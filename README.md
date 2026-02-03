# PaperResearchPubMed
论文智能获取与总结桌面应用

## 目录结构

- backend: Python API 服务
- frontend: Vue3 前端
- desktop: Electron 宿主

## 本地开发

### 后端

1. 进入 backend 目录，安装依赖。
2. 运行 Flask 服务（默认 8000 端口）。

### 前端

1. 进入 frontend 目录，安装依赖。
2. 运行 Vite 开发服务器。

### Electron 开发

1. 构建前端产物到 desktop/renderer。
2. 启动 Electron（将使用系统 python 或环境变量 `PAPER_AGENT_PYTHON`）。

## 打包说明（生成安装包）

> 以下脚本均位于 scripts 目录，适配 Windows PowerShell。

1. 前端构建：运行 scripts/build_frontend.ps1，将产物输出到 desktop/renderer。
2. 后端运行时：运行 scripts/build_backend.ps1，将依赖安装到 desktop/backend/runtime。
3. 安装包生成：运行 scripts/build_installer.ps1，输出在 desktop/dist。

## 关键技术栈

- LangChain ReAct Agent：解析用户检索需求与决策流程
- pymed（优先） + requests + BeautifulSoup（备用）：PubMed 爬取
- python-docx / Markdown / TXT：文档导出

## 测试

1. 后端单元测试：运行 scripts/test_backend.ps1。

## 目录结构说明

- desktop/backend/runtime: 内置 Python 运行时与依赖
- desktop/renderer: 前端构建产物
