import React, { useState, useEffect, useRef } from 'react';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, Square, Activity, Terminal, Settings, Youtube, CheckCircle, AlertCircle, Sparkles, TrendingUp } from 'lucide-react';
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
        <div className="min-h-screen bg-dark-950 text-white p-4 md:p-8 font-sans selection:bg-rose-500/30 relative overflow-hidden">
            {/* Animated Background Elements */}
            <div className="fixed inset-0 pointer-events-none overflow-hidden">
                <motion.div
                    className="absolute top-20 -left-20 w-96 h-96 bg-rose-500/10 rounded-full blur-3xl"
                    animate={{
                        scale: [1, 1.2, 1],
                        opacity: [0.3, 0.5, 0.3],
                    }}
                    transition={{
                        duration: 8,
                        repeat: Infinity,
                        ease: "easeInOut"
                    }}
                />
                <motion.div
                    className="absolute bottom-20 -right-20 w-96 h-96 bg-crimson-500/10 rounded-full blur-3xl"
                    animate={{
                        scale: [1.2, 1, 1.2],
                        opacity: [0.5, 0.3, 0.5],
                    }}
                    transition={{
                        duration: 8,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: 1
                    }}
                />
            </div>

            <div className="max-w-7xl mx-auto space-y-6 relative z-10">
                {/* Header */}
                <motion.header
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center justify-between pb-6 border-b border-white/10"
                >
                    <div className="flex items-center gap-4">
                        <motion.div
                            className="p-3 bg-gradient-red rounded-2xl shadow-glow-red"
                            whileHover={{ scale: 1.05, rotate: 5 }}
                            whileTap={{ scale: 0.95 }}
                        >
                            <Youtube className="w-8 h-8 text-white" />
                        </motion.div>
                        <div>
                            <h1 className="text-3xl md:text-4xl font-bold tracking-tight bg-gradient-to-r from-white via-rose-400 to-crimson-500 bg-clip-text text-transparent">
                                YouTube Automation Agent
                            </h1>
                            <div className="flex items-center gap-2 mt-1">
                                <motion.div
                                    className={cn("w-2 h-2 rounded-full", readyState === ReadyState.OPEN ? "bg-green-500" : "bg-rose-500")}
                                    animate={{
                                        scale: [1, 1.2, 1],
                                        opacity: [1, 0.5, 1],
                                    }}
                                    transition={{
                                        duration: 2,
                                        repeat: Infinity,
                                    }}
                                />
                                <span className="text-sm text-gray-400 font-medium">
                                    {readyState === ReadyState.OPEN ? "System Online" : "Disconnected"}
                                </span>
                            </div>
                        </div>
                    </div>
                    <motion.button
                        className="p-3 glass rounded-xl hover:glass-red transition-all duration-300"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                    >
                        <Settings className="w-6 h-6 text-gray-400" />
                    </motion.button>
                </motion.header>

                {/* Main Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Status Card */}
                    <div className="lg:col-span-2 space-y-6">
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: 0.1 }}
                            className="glass rounded-3xl p-8 relative overflow-hidden group"
                        >
                            {/* Animated gradient overlay */}
                            <div className="absolute inset-0 bg-gradient-to-br from-rose-500/5 via-transparent to-crimson-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

                            <div className="relative z-10">
                                <h2 className="text-gray-400 font-medium mb-3 flex items-center gap-2">
                                    <Activity className="w-5 h-5" />
                                    Current Activity
                                </h2>
                                <motion.div
                                    className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-white to-rose-400 bg-clip-text text-transparent leading-tight min-h-[4rem] flex items-center"
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
                                            className="h-1 bg-gradient-to-r from-rose-500/20 to-crimson-500/20 mt-6 rounded-full overflow-hidden"
                                        >
                                            <motion.div
                                                className="h-full bg-gradient-red"
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
                            className="grid grid-cols-2 gap-4"
                        >
                            <motion.button
                                onClick={startAgent}
                                disabled={isRunning}
                                className="group relative overflow-hidden rounded-2xl bg-gradient-red p-6 font-bold text-xl hover:shadow-glow-red-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none"
                                whileHover={{ scale: isRunning ? 1 : 1.02 }}
                                whileTap={{ scale: isRunning ? 1 : 0.98 }}
                            >
                                <div className="absolute inset-0 shimmer opacity-0 group-hover:opacity-100" />
                                <div className="flex items-center justify-center gap-3 relative z-10">
                                    <Play className="w-6 h-6 fill-current" />
                                    Start Automation
                                </div>
                            </motion.button>

                            <motion.button
                                onClick={stopAgent}
                                disabled={!isRunning}
                                className="rounded-2xl glass border border-rose-500/30 text-white p-6 font-bold text-xl hover:glass-red hover:border-rose-500/50 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                                whileHover={{ scale: !isRunning ? 1 : 1.02 }}
                                whileTap={{ scale: !isRunning ? 1 : 0.98 }}
                            >
                                <div className="flex items-center justify-center gap-3">
                                    <Square className="w-6 h-6 fill-current" />
                                    Stop
                                </div>
                            </motion.button>
                        </motion.div>
                    </div>

                    {/* Stats / Info */}
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.3 }}
                        className="glass rounded-3xl p-6 space-y-6"
                    >
                        <h3 className="font-bold text-xl flex items-center gap-2">
                            <Sparkles className="w-5 h-5 text-rose-500" />
                            Quick Stats
                        </h3>

                        {/* Auth Status */}
                        <motion.div
                            className={cn(
                                "p-5 rounded-2xl border transition-all duration-300",
                                isAuthenticated
                                    ? "bg-green-500/10 border-green-500/30"
                                    : "glass-red border-rose-500/30"
                            )}
                            whileHover={{ scale: 1.02 }}
                        >
                            <div className="flex items-center justify-between mb-3">
                                <div className="text-sm font-medium text-gray-300">YouTube Connection</div>
                                <motion.div
                                    animate={{ rotate: isAuthenticated ? 0 : 360 }}
                                    transition={{ duration: 2, repeat: isAuthenticated ? 0 : Infinity, ease: "linear" }}
                                >
                                    {isAuthenticated ? (
                                        <CheckCircle className="w-5 h-5 text-green-500" />
                                    ) : (
                                        <AlertCircle className="w-5 h-5 text-rose-500" />
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
                                        className="text-green-400 text-sm font-medium"
                                    >
                                        Connected
                                    </motion.div>
                                ) : (
                                    <motion.button
                                        key="connect"
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: -10 }}
                                        onClick={authenticate}
                                        className="w-full py-3 bg-gradient-red hover:shadow-glow-red rounded-xl text-sm font-bold transition-all duration-300"
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                    >
                                        Connect Channel
                                    </motion.button>
                                )}
                            </AnimatePresence>
                        </motion.div>

                        <div className="space-y-4">
                            <motion.div
                                className="p-5 glass rounded-2xl border border-white/5 hover:border-rose-500/30 transition-all duration-300"
                                whileHover={{ scale: 1.02 }}
                            >
                                <div className="text-sm text-gray-400 mb-2">Uploads Today</div>
                                <div className="text-3xl font-bold bg-gradient-to-r from-white to-rose-400 bg-clip-text text-transparent">0</div>
                            </motion.div>
                            <motion.div
                                className="p-5 glass rounded-2xl border border-white/5 hover:border-rose-500/30 transition-all duration-300"
                                whileHover={{ scale: 1.02 }}
                            >
                                <div className="text-sm text-gray-400 mb-2 flex items-center gap-2">
                                    <TrendingUp className="w-4 h-4" />
                                    Next Scheduled
                                </div>
                                <div className="text-2xl font-mono text-rose-400 font-bold">14:00</div>
                            </motion.div>
                        </div>
                    </motion.div>
                </div>

                {/* Terminal / Logs */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                    className="glass rounded-2xl overflow-hidden border border-white/5 font-mono text-sm"
                >
                    <div className="bg-dark-900/50 px-6 py-3 flex items-center gap-3 border-b border-white/5">
                        <Terminal className="w-5 h-5 text-rose-500" />
                        <span className="text-gray-400 font-semibold">System Logs</span>
                        <div className="flex-1" />
                        <motion.div
                            className="flex gap-2"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.6 }}
                        >
                            <div className="w-3 h-3 rounded-full bg-rose-500" />
                            <div className="w-3 h-3 rounded-full bg-yellow-500" />
                            <div className="w-3 h-3 rounded-full bg-green-500" />
                        </motion.div>
                    </div>
                    <div className="p-6 h-80 overflow-y-auto space-y-2 text-gray-300 bg-dark-950/50">
                        <AnimatePresence initial={false}>
                            {logs.length === 0 && (
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    className="text-gray-600 italic"
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
                                    className="break-words hover:bg-white/5 px-2 py-1 rounded transition-colors"
                                >
                                    <span className="text-rose-500 mr-3 font-bold">➜</span>
                                    {log}
                                </motion.div>
                            ))}
                        </AnimatePresence>
                        <div ref={logsEndRef} />
                    </div>
                </motion.div>
            </div>
        </div>
    );
}

export default App;
