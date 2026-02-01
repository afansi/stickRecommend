import React, { useState, useEffect } from 'react';
import api from '../api';
import {
    Compass,
    TrendingUp,
    ShieldAlert,
    BrainCircuit,
    Activity,
    Target,
    BarChart3,
    Calendar,
    Lock,
    ArrowUpRight,
    ArrowDownRight
} from 'lucide-react';

const TradingHub = () => {
    const [macro, setMacro] = useState(null);
    const [opportunities, setOpportunities] = useState([]);
    const [journal, setJournal] = useState([]);
    const [plans, setPlans] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isScanning, setIsScanning] = useState(false);

    const fetchHubData = async () => {
        try {
            const [macroRes, oppRes, journalRes, plansRes, statusRes] = await Promise.all([
                api.get('/macro/indicators'),
                api.get('/analysis/discover'),
                api.get('/journal/entries'),
                api.get('/journal/plans'),
                api.get('/analysis/discover/status')
            ]);
            setMacro(macroRes.data);
            setOpportunities(oppRes.data);
            setJournal(journalRes.data);
            setPlans(plansRes.data);
            setIsScanning(statusRes.data.is_scanning);
        } catch (err) {
            console.error("Hub data fetch failed", err);
        }
        setLoading(false);
    };

    useEffect(() => {
        fetchHubData();

        // Status Polling Interval
        const interval = setInterval(async () => {
            try {
                const res = await api.get('/analysis/discover/status');
                const currentlyScanning = res.data.is_scanning;

                // If a scan just finished, refresh the data
                if (isScanning && !currentlyScanning) {
                    fetchHubData();
                }

                setIsScanning(currentlyScanning);
            } catch (err) {
                console.error("Status poll failed", err);
            }
        }, 3000); // Check every 3 seconds

        return () => clearInterval(interval);
    }, [isScanning]);

    const handleTriggerScan = async () => {
        if (isScanning) return;
        try {
            setIsScanning(true);
            await api.post('/analysis/discover/scan');
        } catch (err) {
            console.error("Failed to trigger scan", err);
            setIsScanning(false);
        }
    };

    if (loading) return <div className="p-10 text-center animate-pulse text-gray-500">Initializing Cockpit Instruments...</div>;

    return (
        <div className="space-y-8 pb-20">
            {/* 1. Header & Navigation */}
            <header className="flex justify-between items-center">
                <div>
                    <h1 className="text-4xl font-black bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                        TRADING COCKPIT (W1)
                    </h1>
                    <p className="text-gray-400 flex items-center gap-2 mt-1">
                        <Compass size={14} /> Institutional Weekly Strategy Mode
                    </p>
                </div>
            </header>

            {/* 2. Macro Heatmap (Radar) */}
            <section className="grid grid-cols-2 md:grid-cols-6 gap-4">
                {macro && Object.entries(macro).map(([key, data]) => (
                    <div key={key} className={`bg-surface p-4 rounded-xl border border-gray-700 ${data.sentiment === 'BEARISH' ? 'border-l-4 border-l-danger' : 'border-l-4 border-l-success'}`}>
                        <div className="text-[10px] uppercase font-bold text-gray-500">{key}</div>
                        <div className="text-xl font-bold text-white">{data.value}</div>
                        <div className={`text-[10px] font-bold flex items-center gap-1 ${data.change_1w_pct >= 0 ? 'text-success' : 'text-danger'}`}>
                            {data.change_1w_pct >= 0 ? <ArrowUpRight size={10} /> : <ArrowDownRight size={10} />}
                            {data.change_1w_pct}% (1w)
                        </div>
                    </div>
                ))}
            </section>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                {/* 3. Discovery Engine (The List) */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="bg-surface rounded-2xl border border-gray-700 p-6">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xl font-bold flex items-center gap-2">
                                <BrainCircuit className="text-primary" /> Alpha Discovery Grid
                            </h3>
                            <div className="flex items-center gap-4">
                                <button
                                    onClick={handleTriggerScan}
                                    disabled={isScanning}
                                    className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${isScanning
                                            ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
                                            : 'bg-primary/20 text-primary hover:bg-primary/30 border border-primary/30'
                                        }`}
                                >
                                    <Activity size={12} className={isScanning ? 'animate-spin' : ''} />
                                    {isScanning ? 'SCANNING MARKETS...' : 'SCAN MARKET'}
                                </button>
                                <span className="text-xs bg-primary/10 text-primary px-3 py-1 rounded-full border border-primary/20">
                                    {opportunities.length} Setups Found
                                </span>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {opportunities.length === 0 ? (
                                <div className="col-span-2 py-10 text-center text-gray-500 border-2 border-dashed border-gray-800 rounded-xl">
                                    No explosive setups found today. Keep scanning.
                                </div>
                            ) : (
                                opportunities.map((opp, idx) => (
                                    <div key={idx} className="bg-background/40 p-4 rounded-xl border border-gray-800 hover:border-primary/50 transition-all cursor-pointer group">
                                        <div className="flex justify-between items-start mb-2">
                                            <div className="text-2xl font-black group-hover:text-primary transition-colors">{opp.ticker}</div>
                                            <div className="flex flex-col items-end">
                                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${opp.action === 'BUY' ? 'bg-success/20 text-success' : 'bg-danger/20 text-danger'}`}>
                                                    {opp.action}
                                                </span>
                                                <span className="text-xs text-gray-500 mt-1">RS: {opp.rs_rating || '--'}/100</span>
                                            </div>
                                        </div>

                                        <div className="flex gap-2 flex-wrap mt-3">
                                            {opp.is_vcp && <span className="text-[10px] bg-accent/20 text-accent font-bold px-2 py-0.5 rounded border border-accent/30">VCP COMPRESSION</span>}
                                            {opp.is_blue_sky && <span className="text-[10px] bg-blue-500/20 text-blue-400 font-bold px-2 py-0.5 rounded border border-blue-500/30">BLUE SKY</span>}
                                            {opp.has_super_trend && <span className="text-[10px] bg-success/20 text-success font-bold px-2 py-0.5 rounded border border-success/30">SUPER TREND</span>}
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                    {/* 4. Behavioral Journal (Anti-Bias) */}
                    <div className="bg-surface rounded-2xl border border-gray-700 p-6">
                        <h3 className="text-xl font-bold flex items-center gap-2 mb-6 text-yellow-500">
                            <ShieldAlert /> Mental Execution Log
                        </h3>
                        <div className="space-y-4">
                            {journal.slice(0, 5).map((entry, i) => (
                                <div key={i} className="flex gap-4 items-start border-l-2 border-gray-700 pl-4 py-2 hover:bg-white/5 rounded-r-lg transition-colors">
                                    <div className="bg-gray-800 p-2 rounded text-gray-400">
                                        {entry.action === 'ENTRY' ? <ArrowUpRight size={18} /> : <ArrowDownRight size={18} />}
                                    </div>
                                    <div className="flex-1">
                                        <div className="flex justify-between">
                                            <span className="font-bold text-white">{entry.ticker} {entry.action}</span>
                                            <span className="text-xs text-gray-500">{new Date(entry.date_logged).toLocaleDateString()}</span>
                                        </div>
                                        <p className="text-sm text-gray-400 mt-1 italic">"{entry.bias_check}"</p>
                                        <div className="flex items-center gap-2 mt-2">
                                            <span className="text-[10px] bg-white/10 px-2 py-0.5 rounded text-gray-300">State: {entry.emotional_state}</span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* 5. Right Sidebar (Active Plans & Probability) */}
                <div className="space-y-6">
                    <div className="bg-surface rounded-2xl border border-gray-700 p-6 border-t-4 border-t-primary">
                        <h3 className="text-xl font-bold flex items-center gap-2 mb-4">
                            <Target className="text-primary" /> Active Trade Plans
                        </h3>
                        <div className="space-y-4">
                            {plans.filter(p => p.is_locked).map((plan, i) => (
                                <div key={i} className="p-4 bg-background/50 rounded-xl border border-gray-800 relative group overflow-hidden">
                                    <div className="absolute top-2 right-2 text-primary">
                                        <Lock size={12} />
                                    </div>
                                    <div className="text-lg font-bold text-white mb-2">{plan.ticker}</div>
                                    <div className="flex justify-between text-xs text-gray-400">
                                        <span>Target: <span className="text-success">${plan.target_price}</span></span>
                                        <span>Stop: <span className="text-danger">${plan.stop_loss}</span></span>
                                    </div>
                                    {/* Probability Bar (Fake/Placeholder for now, will connect to Monte Carlo) */}
                                    <div className="mt-3">
                                        <div className="flex justify-between text-[10px] mb-1">
                                            <span className="text-gray-500">Prob. Success (MC)</span>
                                            <span className="text-primary font-bold">64%</span>
                                        </div>
                                        <div className="w-full bg-gray-800 h-1.5 rounded-full overflow-hidden">
                                            <div className="bg-primary h-full" style={{ width: '64%' }}></div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="bg-background rounded-2xl border border-gray-700 p-6 flex flex-col items-center justify-center text-center py-10">
                        <Activity className="text-gray-500 mb-2" size={32} />
                        <h4 className="text-gray-400 font-bold">Market correlation scan</h4>
                        <p className="text-xs text-gray-500 mt-2">DXY/SPY inverse correlation is strengthening. Caution on High-PE Tech.</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TradingHub;
