/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                dark: {
                    950: '#0a0a0a',
                    900: '#0f0f0f',
                    800: '#1a1a1a',
                    700: '#2a2a2a',
                    600: '#3a3a3a',
                },
                crimson: {
                    600: '#dc143c',
                    500: '#ff1744',
                    400: '#ff4569',
                    300: '#ff6b8a',
                },
                rose: {
                    500: '#ff1744',
                    400: '#ff2e63',
                },
            },
            backgroundImage: {
                'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
                'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
                'gradient-red': 'linear-gradient(135deg, #ff1744 0%, #dc143c 100%)',
                'gradient-dark': 'linear-gradient(135deg, #2a2a2a 0%, #1a1a1a 100%)',
            },
            boxShadow: {
                'glow-red': '0 0 25px rgba(255, 23, 68, 0.6)',
                'glow-red-lg': '0 0 45px rgba(255, 23, 68, 0.8)',
            },
            animation: {
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'float': 'float 6s ease-in-out infinite',
                'glow': 'glow 2s ease-in-out infinite alternate',
            },
            keyframes: {
                float: {
                    '0%, 100%': { transform: 'translateY(0px)' },
                    '50%': { transform: 'translateY(-20px)' },
                },
                glow: {
                    '0%': { boxShadow: '0 0 25px rgba(255, 23, 68, 0.6)' },
                    '100%': { boxShadow: '0 0 45px rgba(255, 23, 68, 0.9)' },
                },
            },
        },
    },
    plugins: [],
}
