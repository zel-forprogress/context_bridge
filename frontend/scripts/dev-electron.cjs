const { spawn } = require('child_process')
const path = require('path')

const rootDir = path.resolve(__dirname, '..')

let viteServer = null
let electronProcess = null
let shuttingDown = false

function getElectronSpawn() {
  const electronCommand = process.platform === 'win32'
    ? path.join(rootDir, 'node_modules', '.bin', 'electron.cmd')
    : path.join(rootDir, 'node_modules', '.bin', 'electron')

  if (process.platform === 'win32') {
    return {
      command: process.env.ComSpec || 'cmd.exe',
      args: ['/d', '/s', '/c', electronCommand, '.'],
    }
  }

  return {
    command: electronCommand,
    args: ['.'],
  }
}

function getPreferredPort() {
  const raw = process.env.VITE_PORT
  if (!raw) return 0
  const parsed = Number(raw)
  return Number.isInteger(parsed) && parsed > 0 ? parsed : 0
}

async function shutdown(code = 0) {
  if (shuttingDown) return
  shuttingDown = true

  if (electronProcess && !electronProcess.killed) {
    electronProcess.kill()
  }

  if (viteServer) {
    await viteServer.close()
  }

  process.exit(code)
}

async function main() {
  const { createServer } = await import('vite')

  viteServer = await createServer({
    root: rootDir,
    configFile: path.join(rootDir, 'vite.config.ts'),
    server: {
      host: '127.0.0.1',
      port: getPreferredPort(),
      strictPort: false,
    },
  })

  await viteServer.listen()
  viteServer.printUrls()

  const localUrls = viteServer.resolvedUrls?.local || []
  const devServerUrl =
    localUrls.find((url) => url.startsWith('http://127.0.0.1')) ||
    localUrls[0]

  if (!devServerUrl) {
    throw new Error('Failed to resolve Vite dev server URL')
  }

  const electronSpawn = getElectronSpawn()

  electronProcess = spawn(electronSpawn.command, electronSpawn.args, {
    cwd: rootDir,
    stdio: 'inherit',
    env: {
      ...process.env,
      CONTEXT_BRIDGE_DEV_SERVER_URL: devServerUrl,
    },
  })

  electronProcess.on('exit', (code) => {
    shutdown(code ?? 0)
  })

  electronProcess.on('error', (err) => {
    console.error(err)
    shutdown(1)
  })
}

process.on('SIGINT', () => shutdown(0))
process.on('SIGTERM', () => shutdown(0))

main().catch((err) => {
  console.error(err)
  shutdown(1)
})
