const { app, BrowserWindow, ipcMain, dialog } = require('electron')
const path = require('path')
const { spawn } = require('child_process')
const net = require('net')
const fs = require('fs')

let mainWindow = null
let pythonProcess = null
let backendPort = 0

function findFreePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer()
    server.listen(0, '127.0.0.1', () => {
      const addr = server.address()
      if (addr && typeof addr === 'object') {
        const port = addr.port
        server.close(() => resolve(port))
      } else {
        reject(new Error('Failed to get port'))
      }
    })
  })
}

function getPythonCommand() {
  return process.platform === 'win32' ? 'python' : 'python3'
}

function getBackendPath() {
  if (process.env.NODE_ENV === 'development') {
    return path.join(__dirname, '..', '..', 'backend', 'main.py')
  }
  return path.join(process.resourcesPath, 'backend', 'main.py')
}

function waitForServer(port, timeoutMs) {
  return new Promise((resolve, reject) => {
    const start = Date.now()
    const check = async () => {
      try {
        const resp = await fetch(`http://127.0.0.1:${port}/api/health`)
        if (resp.ok) return resolve()
      } catch {}
      if (Date.now() - start > timeoutMs) {
        return reject(new Error(`Python backend failed to start within ${timeoutMs}ms`))
      }
      setTimeout(check, 300)
    }
    check()
  })
}

async function startPythonBackend() {
  const port = await findFreePort()
  const pythonCmd = getPythonCommand()
  const backendPath = getBackendPath()
  const backendDir = path.dirname(backendPath)

  // Check Python is available
  try {
    await new Promise((resolve, reject) => {
      const check = spawn(pythonCmd, ['--version'], { stdio: 'pipe' })
      check.on('close', (code) => code === 0 ? resolve() : reject(new Error('Python not found')))
      check.on('error', reject)
    })
  } catch {
    throw new Error('Python 3.10+ is required. Please install Python and try again.')
  }

  // Install backend dependencies if needed
  const requirementsPath = path.join(backendDir, 'requirements.txt')
  if (fs.existsSync(requirementsPath)) {
    await new Promise((resolve, reject) => {
      const pip = spawn(pythonCmd, ['-m', 'pip', 'install', '-r', requirementsPath, '-q'], {
        cwd: backendDir,
        stdio: 'pipe',
      })
      pip.on('close', (code) => code === 0 ? resolve() : reject(new Error('pip install failed')))
      pip.on('error', reject)
    })
  }

  // Start uvicorn
  pythonProcess = spawn(
    pythonCmd,
    ['-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', String(port)],
    { cwd: backendDir, stdio: ['pipe', 'pipe', 'pipe'] }
  )

  pythonProcess.stderr?.on('data', (data) => {
    console.error(`[Python] ${data.toString()}`)
  })

  pythonProcess.on('error', (err) => {
    console.error('Python process error:', err)
  })

  pythonProcess.on('exit', (code) => {
    console.log(`Python process exited with code ${code}`)
    pythonProcess = null
  })

  await waitForServer(port, 15000)
  return port
}

function stopPythonBackend() {
  if (pythonProcess) {
    pythonProcess.kill()
    pythonProcess = null
  }
}

async function createWindow() {
  try {
    backendPort = await startPythonBackend()
  } catch (e) {
    await dialog.showErrorBox(
      'Python Error',
      `Failed to start Python backend: ${e.message}`
    )
    app.quit()
    return
  }

  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  ipcMain.handle('get-backend-port', () => backendPort)

  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:5173')
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'))
  }

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

app.whenReady().then(createWindow)

app.on('before-quit', () => {
  stopPythonBackend()
})

app.on('window-all-closed', () => {
  stopPythonBackend()
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow()
  }
})
