const { app, BrowserWindow } = require("electron");
const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");

let mainWindow;
let backendProcess;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1100,
    height: 760,
    webPreferences: {
      contextIsolation: true,
      preload: path.join(__dirname, "preload.js"),
    },
  });

  let rendererPath = path.join(__dirname, "renderer", "index.html");
  if (app.isPackaged) {
    const asarPath = path.join(app.getAppPath(), "renderer", "index.html");
    const resourcesPath = path.join(process.resourcesPath, "renderer", "index.html");
    rendererPath = fs.existsSync(asarPath) ? asarPath : resourcesPath;
  }
  mainWindow.loadFile(rendererPath);
}

function resolveBackendPaths() {
  if (app.isPackaged) {
    const backendDir = path.join(process.resourcesPath, "backend");
    return {
      backendDir,
      pythonPath: path.join(backendDir, "runtime", "Scripts", "python.exe"),
      scriptPath: path.join(backendDir, "run_flask.py"),
    };
  }
  const backendDir = path.join(__dirname, "..", "backend");
  return {
    backendDir,
    pythonPath: process.env.PAPER_AGENT_PYTHON || "python",
    scriptPath: path.join(backendDir, "run_flask.py"),
  };
}

function startBackend() {
  const { backendDir, pythonPath, scriptPath } = resolveBackendPaths();
  const logPath = path.join(app.getPath("userData"), "backend.log");
  const logStream = fs.createWriteStream(logPath, { flags: "a" });
  const dataDir = path.join(app.getPath("userData"), "data");
  backendProcess = spawn(pythonPath, [scriptPath], {
    cwd: backendDir,
    env: {
      ...process.env,
      PAPER_AGENT_DATA_DIR: dataDir,
      PYTHONNOUSERSITE: "1",
    },
    stdio: ["ignore", "pipe", "pipe"],
  });
  backendProcess.stdout.on("data", (data) => logStream.write(data));
  backendProcess.stderr.on("data", (data) => logStream.write(data));
}

app.whenReady().then(() => {
  startBackend();
  createWindow();
});

app.on("window-all-closed", () => {
  if (backendProcess) {
    backendProcess.kill();
  }
  if (process.platform !== "darwin") {
    app.quit();
  }
});
