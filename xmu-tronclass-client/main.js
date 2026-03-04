const { app, BrowserWindow, ipcMain, shell } = require('electron')
const { spawn } = require('child_process')
const path = require('path')
const http = require('http')

const BRIDGE_PORT = 47325
let mainWindow = null
let bridgeProcess = null

// ── Spawn Python bridge ───────────────────────────────────────────────────────

function spawnBridge() {
  const serverPath = path.join(__dirname, 'bridge', 'server.py')
  bridgeProcess = spawn('python3', [serverPath], {
    env: { ...process.env, BRIDGE_PORT: String(BRIDGE_PORT) },
    stdio: ['ignore', 'pipe', 'pipe'],
  })

  bridgeProcess.stdout.on('data', d => console.log('[bridge]', d.toString().trim()))
  bridgeProcess.stderr.on('data', d => console.error('[bridge:err]', d.toString().trim()))
  bridgeProcess.on('exit', code => console.log(`[bridge] exited: ${code}`))
}

function waitForBridge(retries = 30) {
  return new Promise((resolve, reject) => {
    const check = (n) => {
      const req = http.get(`http://127.0.0.1:${BRIDGE_PORT}/health`, res => {
        resolve()
      })
      req.on('error', () => {
        if (n <= 0) return reject(new Error('Bridge failed to start'))
        setTimeout(() => check(n - 1), 500)
      })
      req.end()
    }
    check(retries)
  })
}

// ── Window ────────────────────────────────────────────────────────────────────

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 400,
    height: 780,
    minWidth: 360,
    minHeight: 600,
    titleBarStyle: 'hiddenInset',
    trafficLightPosition: { x: 12, y: 12 },
    backgroundColor: '#ffffff',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'))
  mainWindow.on('closed', () => { mainWindow = null })

  // Open window.open() links in the system browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url)
    return { action: 'deny' }
  })
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────

app.whenReady().then(async () => {
  spawnBridge()
  try {
    await waitForBridge()
    console.log('[main] Bridge ready')
  } catch (e) {
    console.error('[main] Bridge did not start:', e.message)
  }
  createWindow()
})

app.on('window-all-closed', () => {
  if (bridgeProcess) bridgeProcess.kill()
  if (process.platform !== 'darwin') app.quit()
})

app.on('activate', () => {
  if (mainWindow === null) createWindow()
})

app.on('before-quit', () => {
  if (bridgeProcess) bridgeProcess.kill()
})
