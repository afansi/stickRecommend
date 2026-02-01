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
    const [settings, setSettings] = useState(null); // User risk settings
    const [loading, setLoading] = useState(true);
    const [isScanning, setIsScanning] = useState(false);
    const [selectedOpp, setSelectedOpp] = useState(null); // For the "Commit to Plan" modal
    const [planForm, setPlanForm] = useState({
        entry: 0,
        stop: 0,
        target: 0,
        conviction: 7,
        equity: 50000,
        risk_pct: 1.0
    });

    const fetchHubData = async () => {
        try {
            const [macroRes, oppRes, journalRes, plansRes, statusRes, settingsRes] = await Promise.all([
                api.get('/macro/indicators'),
                api.get('/analysis/discover'),
                api.get('/journal/entries'),
                api.get('/journal/plans'),
                api.get('/analysis/discover/status'),
                api.get('/users/settings')
            ]);
            setMacro(macroRes.data);
            setOpportunities(oppRes.data);
            setJournal(journalRes.data);
            setPlans(plansRes.data);
            setSettings(settingsRes.data);
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
        }, 30000); // Check every 30 seconds

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

    const handleOpenCommitModal = (opp) => {
        setSelectedOpp(opp);
        // Pre-fill with technical hints and User Risk Settings
        setPlanForm({
            entry: opp.suggested_entry || 0,
            stop: opp.suggested_stop || 0,
            target: opp.suggested_target || 0,
            conviction: 7,
            equity: settings?.total_equity || 50000,
            risk_pct: settings?.risk_pct || 1.0
        });
    };

    const handleCommitPlan = async () => {
        try {
            await api.post(`/journal/plans?ticker=${selectedOpp.ticker}&entry=${planForm.entry}&stop=${planForm.stop}&target=${planForm.target}&setup=${selectedOpp.is_vcp ? 'VCP' : 'Breakout'}&conviction=${planForm.conviction}&override_equity=${planForm.equity}&override_risk_pct=${planForm.risk_pct}`);
            setSelectedOpp(null);
            fetchHubData(); // Refresh sidebar
        } catch (err) {
            console.error("Failed to save trade plan", err);
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
                                    <div key={idx} className="bg-background/40 p-4 rounded-xl border border-gray-800 hover:border-primary/50 transition-all group relative">
                                        <div className="flex justify-between items-start mb-2">
                                            <div className="text-2xl font-black group-hover:text-primary transition-colors">{opp.ticker}</div>
                                            <div className="flex flex-col items-end">
                                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${opp.action === 'BUY' ? 'bg-success/20 text-success' : 'bg-danger/20 text-danger'}`}>
                                                    {opp.action}
                                                </span>
                                                <span className="text-xs text-gray-500 mt-1">RS: {opp.rs_rating || '--'}/100</span>
                                            </div>
                                        </div>

                                        <p className="text-xs text-gray-400 line-clamp-2 mb-3 leading-relaxed">
                                            {opp.reasoning}
                                        </p>

                                        <div className="flex justify-between items-end">
                                            <div className="flex gap-2 flex-wrap">
                                                {opp.is_vcp && <span className="text-[10px] bg-accent/20 text-accent font-bold px-2 py-0.5 rounded border border-accent/30">VCP</span>}
                                                {opp.is_blue_sky && <span className="text-[10px] bg-blue-500/20 text-blue-400 font-bold px-2 py-0.5 rounded border border-blue-500/30">BREAKOUT</span>}
                                            </div>
                                            <button
                                                onClick={() => handleOpenCommitModal(opp)}
                                                className="text-[10px] bg-primary text-black font-bold px-3 py-1 rounded hover:bg-primary/80 transition-all opacity-0 group-hover:opacity-100 flex items-center gap-1"
                                            >
                                                <Target size={10} /> COMMIT TO PLAN
                                            </button>
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
                                    <div className="text-lg font-bold text-white mb-1">{plan.ticker}</div>
                                    <div className="flex flex-col gap-1 mb-3">
                                        <div className="flex justify-between text-xs text-gray-400">
                                            <span>Target: <span className="text-success">${plan.target_price}</span></span>
                                            <span>Stop: <span className="text-danger">${plan.stop_loss}</span></span>
                                        </div>
                                        <div className="flex justify-between text-[10px] text-gray-500 bg-gray-900/50 p-1.5 rounded mt-1 border border-gray-800">
                                            <span>R-Manager: <b className="text-primary">{plan.num_shares || 0} Shares</b></span>
                                            <span>Risk: <b className="text-danger">${plan.risk_amount || 0}</b></span>
                                        </div>
                                    </div>

                                    {/* Monte Carlo Probability Bar */}
                                    <div className="mt-2">
                                        <div className="flex justify-between text-[10px] mb-1">
                                            <span className="text-gray-500">Prob. Success (MC)</span>
                                            <span className="text-primary font-bold">{plan.prob_success ? `${Math.round(plan.prob_success)}%` : '--'}</span>
                                        </div>
                                        <div className="w-full bg-gray-800 h-1 rounded-full overflow-hidden">
                                            <div
                                                className="bg-primary h-full transition-all duration-1000"
                                                style={{ width: `${plan.prob_success || 0}%` }}
                                            ></div>
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

            {/* --- COMMIT MODAL --- */}
            {selectedOpp && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="bg-surface border border-gray-700 rounded-3xl w-full max-w-md p-8 shadow-2xl animate-in fade-in zoom-in duration-200">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-2xl font-black text-white">REFINING PLAN: {selectedOpp.ticker}</h2>
                            <button onClick={() => setSelectedOpp(null)} className="text-gray-500 hover:text-white">✕</button>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="text-[10px] uppercase font-bold text-gray-500 block mb-1">Entry Price ($)</label>
                                <input
                                    type="number"
                                    className="w-full bg-background border border-gray-700 rounded-xl p-3 text-white focus:border-primary outline-none transition-all"
                                    value={planForm.entry}
                                    onChange={(e) => setPlanForm({ ...planForm, entry: parseFloat(e.target.value) })}
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-[10px] uppercase font-bold text-gray-500 block mb-1">Stop Loss ($)</label>
                                    <input
                                        type="number"
                                        className="w-full bg-background border border-gray-700 rounded-xl p-3 text-white focus:border-danger outline-none transition-all"
                                        value={planForm.stop}
                                        onChange={(e) => setPlanForm({ ...planForm, stop: parseFloat(e.target.value) })}
                                    />
                                </div>
                                <div>
                                    <label className="text-[10px] uppercase font-bold text-gray-500 block mb-1">Profit Target ($)</label>
                                    <input
                                        type="number"
                                        className="w-full bg-background border border-gray-700 rounded-xl p-3 text-white focus:border-success outline-none transition-all"
                                        value={planForm.target}
                                        onChange={(e) => setPlanForm({ ...planForm, target: parseFloat(e.target.value) })}
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="text-[10px] uppercase font-bold text-gray-500 block mb-1">Conviction (1-10)</label>
                                <input
                                    type="range" min="1" max="10"
                                    className="w-full accent-primary bg-background h-2 rounded-lg appearance-none cursor-pointer"
                                    value={planForm.conviction}
                                    onChange={(e) => setPlanForm({ ...planForm, conviction: parseInt(e.target.value) })}
                                />
                                <div className="text-center text-primary font-bold text-sm mt-1">{planForm.conviction}/10</div>
                            </div>

                            <div className="pt-4 border-t border-gray-800 space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-[10px] uppercase font-bold text-gray-400 block mb-1">Total Equity ($)</label>
                                        <input
                                            type="number"
                                            className="w-full bg-background/50 border border-gray-800 rounded-xl p-3 text-white text-xs outline-none focus:border-gray-600 transition-all"
                                            value={planForm.equity}
                                            onChange={(e) => setPlanForm({ ...planForm, equity: parseFloat(e.target.value) })}
                                        />
                                    </div>
                                    <div>
                                        <label className="text-[10px] uppercase font-bold text-gray-400 block mb-1">Risk per Trade (%)</label>
                                        <input
                                            type="number" step="0.1"
                                            className="w-full bg-background/50 border border-gray-800 rounded-xl p-3 text-white text-xs outline-none focus:border-gray-600 transition-all"
                                            value={planForm.risk_pct}
                                            onChange={(e) => setPlanForm({ ...planForm, risk_pct: parseFloat(e.target.value) })}
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="mt-8">
                            <button
                                onClick={handleCommitPlan}
                                className="w-full bg-primary hover:bg-primary/90 text-black font-black py-4 rounded-2xl transition-all shadow-lg shadow-primary/20 flex items-center justify-center gap-2"
                            >
                                <Lock size={18} /> INITIALIZE \u0026 LOCK TRADE PLAN
                            </button>
                            <p className="text-[10px] text-center text-gray-500 mt-4 uppercase tracking-widest">
                                Weekend Lockdown Mode: Plan will be read-only until manual execution.
                            </p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default TradingHub;
