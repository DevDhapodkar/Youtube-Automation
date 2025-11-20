import React, { useState, useEffect, useRef } from 'react';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import { motion } from 'framer-motion';
import { Play, Square, Activity, Terminal, Settings, Youtube, CheckCircle, AlertCircle } from 'lucide-react';
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
        <div className="min-h-screen bg-dark-900 text-white p-8 font-sans selection:bg-accent-500/30">
            <div className="max-w-6xl mx-auto space-y-8">
                {/* Header */}
                <header className="flex items-center justify-between pb-6 border-b border-white/10">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-red-600/20 rounded-xl border border-red-500/30">
                            <Youtube className="w-8 h-8 text-red-500" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold tracking-tight">YouTube Automation Agent</h1>
                            <div className="flex items-center gap-2 mt-1">
                                <div className={cn("w-2 h-2 rounded-full animate-pulse", readyState === ReadyState.OPEN ? "bg-green-500" : "bg-red-500")} />
                                <span className="text-sm text-gray-400 font-medium">
                                    {readyState === ReadyState.OPEN ? "System Online" : "Disconnected"}
                                </span>
                            </div>
                        </div>
                    </div>
                    <button className="p-2 hover:bg-white/5 rounded-lg transition-colors">
                        <Settings className="w-6 h-6 text-gray-400" />
                    </button>
                </header>

                {/* Main Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Status Card */}
                    <div className="lg:col-span-2 space-y-6">
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="bg-dark-800 rounded-3xl p-8 border border-white/5 relative overflow-hidden"
                        >
                            <div className="absolute top-0 right-0 p-32 bg-accent-500/10 rounded-full blur-3xl -mr-16 -mt-16" />

                            <h2 className="text-gray-400 font-medium mb-2 flex items-center gap-2">
                                <Activity className="w-4 h-4" /> Current Activity
                            </h2>
                            <div className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-400 leading-tight min-h-[3em]">
                                {status}
                            </div>

                            {/* Progress Bar (Fake for visual) */}
                            {isRunning && (
                                <motion.div
                                    className="h-1 bg-accent-500/30 mt-8 rounded-full overflow-hidden"
                                >
                                    <motion.div
                                        className="h-full bg-accent-500"
                                        initial={{ x: '-100%' }}
                                        animate={{ x: '100%' }}
                                        transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                                    />
                                </motion.div>
                            )}
                        </motion.div>

                        {/* Controls */}
                        <div className="grid grid-cols-2 gap-4">
                            <button
                                onClick={startAgent}
                                disabled={isRunning}
                                className="group relative overflow-hidden rounded-2xl bg-white text-black p-6 font-bold text-xl hover:scale-[1.02] transition-transform disabled:opacity-50 disabled:hover:scale-100"
                            >
                                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-black/5 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
                                <div className="flex items-center justify-center gap-3">
                                    <Play className="w-6 h-6 fill-current" />
                                    Start Automation
                                </div>
                            </button>

                            <button
                                onClick={stopAgent}
                                disabled={!isRunning}
                                className="rounded-2xl bg-dark-800 border border-white/10 text-white p-6 font-bold text-xl hover:bg-red-500/10 hover:border-red-500/50 hover:text-red-500 transition-all disabled:opacity-50"
                            >
                                <div className="flex items-center justify-center gap-3">
                                    <Square className="w-6 h-6 fill-current" />
                                    Stop
                                </div>
                            </button>
                        </div>
                    </div>

                    {/* Stats / Info */}
                    <div className="bg-dark-800 rounded-3xl p-6 border border-white/5 space-y-6">
                        <h3 className="font-bold text-lg">Quick Stats</h3>

                        {/* Auth Status */}
                        <div className={cn("p-4 rounded-xl border transition-colors", isAuthenticated ? "bg-green-500/10 border-green-500/20" : "bg-red-500/10 border-red-500/20")}>
                            <div className="flex items-center justify-between mb-2">
                                <div className="text-sm font-medium text-gray-300">YouTube Connection</div>
                                {isAuthenticated ? <CheckCircle className="w-5 h-5 text-green-500" /> : <AlertCircle className="w-5 h-5 text-red-500" />}
                            </div>
                            {isAuthenticated ? (
                                <div className="text-green-400 text-sm">Connected</div>
                            ) : (
                                <button
                                    onClick={authenticate}
                                    className="w-full py-2 bg-red-600 hover:bg-red-500 rounded-lg text-sm font-bold transition-colors"
                                >
                                    Connect Channel
                                </button>
                            )}
                        </div>

                        <div className="space-y-4">
                            <div className="p-4 bg-dark-900 rounded-xl border border-white/5">
                                <div className="text-sm text-gray-400">Uploads Today</div>
                                <div className="text-2xl font-bold">0</div>
                            </div>
                            <div className="p-4 bg-dark-900 rounded-xl border border-white/5">
                                <div className="text-sm text-gray-400">Next Scheduled</div>
                                <div className="text-xl font-mono text-accent-400">14:00</div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Terminal / Logs */}
                <div className="bg-black rounded-xl border border-white/10 overflow-hidden font-mono text-sm">
                    <div className="bg-dark-800 px-4 py-2 flex items-center gap-2 border-b border-white/5">
                        <Terminal className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-400">System Logs</span>
                    </div>
                    <div className="p-4 h-64 overflow-y-auto space-y-1 text-gray-300">
                        {logs.length === 0 && <div className="text-gray-600 italic">Waiting for logs...</div>}
                        {logs.map((log, i) => (
                            <div key={i} className="break-words">
                                <span className="text-accent-500 mr-2">➜</span>
                                {log}
                            </div>
                        ))}
                        <div ref={logsEndRef} />
                    </div>
                </div>
            </div>
        </div>
    );
}

export default App;
