import { initTheme } from './vendor/ddlc-theme.js'
import { startCloud } from './vendor/ddlc-cloud.js'

const cloud = startCloud(document.getElementById('cloud'))

initTheme({
  button: document.getElementById('theme'),
  icon: document.getElementById('theme-icon'),
  key: 'app:theme',
  // a canvas reads its colours again whenever the side shown changes
  onChange: () => cloud.recolor(),
})
