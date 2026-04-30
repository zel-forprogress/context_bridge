import { app, BrowserWindow, ipcMain, dialog } from 'electron'
import path from 'path'
import { startPythonBackend, stopPythonBackend } from './python-manager'

let mainWindow: BrowserWindow | null = null
let backendPort = 0

async function createWindow() {
  try {
    backendPort = await startPythonBackend()
  } catch (e) {
    await dialog.showErrorBox(
      'Python Error',
      `Failed to start Python backend: ${e instanceof Error ? e.message : e}`
    )
    app.quit()
    return
  }

  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
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
