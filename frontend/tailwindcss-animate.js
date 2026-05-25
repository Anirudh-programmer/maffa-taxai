// Minimal tailwindcss-animate shim for environments where the package isn't installed
// In production, install the real package: npm install tailwindcss-animate
const plugin = require('tailwindcss/plugin')

module.exports = plugin(
  ({ addUtilities, matchUtilities, theme }) => {
    addUtilities({
      '@keyframes enter': { from: { opacity: 'var(--tw-enter-opacity,1)', transform: 'translate3d(var(--tw-enter-translate-x,0),var(--tw-enter-translate-y,0),0) scale3d(var(--tw-enter-scale,1),var(--tw-enter-scale,1),var(--tw-enter-scale,1)) rotate(var(--tw-enter-rotate,0))' } },
      '@keyframes exit': { to: { opacity: 'var(--tw-exit-opacity,1)', transform: 'translate3d(var(--tw-exit-translate-x,0),var(--tw-exit-translate-y,0),0) scale3d(var(--tw-exit-scale,1),var(--tw-exit-scale,1),var(--tw-exit-scale,1)) rotate(var(--tw-exit-rotate,0))' } },
      '.animate-in': { animationName: 'enter', animationDuration: theme('animationDuration.DEFAULT', '150ms'), '--tw-enter-opacity': 'initial', '--tw-enter-scale': 'initial', '--tw-enter-rotate': 'initial', '--tw-enter-translate-x': 'initial', '--tw-enter-translate-y': 'initial' },
      '.animate-out': { animationName: 'exit', animationDuration: theme('animationDuration.DEFAULT', '150ms'), '--tw-exit-opacity': 'initial', '--tw-exit-scale': 'initial', '--tw-exit-rotate': 'initial', '--tw-exit-translate-x': 'initial', '--tw-exit-translate-y': 'initial' },
    })
  }
)
