# PaperResearchPubMed
论文智能获取与总结桌面应用

## 目录结构

- backend: Python API 服务
- frontend: Vue3 前端
- desktop: Electron 宿主

## 本地开发

### 后端

1. 确保本机已安装 Python（推荐 3.9+），并已加入 PATH。
2. 在 backend 目录创建虚拟环境并安装依赖（requirements.txt）。
3. 运行 Flask 服务（默认 8000 端口）。

### 前端

1. 进入 frontend 目录，安装依赖。
2. 运行 Vite 开发服务器。

### Electron 开发

1. 构建前端产物到 desktop/renderer。
2. 启动 Electron（将使用系统 Python，或通过环境变量 `PAPER_AGENT_PYTHON` 指定 Python 路径）。

## 打包说明（生成安装包）

> 以下脚本均位于 scripts 目录，适配 Windows PowerShell。

1. 前端构建：运行 scripts/build_frontend.ps1，将产物输出到 desktop/renderer。
2. 后端依赖：运行 scripts/build_backend.ps1，在本机 Python 环境下安装依赖（无需硬编码路径）。
3. 安装包生成：运行 scripts/build_installer.ps1，输出在 desktop/dist。

> 说明：当前打包默认不内置 Python 运行时，目标用户需自行准备 Python 环境或在运行时通过 `PAPER_AGENT_PYTHON` 指定。

### 后端打包环境配置（必读）

1. 安装 Python 3.9+（建议 3.10），并确保 `python` 与 `pip` 可在终端直接使用。
2. 如需指定 Python 路径，设置环境变量 `PAPER_AGENT_PYTHON` 为完整解释器路径。
3. 运行 scripts/build_backend.ps1，会基于当前 Python 创建 runtime 并安装依赖。
4. 如果下载源码后第一次打包较慢，这是依赖安装阶段，属正常情况。

## Docker 容器化部署（推荐）

适用于在任意电脑上快速部署前后端服务。

### 环境要求

1. 安装 Docker 与 Docker Compose。
2. 可访问外网（用于拉取镜像与访问 PubMed）。

### 部署流程（从 git clone 开始）

1. 克隆代码并进入目录：

	```bash
	git clone https://github.com/KaiNYuL/PaperResearchPubMed.git
	cd PaperResearchPubMed
	```

2. 构建并启动容器：

	```bash
	docker compose up -d --build
	```

3. 访问服务：

	- 前端：`http://<服务器IP>:5173`
	- 后端：`http://<服务器IP>:8000`
	- 后端文档：`http://<服务器IP>:8000/docs`

4. 首次使用需在前端右上角“设置”中填写 `API 地址` 与 `API Key`，保存后即可使用大模型能力。

### 常见问题

- 若前端请求超时，可等待更长时间或减小检索数量。
- 若爬取结果为空，请确认容器可访问外网，且模型配置已保存成功。
- 若需要在内网使用，请为 Docker 配置代理或内网镜像源。

## 自助部署（给有工程能力的用户）

1. 安装 Node.js（用于前端与 Electron）。
2. 安装 Python 3.9+ 并加入 PATH。
3. 后端：进入 backend 目录，创建虚拟环境并安装 requirements.txt。
4. 前端：进入 frontend 目录，安装依赖并构建产物到 desktop/renderer。
5. Electron：进入 desktop 目录，安装依赖后启动或打包。

> 可选：设置环境变量 `PAPER_AGENT_PYTHON`，显式指定后端使用的 Python 解释器路径。

## 关键技术栈

- LangChain ReAct Agent：解析用户检索需求与决策流程
- pymed（优先） + requests + BeautifulSoup（备用）：PubMed 爬取
- python-docx / Markdown / TXT：文档导出

## 测试

1. 后端单元测试：运行 scripts/test_backend.ps1。

## 目录结构说明

- desktop/backend/runtime: 内置 Python 运行时与依赖
- desktop/renderer: 前端构建产物
