import React, { useState, useEffect, useRef } from 'react';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, Square, Activity, Terminal, Settings, Youtube, CheckCircle, AlertCircle, Sparkles, TrendingUp, Zap, X, Check } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { JellySwitch } from './components/JellySwitch';

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
    const [selectedNiche, setSelectedNiche] = useState('general');
    const [schedule, setSchedule] = useState([]);
    const [dailyShortCount, setDailyShortCount] = useState(2);
    const [dailyLongCount, setDailyLongCount] = useState(1);
    const [authUrl, setAuthUrl] = useState(null);
    const [newTime, setNewTime] = useState('');
    const logsEndRef = useRef(null);

    // Manual Order State
    const [orderNiche, setOrderNiche] = useState('general');
    const [orderTopic, setOrderTopic] = useState('');
    const [orderType, setOrderType] = useState('portrait'); // portrait | landscape
    const [orderDuration, setOrderDuration] = useState(60);
    const [isOrdering, setIsOrdering] = useState(false);

    const niches = [
        { value: 'general', label: '🎬 General/Trending', desc: 'Viral curiosity content' },
        { value: 'horror', label: '👻 Horror Facts', desc: 'Scary facts & legends' },
        { value: 'horror_stories', label: '📖 Horror Stories', desc: 'Narrative suspense tales' },
        { value: 'history', label: '📜 History Facts', desc: 'Educational & dramatic' },
        { value: 'scp', label: '🔬 SCP Foundation', desc: 'Classified anomalies' },
        { value: 'life_advice', label: '💡 Life Advice', desc: 'Psychology & tips' },
        { value: 'news', label: '📰 News/Tech', desc: 'Breaking updates' },
    ];

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
                setSelectedNiche(data.niche || 'general');
                setSchedule(data.schedule || []);
                setDailyShortCount(data.daily_short_count !== undefined ? data.daily_short_count : 2);
                setDailyLongCount(data.daily_long_count !== undefined ? data.daily_long_count : 1);
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
            } else if (msg.type === 'auth_url') {
                setAuthUrl(msg.data);
                setLogs((prev) => [...prev, "Received Auth URL. Please check the popup."]);
            }
        }
    }, [lastMessage]);

    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    const handleSwitchToggle = async (newState) => {
        if (newState && !isRunning) {
            // Start
            try {
                await fetch('http://localhost:8000/start', { method: 'POST' });
                setIsRunning(true);
            } catch (e) {
                console.error(e);
            }
        } else if (!newState && isRunning) {
            // Stop
            try {
                await fetch('http://localhost:8000/stop', { method: 'POST' });
                setIsRunning(false);
            } catch (e) {
                console.error(e);
            }
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

    const updateConfig = async () => {
        try {
            const res = await fetch('http://localhost:8000/update_config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    niche: selectedNiche,
                    schedule,
                    daily_short_count: parseInt(dailyShortCount),
                    daily_long_count: parseInt(dailyLongCount)
                })
            });
            const data = await res.json();
            setLogs(prev => [...prev, `Config updated: ${data.message}`]);
            setShowSettings(false);
        } catch (e) {
            console.error(e);
        }
    };

    const addScheduleTime = () => {
        if (newTime && !schedule.includes(newTime)) {
            setSchedule([...schedule, newTime]);
            setNewTime('');
        }
    };

    const removeScheduleTime = (time) => {
        setSchedule(schedule.filter(t => t !== time));
    };

    const handleOrderVideo = async () => {
        if (isRunning || isOrdering) return;

        setIsOrdering(true);
        try {
            const res = await fetch('http://localhost:8000/order_video', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    niche: orderNiche,
                    topic: orderTopic || null,
                    orientation: orderType,
                    duration: parseInt(orderDuration),
                    upload: true
                })
            });
            const data = await res.json();
            if (data.success) {
                setLogs(prev => [...prev, "✅ Order received! Starting generation..."]);
            } else {
                setLogs(prev => [...prev, `❌ Error: ${data.message}`]);
                setIsOrdering(false);
            }
        } catch (e) {
            console.error(e);
            setLogs(prev => [...prev, "❌ Network Error"]);
            setIsOrdering(false);
        }

        // Reset ordering state after a delay or let the logs/status handle it
        setTimeout(() => setIsOrdering(false), 2000);
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
                    className="flex items-center justify-between pb-6 border-b border-white/20">
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
                                YouTube Automation <span className="text-sm bg-crimson-500 px-2 py-1 rounded-full align-top ml-2">v1.1</span>
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

                {/* Main Grid */}
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

                        {/* Jelly Switch Control */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}
                            className="glass rounded-3xl p-10 border border-white/20"
                        >
                            <div className="flex flex-col items-center gap-6">
                                <h3 className="text-2xl font-black text-white flex items-center gap-3">
                                    <Zap className="w-7 h-7 text-crimson-400" />
                                    Agent Control
                                </h3>

                                <div className="flex items-center gap-6">
                                    <span className={cn(
                                        "text-lg font-bold transition-colors",
                                        !isRunning ? "text-white" : "text-gray-500"
                                    )}>
                                        OFF
                                    </span>

                                    <JellySwitch
                                        checked={isRunning}
                                        onChange={handleSwitchToggle}
                                        size="large"
                                    />

                                    <span className={cn(
                                        "text-lg font-bold transition-colors",
                                        isRunning ? "text-crimson-400" : "text-gray-500"
                                    )}>
                                        ON
                                    </span>
                                </div>

                                <p className="text-gray-400 text-sm text-center">
                                    {isRunning
                                        ? "Agent is running - toggle to stop"
                                        : "Agent is idle - toggle to start"}
                                </p>
                            </div>
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

                    {/* Create Video Card */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.35 }}
                        className="lg:col-span-3 glass rounded-3xl p-8 border border-white/20 relative overflow-hidden"
                    >
                        <div className="absolute top-0 right-0 p-4 opacity-10">
                            <Sparkles className="w-32 h-32 text-crimson-500" />
                        </div>

                        <h3 className="font-black text-2xl flex items-center gap-3 text-white mb-6 relative z-10">
                            <Sparkles className="w-7 h-7 text-crimson-400" />
                            Create Custom Video
                        </h3>

                        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 relative z-10">
                            {/* Niche */}
                            <div className="space-y-2">
                                <label className="text-sm font-bold text-gray-400">Niche</label>
                                <select
                                    value={orderNiche}
                                    onChange={(e) => setOrderNiche(e.target.value)}
                                    className="w-full p-3 bg-dark-800 border border-white/10 rounded-xl text-white focus:border-crimson-500 focus:outline-none"
                                >
                                    {niches.map(n => (
                                        <option key={n.value} value={n.value}>{n.label}</option>
                                    ))}
                                    <option value="custom">Custom Niche</option>
                                </select>
                            </div>

                            {/* Topic */}
                            <div className="space-y-2 md:col-span-2">
                                <label className="text-sm font-bold text-gray-400">Topic (Optional)</label>
                                <input
                                    type="text"
                                    placeholder="Leave empty for AI viral topic..."
                                    value={orderTopic}
                                    onChange={(e) => setOrderTopic(e.target.value)}
                                    className="w-full p-3 bg-dark-800 border border-white/10 rounded-xl text-white focus:border-crimson-500 focus:outline-none"
                                >
                                </input>
                            </div>

                            {/* Type & Action */}
                            <div className="space-y-2">
                                <label className="text-sm font-bold text-gray-400">Format</label>
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => { setOrderType('portrait'); setOrderDuration(60); }}
                                        className={cn(
                                            "flex-1 p-3 rounded-xl font-bold text-sm transition-all border",
                                            orderType === 'portrait'
                                                ? "bg-crimson-500 border-crimson-400 text-white shadow-glow-red"
                                                : "bg-dark-800 border-white/10 text-gray-400 hover:bg-dark-700"
                                        )}
                                    >
                                        Shorts
                                    </button>
                                    <button
                                        onClick={() => { setOrderType('landscape'); setOrderDuration(300); }}
                                        className={cn(
                                            "flex-1 p-3 rounded-xl font-bold text-sm transition-all border",
                                            orderType === 'landscape'
                                                ? "bg-crimson-500 border-crimson-400 text-white shadow-glow-red"
                                                : "bg-dark-800 border-white/10 text-gray-400 hover:bg-dark-700"
                                        )}
                                    >
                                        Long
                                    </button>
                                </div>
                            </div>

                            {/* Duration */}
                            <div className="space-y-2">
                                <label className="text-sm font-bold text-gray-400">Target Duration</label>
                                <select
                                    value={orderDuration}
                                    onChange={(e) => setOrderDuration(e.target.value)}
                                    className="w-full p-3 bg-dark-800 border border-white/10 rounded-xl text-white focus:border-crimson-500 focus:outline-none"
                                >
                                    <option value="30">30 Seconds</option>
                                    <option value="60">1 Minute (Shorts)</option>
                                    <option value="120">2 Minutes</option>
                                    <option value="180">3 Minutes</option>
                                    <option value="300">5 Minutes</option>
                                    <option value="480">8 Minutes</option>
                                    <option value="600">10 Minutes</option>
                                    <option value="900">15 Minutes</option>
                                </select>
                            </div>
                        </div>

                        <div className="mt-6 flex justify-end relative z-10">
                            <motion.button
                                onClick={handleOrderVideo}
                                disabled={isRunning || isOrdering}
                                className={cn(
                                    "px-8 py-3 rounded-xl font-black text-lg flex items-center gap-2 transition-all",
                                    isRunning || isOrdering
                                        ? "bg-gray-600 text-gray-400 cursor-not-allowed"
                                        : "bg-gradient-to-r from-crimson-500 to-rose-600 text-white shadow-lg hover:shadow-glow-red hover:scale-105"
                                )}
                                whileTap={{ scale: 0.95 }}
                            >
                                {isRunning || isOrdering ? (
                                    <>Processing...</>
                                ) : (
                                    <>
                                        <Zap className="w-5 h-5" />
                                        Generate Now
                                    </>
                                )}
                            </motion.button>
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
                                {/* Niche Selection */}
                                <div className="p-6 glass rounded-2xl border border-white/20">
                                    <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                                        🎯 Video Type (Niche)
                                    </h3>
                                    <select
                                        value={selectedNiche}
                                        onChange={(e) => setSelectedNiche(e.target.value)}
                                        className="w-full p-4 bg-dark-800 border-2 border-white/20 rounded-xl text-white font-semibold focus:border-crimson-500 focus:outline-none transition-all"
                                    >
                                        {niches.map(niche => (
                                            <option key={niche.value} value={niche.value}>
                                                {niche.label} - {niche.desc}
                                            </option>
                                        ))}
                                    </select>
                                    <p className="text-gray-400 text-sm mt-3">
                                        Choose the type of content to generate. Each niche has tailored scripts and visuals.
                                    </p>
                                </div>

                                {/* Schedule Configuration */}
                                <div className="p-6 glass rounded-2xl border border-white/20">
                                    <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                                        ⏰ Upload Schedule
                                    </h3>
                                    <div className="space-y-4">
                                        <div className="flex gap-3">
                                            <input
                                                type="time"
                                                value={newTime}
                                                onChange={(e) => setNewTime(e.target.value)}
                                                className="flex-1 p-4 bg-dark-800 border-2 border-white/20 rounded-xl text-white font-mono focus:border-crimson-500 focus:outline-none transition-all"
                                            />
                                            <motion.button
                                                onClick={addScheduleTime}
                                                className="px-6 py-4 bg-gradient-red hover:shadow-glow-red rounded-xl text-white font-bold transition-all"
                                                whileHover={{ scale: 1.05 }}
                                                whileTap={{ scale: 0.95 }}
                                            >
                                                Add
                                            </motion.button>
                                        </div>

                                        {schedule.length > 0 && (
                                            <div className="space-y-2">
                                                <p className="text-sm text-gray-400 font-semibold">Scheduled Times:</p>
                                                {schedule.map((time, i) => (
                                                    <motion.div
                                                        key={i}
                                                        initial={{ opacity: 0, x: -20 }}
                                                        animate={{ opacity: 1, x: 0 }}
                                                        className="flex items-center justify-between p-3 bg-dark-800 rounded-lg border border-white/10"
                                                    >
                                                        <span className="font-mono text-crimson-400 font-bold text-lg">{time}</span>
                                                        <motion.button
                                                            onClick={() => removeScheduleTime(time)}
                                                            className="p-2 glass-red rounded-lg hover:bg-crimson-500/30 transition-all"
                                                            whileHover={{ scale: 1.1 }}
                                                            whileTap={{ scale: 0.9 }}
                                                        >
                                                            <X className="w-4 h-4 text-white" />
                                                        </motion.button>
                                                    </motion.div>
                                                ))}
                                            </div>
                                        )}

                                        <p className="text-gray-400 text-sm">
                                            {schedule.length === 0
                                                ? "No scheduled times. Videos will only run when you click Start."
                                                : `Agent will automatically run ${schedule.length} time(s) per day.`}
                                        </p>
                                    </div>
                                </div>

                                {/* Daily Limits Configuration */}
                                <div className="p-6 glass rounded-2xl border border-white/20">
                                    <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                                        📊 Daily Video Limits
                                    </h3>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-gray-400 text-sm font-semibold mb-2">Daily Shorts</label>
                                            <input
                                                type="number"
                                                min="0"
                                                max="10"
                                                value={dailyShortCount}
                                                onChange={(e) => setDailyShortCount(e.target.value)}
                                                className="w-full p-4 bg-dark-800 border-2 border-white/20 rounded-xl text-white font-mono focus:border-crimson-500 focus:outline-none transition-all"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-gray-400 text-sm font-semibold mb-2">Daily Long Videos</label>
                                            <input
                                                type="number"
                                                min="0"
                                                max="5"
                                                value={dailyLongCount}
                                                onChange={(e) => setDailyLongCount(e.target.value)}
                                                className="w-full p-4 bg-dark-800 border-2 border-white/20 rounded-xl text-white font-mono focus:border-crimson-500 focus:outline-none transition-all"
                                            />
                                        </div>
                                    </div>
                                    <p className="text-gray-400 text-sm mt-3">
                                        The agent will generate this many videos each time the schedule triggers.
                                    </p>
                                </div>

                                <div className="p-6 glass-red rounded-2xl border border-crimson-500/30">
                                    <h3 className="text-xl font-bold text-white mb-4">⚙️ API Configuration</h3>
                                    <p className="text-gray-300 text-sm mb-4">
                                        Configure your API keys in the <code className="bg-dark-700 px-2 py-1 rounded text-crimson-400">.env</code> file:
                                    </p>
                                    <div className="space-y-3 text-sm font-mono bg-dark-900/50 p-4 rounded-xl border border-white/10">
                                        <div className="text-gray-400">GEMINI_API_KEY=your_key_here</div>
                                        <div className="text-gray-400">PEXELS_API_KEY=your_key_here</div>
                                        <div className="text-gray-400">YOUTUBE_API_KEY=your_key_here</div>
                                    </div>
                                </div>

                                <motion.button
                                    onClick={updateConfig}
                                    className="w-full py-4 bg-gradient-red hover:shadow-glow-red rounded-xl text-lg font-black transition-all duration-300 text-white flex items-center justify-center gap-2"
                                    whileHover={{ scale: 1.02 }}
                                    whileTap={{ scale: 0.98 }}
                                >
                                    <Check className="w-5 h-5" />
                                    Save Configuration
                                </motion.button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
                {/* Auth URL Modal */}
                <AnimatePresence>
                    {authUrl && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center z-[60] p-4"
                        >
                            <motion.div
                                initial={{ scale: 0.9, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                exit={{ scale: 0.9, opacity: 0 }}
                                className="glass border-2 border-crimson-500 rounded-3xl p-8 max-w-xl w-full text-center space-y-6 shadow-glow-red-lg"
                            >
                                <div className="w-16 h-16 bg-crimson-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <Youtube className="w-8 h-8 text-crimson-500" />
                                </div>

                                <h2 className="text-2xl font-black text-white">
                                    Authentication Required
                                </h2>

                                <p className="text-gray-300">
                                    Please authorize the application to access your YouTube channel.
                                    Click the button below to open the Google login page.
                                </p>

                                <a
                                    href={authUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="block w-full py-4 bg-gradient-red hover:shadow-glow-red rounded-xl text-lg font-bold text-white transition-all transform hover:scale-105"
                                    onClick={() => setAuthUrl(null)}
                                >
                                    Authorize with Google
                                </a>

                                <button
                                    onClick={() => setAuthUrl(null)}
                                    className="text-gray-500 hover:text-white text-sm font-semibold transition-colors"
                                >
                                    Close / Already Authorized
                                </button>
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>

            </AnimatePresence>
        </div >
    );
}

export default App;
