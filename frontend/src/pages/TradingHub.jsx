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
    const [correlations, setCorrelations] = useState(null);
    const [opportunities, setOpportunities] = useState([]);
    const [journal, setJournal] = useState([]);
    const [plans, setPlans] = useState([]);
    const [latestReview, setLatestReview] = useState(null);
    const [settings, setSettings] = useState(null); // User risk settings
    const [loading, setLoading] = useState(true);
    const [isScanning, setIsScanning] = useState(false);
    const [scanStatus, setScanStatus] = useState({ phase: 'idle', current: 0, total: 0, message: '' });
    const [selectedOpp, setSelectedOpp] = useState(null); // For the "Commit to Plan" modal
    const [journalModal, setJournalModal] = useState(null); // For the "Log Trade" modal
    const [planForm, setPlanForm] = useState({
        entry: 0,
        stop: 0,
        target: 0,
        conviction: 7,
        equity: 50000,
        risk_pct: 1.0
    });
    const [journalForm, setJournalForm] = useState({
        action: 'ENTRY',
        price: 0,
        emotion: 'Calm',
        notes: ''
    });

    const fetchHubData = async () => {
        try {
            const [macroRes, corrRes, oppRes, journalRes, plansRes, statusRes, settingsRes, reviewRes] = await Promise.all([
                api.get('/macro/indicators'),
                api.get('/macro/correlations'),
                api.get('/analysis/discover'),
                api.get('/journal/entries'),
                api.get('/journal/plans'),
                api.get('/analysis/discover/status'),
                api.get('/users/settings'),
                api.get('/reporting/latest-review').catch(() => ({ data: null }))
            ]);
            setMacro(macroRes.data);
            setCorrelations(corrRes.data);
            setOpportunities(oppRes.data);
            setJournal(journalRes.data);
            setPlans(plansRes.data);
            setSettings(settingsRes.data);
            setLatestReview(reviewRes.data);
            setIsScanning(statusRes.data.is_scanning);
            setScanStatus(statusRes.data);
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
                setScanStatus(res.data);

                // If a scan just finished, refresh the data
                if (isScanning && !currentlyScanning) {
                    fetchHubData();
                }

                setIsScanning(currentlyScanning);
            } catch (err) {
                console.error("Status poll failed", err);
            }
        }, isScanning ? 3000 : 30000); // Check every 3 seconds during scan, 30s otherwise

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

    const handleOpenJournalModal = (plan) => {
        setJournalModal(plan);
        setJournalForm({
            action: 'ENTRY',
            price: plan.entry_price || 0,
            emotion: 'Calm',
            notes: ''
        });
    };

    const handleLogExecution = async () => {
        try {
            await api.post(`/journal/execute?ticker=${journalModal.ticker}&action=${journalForm.action}&price=${journalForm.price}&emotion=${journalForm.emotion}&bias_note=${encodeURIComponent(journalForm.notes)}`);
            setJournalModal(null);
            fetchHubData(); // Refresh journal list
        } catch (err) {
            console.error("Failed to log execution", err);
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

                        {/* Progress Display */}
                        {isScanning && (
                            <div className="mb-6 p-4 bg-background/60 rounded-xl border border-primary/20 animate-in fade-in slide-in-from-top-4 duration-500">
                                <div className="flex justify-between items-center mb-2">
                                    <div className="flex items-center gap-2">
                                        <div className="relative">
                                            <Activity size={16} className="text-primary animate-pulse" />
                                            <div className="absolute inset-0 bg-primary/20 blur-md rounded-full animate-pulse"></div>
                                        </div>
                                        <span className="text-xs font-bold text-gray-300 uppercase tracking-widest">
                                            {scanStatus.phase === 'retrieval' && '🛰️ Phase 1: Index Scraping'}
                                            {scanStatus.phase === 'liquidity' && '🌊 Phase 2: Liquidity Gate'}
                                            {scanStatus.phase === 'screening' && '⚙️ Phase 3: Technical Screening'}
                                            {scanStatus.phase === 'analysis' && '🧠 Phase 4: AI Deep Analysis'}
                                        </span>
                                    </div>
                                    <span className="text-[10px] font-mono text-primary font-bold">
                                        {scanStatus.total > 0 ? `${Math.round((scanStatus.current / scanStatus.total) * 100)}%` : 'INIT...'}
                                    </span>
                                </div>

                                <div className="h-1.5 w-full bg-gray-800 rounded-full overflow-hidden border border-gray-700/50">
                                    <div
                                        className="h-full bg-gradient-to-r from-blue-500 to-primary transition-all duration-700 ease-out shadow-[0_0_10px_rgba(59,130,246,0.5)]"
                                        style={{ width: `${scanStatus.total > 0 ? (scanStatus.current / scanStatus.total) * 100 : 5}%` }}
                                    ></div>
                                </div>

                                <div className="mt-2 flex justify-between items-center">
                                    <p className="text-[10px] text-gray-500 italic flex items-center gap-1">
                                        <TrendingUp size={10} /> {scanStatus.message || 'Initializing systems...'}
                                    </p>
                                    {scanStatus.total > 0 && (
                                        <span className="text-[10px] text-gray-400 font-bold">
                                            {scanStatus.current} / {scanStatus.total}
                                        </span>
                                    )}
                                </div>
                            </div>
                        )}

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
                                                {opp.is_decoupled && (
                                                    <span className="text-[10px] bg-primary/20 text-primary font-bold px-2 py-0.5 rounded border border-primary/50 flex items-center gap-1 animate-pulse">
                                                        <BrainCircuit size={10} /> ALPHA DECOUPLING
                                                    </span>
                                                )}
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
                            {plans.map((plan, i) => (
                                <div key={i} className="p-4 bg-background/50 rounded-xl border border-gray-800 relative group overflow-hidden">
                                    <div className="absolute top-2 right-2 flex gap-1">
                                        {plan.is_locked ? (
                                            <div className="text-primary" title="Locked Weekend Plan">
                                                <Lock size={12} />
                                            </div>
                                        ) : (
                                            <div className="text-gray-500" title="Unlocked/Intra-week Plan">
                                                <Activity size={12} />
                                            </div>
                                        )}
                                    </div>
                                    <div className="text-lg font-bold text-white mb-1">{plan.ticker}</div>

                                    {/* Unlocking Logic Info */}
                                    <div className="mb-2">
                                        {(() => {
                                            const today = new Date();
                                            const planned = new Date(plan.date_planned);
                                            const daysHeld = Math.floor((today - planned) / (1000 * 60 * 60 * 24));
                                            const durationDays = (plan.expected_duration_weeks || 4) * 7;
                                            const isWeekend = today.getDay() === 0 || today.getDay() === 6;
                                            const isUnlocked = !plan.is_locked || isWeekend || daysHeld >= durationDays;

                                            if (plan.is_locked && !isWeekend && daysHeld < durationDays) {
                                                return (
                                                    <div className="text-[9px] text-yellow-500 font-bold uppercase tracking-widest flex items-center gap-1">
                                                        <Lock size={10} /> Locked until weekend or {durationDays - daysHeld} days
                                                    </div>
                                                );
                                            } else if (plan.is_locked) {
                                                return (
                                                    <div className="text-[9px] text-success font-bold uppercase tracking-widest flex items-center gap-1">
                                                        <Activity size={10} /> Plan Unlocked for Execution
                                                    </div>
                                                );
                                            }
                                            return null;
                                        })()}
                                    </div>

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

                                    <button
                                        onClick={() => handleOpenJournalModal(plan)}
                                        className="w-full mt-3 bg-white/5 hover:bg-white/10 border border-gray-700 hover:border-gray-600 text-[10px] font-bold py-1.5 rounded transition-all uppercase tracking-widest text-gray-300"
                                    >
                                        Log Execution
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="bg-surface rounded-2xl border border-gray-700 p-6">
                        <h3 className="text-xl font-bold flex items-center gap-2 mb-6">
                            <Activity className="text-primary" /> Inter-Market Correlations
                        </h3>
                        <div className="grid grid-cols-2 gap-4">
                            {correlations && Object.entries(correlations)
                                .filter(([key]) => key !== 'SPY')
                                .map(([key, value]) => (
                                    <div key={key} className="bg-background/40 p-3 rounded-xl border border-gray-800 flex justify-between items-center">
                                        <div>
                                            <div className="text-[10px] text-gray-500 font-bold uppercase">{key}</div>
                                            <div className="text-xs text-gray-400">vs SP500</div>
                                        </div>
                                        <div className="text-right">
                                            <div className={`text-lg font-black ${Math.abs(value) > 0.7 ? 'text-primary' : 'text-white'}`}>
                                                {value > 0 ? `+${value}` : value}
                                            </div>
                                            <div className="text-[8px] uppercase font-bold text-gray-600">r-coeff</div>
                                        </div>
                                    </div>
                                ))
                            }
                        </div>
                        <p className="text-[10px] text-gray-500 mt-6 uppercase tracking-widest leading-relaxed text-center px-4">
                            Values &gt; 0.70 indicate strong directional lock. Inverse correlations (negative) are critical for risk hedging.
                        </p>
                    </div>
                </div>
            </div>

            {/* 6. Institutional Weekend Review */}
            {
                plans.length > 0 && (
                    <section className="bg-surface rounded-2xl border border-gray-700 p-8 border-t-4 border-t-yellow-500">
                        <div className="flex justify-between items-start mb-8">
                            <div>
                                <h3 className="text-2xl font-black flex items-center gap-3 text-white">
                                    <Calendar className="text-yellow-500" /> Weekend Performance Post-Mortem
                                </h3>
                                <p className="text-gray-500 text-sm mt-1">Closing analysis, Risk audit, and psychological archiving.</p>
                            </div>
                            <button
                                onClick={async () => {
                                    try {
                                        await api.post('/reporting/generate-weekend-review');
                                        fetchHubData();
                                    } catch (err) {
                                        alert("Review generation failed. Ensure you have active trade plans.");
                                    }
                                }}
                                className="bg-yellow-500 hover:bg-yellow-400 text-black font-bold px-6 py-2 rounded-xl transition-all shadow-lg shadow-yellow-500/20 text-sm"
                            >
                                GENERATE NEW REVIEW
                            </button>
                        </div>

                        {latestReview ? (
                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                                {/* Summary Stats */}
                                <div className="lg:col-span-1 space-y-6">
                                    <div className="bg-background/40 p-6 rounded-2xl border border-gray-800">
                                        <div className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mb-4">Portfolio Exposure</div>
                                        <div className="text-3xl font-black text-white">${latestReview.total_exposure?.toLocaleString()}</div>
                                        <div className="mt-4 flex items-center justify-between">
                                            <span className="text-xs text-gray-400">Cumulative Risk</span>
                                            <span className={`text-xs font-bold px-3 py-1 rounded-full ${latestReview.risk_verdict === 'Acceptable' ? 'bg-success/20 text-success' : 'bg-danger/20 text-danger'}`}>
                                                {latestReview.cumulative_risk_pct?.toFixed(2)}%
                                            </span>
                                        </div>
                                        <div className="mt-6 pt-6 border-t border-gray-800">
                                            <div className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mb-2">Review Status</div>
                                            <div className="flex items-center gap-2 text-sm text-yellow-500 font-bold">
                                                <ShieldAlert size={16} /> {latestReview.risk_verdict} Risk Mode
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* LLM Feedback */}
                                <div className="lg:col-span-2 bg-background/20 p-8 rounded-2xl border border-gray-800 prose prose-invert prose-sm max-w-none">
                                    <div className="flex items-center gap-2 text-primary font-bold uppercase tracking-widest text-[10px] mb-4">
                                        <BrainCircuit size={14} /> Institutional AI Verdict
                                    </div>
                                    <div className="text-gray-300 leading-relaxed whitespace-pre-wrap font-mono uppercase text-[12px]">
                                        {latestReview.global_market_analysis}
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="bg-background/20 py-16 text-center rounded-2xl border border-gray-800 border-dashed">
                                <Activity className="mx-auto text-gray-700 mb-4" size={48} />
                                <h4 className="text-gray-500 font-bold text-lg">No Weekend Review Generated Yet</h4>
                                <p className="text-gray-600 text-sm mt-2">Generate a post-mortem to analyze your weekly performance and risk.</p>
                            </div>
                        )}
                    </section>
                )
            }

            {/* --- COMMIT MODAL --- */}
            {
                selectedOpp && (
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
                )
            }

            {/* --- JOURNAL MODAL --- */}
            {
                journalModal && (
                    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                        <div className="bg-surface border border-gray-700 rounded-3xl w-full max-w-md p-8 shadow-2xl animate-in fade-in zoom-in duration-200">
                            <div className="flex justify-between items-center mb-6">
                                <div>
                                    <h2 className="text-2xl font-black text-white">JOURNAL: {journalModal.ticker}</h2>
                                    <p className="text-[10px] text-gray-400 uppercase tracking-widest font-bold">Execution \u0026 Anti-Bias Log</p>
                                </div>
                                <button onClick={() => setJournalModal(null)} className="text-gray-500 hover:text-white">✕</button>
                            </div>

                            <div className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-[10px] uppercase font-bold text-gray-500 block mb-1">Action</label>
                                        <select
                                            className="w-full bg-background border border-gray-700 rounded-xl p-3 text-white outline-none focus:border-primary transition-all text-xs"
                                            value={journalForm.action}
                                            onChange={(e) => setJournalForm({ ...journalForm, action: e.target.value })}
                                        >
                                            <option value="ENTRY">ENTRY (BUY)</option>
                                            <option value="EXIT">EXIT (SELL)</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="text-[10px] uppercase font-bold text-gray-500 block mb-1">Price ($)</label>
                                        <input
                                            type="number"
                                            className="w-full bg-background border border-gray-700 rounded-xl p-3 text-white focus:border-primary outline-none transition-all text-xs"
                                            value={journalForm.price}
                                            onChange={(e) => setJournalForm({ ...journalForm, price: parseFloat(e.target.value) })}
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="text-[10px] uppercase font-bold text-gray-500 block mb-1">Psychological State</label>
                                    <div className="grid grid-cols-3 gap-2">
                                        {['Calm', 'Fearful', 'Greedy', 'Impulsive', 'Anxious', 'Confident'].map(state => (
                                            <button
                                                key={state}
                                                onClick={() => setJournalForm({ ...journalForm, emotion: state })}
                                                className={`text-[10px] py-2 rounded-lg border font-bold transition-all ${journalForm.emotion === state
                                                    ? 'bg-primary border-primary text-black'
                                                    : 'bg-background border-gray-800 text-gray-400 hover:border-gray-600'
                                                    }`}
                                            >
                                                {state.toUpperCase()}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                <div>
                                    <label className="text-[10px] uppercase font-bold text-gray-500 block mb-1">Bias Check / Notes</label>
                                    <textarea
                                        className="w-full bg-background border border-gray-700 rounded-xl p-3 text-white focus:border-primary outline-none transition-all text-xs h-24 resize-none"
                                        placeholder="Why are you taking this action now? Does it follow the plan?"
                                        value={journalForm.notes}
                                        onChange={(e) => setJournalForm({ ...journalForm, notes: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div className="mt-8">
                                <button
                                    onClick={handleLogExecution}
                                    className="w-full bg-white text-black font-black py-4 rounded-2xl transition-all shadow-lg hover:bg-gray-200 flex items-center justify-center gap-2"
                                >
                                    <Target size={18} /> COMMIT TO JOURNAL
                                </button>
                                <p className="text-[10px] text-center text-gray-500 mt-4 uppercase tracking-widest leading-relaxed">
                                    Anti-Bias engine will now cross-reference this against your locked weekend plan.
                                </p>
                            </div>
                        </div>
                    </div>
                )
            }
        </div >
    );
};

export default TradingHub;
