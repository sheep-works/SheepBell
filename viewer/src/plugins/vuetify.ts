import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import { createVuetify, type ThemeDefinition } from 'vuetify'

const customDarkTheme: ThemeDefinition = {
  dark: true,
  colors: {
    background: '#0f172a',
    surface: '#1e293b',
    'surface-bright': '#334155',
    'surface-light': '#475569',
    'surface-variant': '#1e293b',
    primary: '#14b8a6',
    'primary-darken-1': '#0d9488',
    secondary: '#2dd4bf',
    'secondary-darken-1': '#0f766e',
    error: '#f43f5e',
    info: '#38bdf8',
    success: '#10b981',
    warning: '#f59e0b',
  },
}

const customLightTheme: ThemeDefinition = {
  dark: false,
  colors: {
    background: '#f8fafc',
    surface: '#ffffff',
    'surface-bright': '#ffffff',
    'surface-light': '#f1f5f9',
    'surface-variant': '#e2e8f0',
    primary: '#0d9488',
    'primary-darken-1': '#0f766e',
    secondary: '#14b8a6',
    'secondary-darken-1': '#115e59',
    error: '#e11d48',
    info: '#0284c7',
    success: '#059669',
    warning: '#d97706',
  },
}

export default createVuetify({
  theme: {
    defaultTheme: 'dark',
    themes: {
      dark: customDarkTheme,
      light: customLightTheme,
    },
  },
})
