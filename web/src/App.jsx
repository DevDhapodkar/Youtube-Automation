import React, { useState, useEffect, useRef } from 'react';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, Square, Activity, Terminal, Settings, Youtube, CheckCircle, AlertCircle, Sparkles, TrendingUp, Zap, X, Save } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs) {
    return twMerge(clsx(inputs));
}

const WS_URL = 'ws://localhost:8000/ws';

function App() {
    const [logs, setLogs] = useState([]);
    const [status, setStatus] = useState('Idle');
    const [isRunning, setIsRunning] = useState(false);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [showSettings, setShowSettings] = useState(false);
    const logsEndRef = useRef(null);

    const { sendMessage, lastMessage, readyState } = useWebSocket(WS_URL, {
        onOpen: () => console.log('Connected to Agent'),
        shouldReconnect: (closeEvent) => true,
    });

    useEffect(() => {
        // Initial status check
        fetch('http://localhost:8000/status')
            .then(res => res.json())
            .then(data => {
                setIsRunning(data.is_running);
                setStatus(data.current_action);
                setIsAuthenticated(data.is_authenticated);
            });
    }, []);

    useEffect(() => {
        if (lastMessage !== null) {
            const msg = JSON.parse(lastMessage.data);
            if (msg.type === 'log') {
                setLogs((prev) => [...prev, msg.data]);
            } else if (msg.type === 'status') {
                setStatus(msg.data);
            } else if (msg.type === 'state') {
                setIsRunning(msg.data.is_running);
            } else if (msg.type === 'error') {
                setLogs((prev) => [...prev, `ERROR: ${msg.data}`]);
            }
        }
    }, [lastMessage]);

    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    const startAgent = async () => {
        try {
            await fetch('http://localhost:8000/start', { method: 'POST' });
            setIsRunning(true);
        } catch (e) {
            console.error(e);
        }
    };

    const stopAgent = async () => {
        try {
            await fetch('http://localhost:8000/stop', { method: 'POST' });
            setIsRunning(false);
        } catch (e) {
            console.error(e);
        }
    };

    const authenticate = async () => {
        try {
            setLogs(prev => [...prev, "Starting Authentication... Check for browser window."]);
            const res = await fetch('http://localhost:8000/auth', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                setIsAuthenticated(true);
                setLogs(prev => [...prev, "Authentication Successful!"]);
            } else {
                setLogs(prev => [...prev, "Authentication Failed."]);
            }
        } catch (e) {
            console.error(e);
        }
    };

    return (
        <div className="min-h-screen bg-dark-900 text-white p-4 md:p-8 font-sans selection:bg-crimson-500/30 relative overflow-hidden">
            {/* Animated Background Elements */}
            <div className="fixed inset-0 pointer-events-none overflow-hidden">
                <motion.div
                    className="absolute top-20 right-20 w-[500px] h-[500px] bg-crimson-500/20 rounded-full blur-[100px]"
                    animate={{
                        scale: [1, 1.2, 1],
                        x: [0, 50, 0],
                        y: [0, 30, 0],
                    }}
                    transition={{
                        duration: 10,
                        repeat: Infinity,
                        ease: "easeInOut"
                    }}
                />
                <motion.div
                    className="absolute bottom-20 left-20 w-[500px] h-[500px] bg-rose-500/15 rounded-full blur-[100px]"
                    animate={{
                        scale: [1.2, 1, 1.2],
                        x: [0, -30, 0],
                        y: [0, 50, 0],
                    }}
                    transition={{
                        duration: 12,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: 1
                    }}
                />
            </div>

            <div className="max-w-7xl mx-auto space-y-8 relative z-10">
                {/* Header */}
                <motion.header
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center justify-between pb-6 border-b border-white/20"
                >
                    <div className="flex items-center gap-4">
                        <motion.div
                            className="p-4 bg-gradient-red rounded-2xl shadow-glow-red-lg"
                            whileHover={{ scale: 1.05, rotate: 5 }}
                            whileTap={{ scale: 0.95 }}
                        >
                            <Youtube className="w-10 h-10 text-white drop-shadow-lg" />
                        </motion.div>
                        <div>
                            <h1 className="text-4xl md:text-5xl font-black tracking-tight text-white drop-shadow-lg">
                                YouTube Automation
                            </h1>
                            <div className="flex items-center gap-3 mt-2">
                                <motion.div
                                    className={cn("w-2.5 h-2.5 rounded-full shadow-lg",
                                        readyState === ReadyState.OPEN ? "bg-green-400 shadow-green-400/50" : "bg-crimson-500 shadow-crimson-500/50"
                                    )}
                                    animate={{
                                        scale: [1, 1.3, 1],
                                    }}
                                    transition={{
                                        duration: 2,
                                        repeat: Infinity,
                                    }}
                                />
                                <span className="text-base text-gray-300 font-semibold">
                                    {readyState === ReadyState.OPEN ? "System Online" : "Disconnected"}
                                </span>
                            </div>
                        </div>
                    </div>
                    <motion.button
                        onClick={() => setShowSettings(true)}
                        className="p-4 glass rounded-2xl hover:glass-red transition-all duration-300"
                        whileHover={{ scale: 1.05, rotate: 90 }}
                        whileTap={{ scale: 0.95 }}
                    >
                        <Settings className="w-7 h-7 text-white" />
                    </motion.button>
                </motion.header>

                {/* Main Grid - rest of the code stays the same */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Status Card */}
                    <div className="lg:col-span-2 space-y-6">
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: 0.1 }}
                            className="glass rounded-3xl p-10 relative overflow-hidden group border border-white/20"
                        >
                            {/* Gradient overlay */}
                            <div className="absolute inset-0 bg-gradient-to-br from-crimson-500/10 via-transparent to-rose-500/10" />

                            <div className="relative z-10">
                                <h2 className="text-gray-300 font-bold text-lg mb-4 flex items-center gap-3">
                                    <Zap className="w-6 h-6 text-crimson-400" />
                                    Current Activity
                                </h2>
                                <motion.div
                                    className="text-4xl md:text-5xl font-black text-white leading-tight min-h-[5rem] flex items-center drop-shadow-lg"
                                    key={status}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ duration: 0.3 }}
                                >
                                    {status}
                                </motion.div>

                                {/* Progress Bar */}
                                <AnimatePresence>
                                    {isRunning && (
                                        <motion.div
                                            initial={{ opacity: 0, scaleX: 0 }}
                                            animate={{ opacity: 1, scaleX: 1 }}
                                            exit={{ opacity: 0, scaleX: 0 }}
                                            className="h-2 bg-dark-700 mt-8 rounded-full overflow-hidden"
                                        >
                                            <motion.div
                                                className="h-full bg-gradient-red shadow-glow-red"
                                                initial={{ x: '-100%' }}
                                                animate={{ x: '100%' }}
                                                transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
                                            />
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        </motion.div>

                        {/* Controls */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}
                            className="grid grid-cols-2 gap-6"
                        >
                            <motion.button
                                onClick={startAgent}
                                disabled={isRunning}
                                className="group relative overflow-hidden rounded-3xl bg-gradient-red p-8 font-black text-2xl shadow-glow-red hover:shadow-glow-red-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-glow-red"
                                whileHover={{ scale: isRunning ? 1 : 1.03 }}
                                whileTap={{ scale: isRunning ? 1 : 0.97 }}
                            >
                                <div className="absolute inset-0 shimmer opacity-0 group-hover:opacity-100" />
                                <div className="flex items-center justify-center gap-3 relative z-10 text-white">
                                    <Play className="w-8 h-8 fill-current drop-shadow-lg" />
                                    <span className="drop-shadow-lg">Start</span>
                                </div>
                            </motion.button>

                            <motion.button
                                onClick={stopAgent}
                                disabled={!isRunning}
                                className="rounded-3xl glass border-2 border-crimson-500/50 text-white p-8 font-black text-2xl hover:glass-red hover:border-crimson-500 hover:shadow-glow-red transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                                whileHover={{ scale: !isRunning ? 1 : 1.03 }}
                                whileTap={{ scale: !isRunning ? 1 : 0.97 }}
                            >
                                <div className="flex items-center justify-center gap-3 drop-shadow-lg">
                                    <Square className="w-8 h-8 fill-current" />
                                    <span>Stop</span>
                                </div>
                            </motion.button>
                        </motion.div>
                    </div>

                    {/* Stats / Info */}
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.3 }}
                        className="glass rounded-3xl p-8 space-y-6 border border-white/20"
                    >
                        <h3 className="font-black text-2xl flex items-center gap-3 text-white">
                            <Sparkles className="w-7 h-7 text-crimson-400" />
                            Quick Stats
                        </h3>

                        {/* Auth Status */}
                        <motion.div
                            className={cn(
                                "p-6 rounded-2xl border-2 transition-all duration-300",
                                isAuthenticated
                                    ? "bg-green-500/20 border-green-400/50 shadow-lg shadow-green-500/20"
                                    : "glass-red border-crimson-500/50 shadow-lg shadow-crimson-500/20"
                            )}
                            whileHover={{ scale: 1.02 }}
                        >
                            <div className="flex items-center justify-between mb-4">
                                <div className="text-base font-bold text-white">YouTube Connection</div>
                                <motion.div
                                    animate={{ rotate: isAuthenticated ? 0 : 360 }}
                                    transition={{ duration: 2, repeat: isAuthenticated ? 0 : Infinity, ease: "linear" }}
                                >
                                    {isAuthenticated ? (
                                        <CheckCircle className="w-7 h-7 text-green-400 drop-shadow-lg" />
                                    ) : (
                                        <AlertCircle className="w-7 h-7 text-crimson-400 drop-shadow-lg" />
                                    )}
                                </motion.div>
                            </div>
                            <AnimatePresence mode="wait">
                                {isAuthenticated ? (
                                    <motion.div
                                        key="connected"
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: -10 }}
                                        className="text-green-300 text-base font-bold"
                                    >
                                        ✓ Connected
                                    </motion.div>
                                ) : (
                                    <motion.button
                                        key="connect"
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: -10 }}
                                        onClick={authenticate}
                                        className="w-full py-4 bg-gradient-red hover:shadow-glow-red rounded-xl text-base font-black transition-all duration-300 text-white"
                                        whileHover={{ scale: 1.03 }}
                                        whileTap={{ scale: 0.97 }}
                                    >
                                        Connect Channel
                                    </motion.button>
                                )}
                            </AnimatePresence>
                        </motion.div>

                        <div className="space-y-4">
                            <motion.div
                                className="p-6 glass rounded-2xl border border-white/20 hover:border-crimson-500/50 hover:shadow-lg hover:shadow-crimson-500/10 transition-all duration-300"
                                whileHover={{ scale: 1.02 }}
                            >
                                <div className="text-sm text-gray-300 font-semibold mb-2">Uploads Today</div>
                                <div className="text-5xl font-black text-white drop-shadow-lg">0</div>
                            </motion.div>
                            <motion.div
                                className="p-6 glass rounded-2xl border border-white/20 hover:border-crimson-500/50 hover:shadow-lg hover:shadow-crimson-500/10 transition-all duration-300"
                                whileHover={{ scale: 1.02 }}
                            >
                                <div className="text-sm text-gray-300 font-semibold mb-2 flex items-center gap-2">
                                    <TrendingUp className="w-5 h-5 text-crimson-400" />
                                    Next Scheduled
                                </div>
                                <div className="text-4xl font-black font-mono text-crimson-400 drop-shadow-lg">14:00</div>
                            </motion.div>
                        </div>
                    </motion.div>
                </div>

                {/* Terminal / Logs */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                    className="glass rounded-3xl overflow-hidden border-2 border-white/20 font-mono text-sm shadow-2xl"
                >
                    <div className="bg-dark-800/80 px-6 py-4 flex items-center gap-3 border-b border-white/20">
                        <Terminal className="w-6 h-6 text-crimson-400" />
                        <span className="text-white font-bold text-base">System Logs</span>
                        <div className="flex-1" />
                        <motion.div
                            className="flex gap-2"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.6 }}
                        >
                            <div className="w-3 h-3 rounded-full bg-crimson-500 shadow-lg shadow-crimson-500/50" />
                            <div className="w-3 h-3 rounded-full bg-yellow-400 shadow-lg shadow-yellow-400/50" />
                            <div className="w-3 h-3 rounded-full bg-green-400 shadow-lg shadow-green-400/50" />
                        </motion.div>
                    </div>
                    <div className="p-6 h-96 overflow-y-auto space-y-2 bg-dark-900/50">
                        <AnimatePresence initial={false}>
                            {logs.length === 0 && (
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    className="text-gray-500 italic text-base"
                                >
                                    Waiting for logs...
                                </motion.div>
                            )}
                            {logs.map((log, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ duration: 0.3 }}
                                    className="break-words hover:bg-white/5 px-3 py-2 rounded-lg transition-colors text-gray-200"
                                >
                                    <span className="text-crimson-400 mr-3 font-bold text-base">➜</span>
                                    {log}
                                </motion.div>
                            ))}
                        </AnimatePresence>
                        <div ref={logsEndRef} />
                    </div>
                </motion.div>
            </div>

            {/* Settings Modal */}
            <AnimatePresence>
                {showSettings && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
                        onClick={() => setShowSettings(false)}
                    >
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            transition={{ type: "spring", damping: 20 }}
                            className="glass border-2 border-white/20 rounded-3xl p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <div className="flex items-center justify-between mb-8">
                                <h2 className="text-3xl font-black text-white flex items-center gap-3">
                                    <Settings className="w-8 h-8 text-crimson-400" />
                                    Settings
                                </h2>
                                <motion.button
                                    onClick={() => setShowSettings(false)}
                                    className="p-2 glass rounded-xl hover:glass-red transition-all"
                                    whileHover={{ scale: 1.1, rotate: 90 }}
                                    whileTap={{ scale: 0.9 }}
                                >
                                    <X className="w-6 h-6 text-white" />
                                </motion.button>
                            </div>

                            <div className="space-y-6">
                                <div className="p-6 glass-red rounded-2xl border border-crimson-500/30">
                                    <h3 className="text-xl font-bold text-white mb-4">API Configuration</h3>
                                    <p className="text-gray-300 text-sm mb-4">
                                        Configure your API keys in the <code className="bg-dark-700 px-2 py-1 rounded text-crimson-400">.env</code> file:
                                    </p>
                                    <div className="space-y-3 text-sm font-mono bg-dark-900/50 p-4 rounded-xl border border-white/10">
                                        <div className="text-gray-400">GEMINI_API_KEY=your_key_here</div>
                                        <div className="text-gray-400">PEXELS_API_KEY=your_key_here</div>
                                    </div>
                                </div>

                                <div className="p-6 glass rounded-2xl border border-white/20">
                                    <h3 className="text-xl font-bold text-white mb-4">Upload Schedule</h3>
                                    <p className="text-gray-300 text-sm mb-4">
                                        Automation runs every 6 hours by default. Modify in <code className="bg-dark-700 px-2 py-1 rounded text-crimson-400">config/settings.py</code>
                                    </p>
                                </div>

                                <div className="p-6 glass rounded-2xl border border-white/20">
                                    <h3 className="text-xl font-bold text-white mb-4">Safety Mode</h3>
                                    <p className="text-gray-300 text-sm mb-4">
                                        Real uploads are currently disabled. To enable, uncomment the upload code in <code className="bg-dark-700 px-2 py-1 rounded text-crimson-400">api/main.py</code>
                                    </p>
                                </div>

                                <motion.button
                                    onClick={() => setShowSettings(false)}
                                    className="w-full py-4 bg-gradient-red hover:shadow-glow-red rounded-xl text-lg font-black transition-all duration-300 text-white flex items-center justify-center gap-2"
                                    whileHover={{ scale: 1.02 }}
                                    whileTap={{ scale: 0.98 }}
                                >
                                    <Save className="w-5 h-5" />
                                    Close
                                </motion.button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

export default App;
