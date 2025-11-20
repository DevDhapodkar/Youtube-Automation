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
                    950: '#000000',
                    900: '#0a0a0a',
                    800: '#1a1a1a',
                    700: '#2a2a2a',
                },
                crimson: {
                    600: '#dc143c',
                    500: '#ff1744',
                    400: '#ff4569',
                    300: '#ff6b8a',
                },
                rose: {
                    500: '#ff0844',
                    400: '#ff2e63',
                },
            },
            backgroundImage: {
                'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
                'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
                'gradient-red': 'linear-gradient(135deg, #ff0844 0%, #dc143c 100%)',
                'gradient-dark': 'linear-gradient(135deg, #1a1a1a 0%, #0a0a0a 100%)',
            },
            boxShadow: {
                'glow-red': '0 0 20px rgba(255, 8, 68, 0.5)',
                'glow-red-lg': '0 0 40px rgba(255, 8, 68, 0.6)',
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
                    '0%': { boxShadow: '0 0 20px rgba(255, 8, 68, 0.5)' },
                    '100%': { boxShadow: '0 0 40px rgba(255, 8, 68, 0.8)' },
                },
            },
        },
    },
    plugins: [],
}
