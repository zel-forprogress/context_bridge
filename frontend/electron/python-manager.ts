import { spawn, ChildProcess } from 'child_process'
import net from 'net'
import path from 'path'
import fs from 'fs'

let pythonProcess: ChildProcess | null = null

function findFreePort(): Promise<number> {
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

function getPythonCommand(): string {
  return process.platform === 'win32' ? 'python' : 'python3'
}

function getBackendPath(): string {
  // In development, backend is at project root /backend
  // In production, it's bundled
  const devPath = path.join(__dirname, '..', '..', 'backend', 'main.py')
  if (fs.existsSync(devPath)) {
    return devPath
  }
  return path.join(process.resourcesPath, 'backend', 'main.py')
}

async function waitForServer(port: number, timeoutMs: number): Promise<void> {
  const start = Date.now()
  while (Date.now() - start < timeoutMs) {
    try {
      const resp = await fetch(`http://127.0.0.1:${port}/api/health`)
      if (resp.ok) return
    } catch {
      // Server not ready yet
    }
    await new Promise((r) => setTimeout(r, 300))
  }
  throw new Error(`Python backend failed to start within ${timeoutMs}ms`)
}

export async function startPythonBackend(): Promise<number> {
  const port = await findFreePort()
  const pythonCmd = getPythonCommand()
  const backendPath = getBackendPath()
  const backendDir = path.dirname(backendPath)

  if (!fs.existsSync(backendPath)) {
    throw new Error(`Backend entry not found: ${backendPath}`)
  }

  // Check Python is available
  try {
    const check = spawn(pythonCmd, ['--version'], { stdio: 'pipe' })
    await new Promise<void>((resolve, reject) => {
      check.on('close', (code) => (code === 0 ? resolve() : reject(new Error('Python not found'))))
      check.on('error', reject)
    })
  } catch {
    throw new Error('Python 3.10+ is required. Please install Python and try again.')
  }

  // Install backend dependencies if needed
  const requirementsPath = path.join(backendDir, 'requirements.txt')
  if (fs.existsSync(requirementsPath)) {
    const pip = spawn(pythonCmd, ['-m', 'pip', 'install', '-r', requirementsPath, '-q'], {
      cwd: backendDir,
      stdio: 'pipe',
    })
    await new Promise<void>((resolve, reject) => {
      pip.on('close', (code) => (code === 0 ? resolve() : reject(new Error('pip install failed'))))
      pip.on('error', reject)
    })
  }

  // Start uvicorn
  pythonProcess = spawn(
    pythonCmd,
    ['-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', String(port)],
    {
      cwd: backendDir,
      stdio: ['pipe', 'pipe', 'pipe'],
    }
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

  // Wait for server to be ready
  await waitForServer(port, 15000)

  return port
}

export function stopPythonBackend() {
  if (pythonProcess) {
    pythonProcess.kill()
    pythonProcess = null
  }
}
