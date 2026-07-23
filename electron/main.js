const { app, BrowserWindow, dialog } = require('electron')
const { exec, spawn } = require('node:child_process')
const http = require('node:http')
const path = require('node:path')
const { pathToFileURL } = require('node:url')

const repositoryRoot = path.join(__dirname, '..')
const healthUrl = 'http://127.0.0.1:8000/health'
const startupTimeoutMs = 15_000
const pollIntervalMs = 300
const shutdownTimeoutMs = 2_000

let backendProcess = null
let backendExitPromise = Promise.resolve()
let quitting = false
let backendStopped = false

function startBackend() {
  backendProcess = spawn(
    'uv',
    ['run', 'uvicorn', 'backend.main:app', '--port', '8000'],
    {
      cwd: repositoryRoot,
      stdio: 'inherit',
      // Improve PATH and executable-extension resolution for uv on Windows.
      shell: process.platform === 'win32',
    },
  )

  backendExitPromise = new Promise((resolve) => {
    backendProcess.once('exit', (code, signal) => {
      backendStopped = true
      backendProcess = null
      resolve({ code, signal })
    })
  })

  backendProcess.once('error', (error) => {
    console.error('Failed to start backend:', error)
  })
}

function checkHealth() {
  return new Promise((resolve) => {
    const request = http.get(healthUrl, (response) => {
      response.resume()
      resolve(response.statusCode === 200)
    })

    request.setTimeout(1_000, () => {
      request.destroy()
      resolve(false)
    })
    request.on('error', () => resolve(false))
  })
}

async function waitForBackend() {
  const deadline = Date.now() + startupTimeoutMs

  while (Date.now() < deadline) {
    if (await checkHealth()) return true
    if (backendStopped) return false
    await new Promise((resolve) => setTimeout(resolve, pollIntervalMs))
  }

  return false
}

async function stopBackend() {
  if (!backendProcess || backendStopped) return

  const processToStop = backendProcess
  if (process.platform === 'win32') {
    await new Promise((resolve) => {
      exec(`taskkill /PID ${processToStop.pid} /T /F`, (error) => {
        if (error) {
          console.error('Failed to stop backend process tree:', error)
        }
        resolve()
      })
    })
    await backendExitPromise
  } else {
    processToStop.kill('SIGTERM')

    const exitedGracefully = await Promise.race([
      backendExitPromise.then(() => true),
      new Promise((resolve) =>
        setTimeout(() => resolve(false), shutdownTimeoutMs),
      ),
    ])

    if (!exitedGracefully && processToStop.exitCode === null) {
      processToStop.kill('SIGKILL')
      await backendExitPromise
    }
  }
}

async function createWindow() {
  const window = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  window.webContents.session.webRequest.onHeadersReceived(
    { urls: ['http://127.0.0.1:8000/*'] },
    (details, callback) => {
      callback({
        responseHeaders: {
          ...details.responseHeaders,
          'Access-Control-Allow-Origin': ['*'],
        },
      })
    },
  )

  window.webContents.session.webRequest.onBeforeRequest(
    { urls: ['file:///assets/*'] },
    (details, callback) => {
      const assetName = path.basename(new URL(details.url).pathname)
      callback({
        redirectURL: pathToFileURL(
          path.join(repositoryRoot, 'frontend', 'dist', 'assets', assetName),
        ).href,
      })
    },
  )

  await window.loadFile(
    path.join(repositoryRoot, 'frontend', 'dist', 'index.html'),
  )
}

app.whenReady().then(async () => {
  startBackend()

  if (!(await waitForBackend())) {
    dialog.showErrorBox(
      'Backend failed to start',
      'The drawing inspection service did not become healthy within 15 seconds.',
    )
    app.quit()
    return
  }

  try {
    await createWindow()
  } catch (error) {
    dialog.showErrorBox(
      'Frontend failed to load',
      `Build the frontend before starting Electron.\n\n${error.message}`,
    )
    app.quit()
  }
})

app.on('window-all-closed', () => {
  app.quit()
})

app.on('before-quit', (event) => {
  if (quitting) return

  event.preventDefault()
  quitting = true
  stopBackend()
    .catch((error) => console.error('Failed to stop backend:', error))
    .finally(() => app.exit(0))
})
