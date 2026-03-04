const { contextBridge, shell } = require('electron')

// Expose bridge API URL to renderer
contextBridge.exposeInMainWorld('BRIDGE', {
  url: 'http://127.0.0.1:47325',
})

// Expose shell.openExternal so renderer can open download URLs in the browser
contextBridge.exposeInMainWorld('electronAPI', {
  openExternal: (url) => shell.openExternal(url),
})
