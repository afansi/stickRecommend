import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api';
import { ArrowLeft, TrendingUp, FileText, CheckCircle, AlertTriangle, Radar } from 'lucide-react';

const StockDetail = () => {
    const { ticker } = useParams();
    const [data, setData] = useState(null);
    const [technicals, setTechnicals] = useState(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    const fetchData = async (force = false) => {
        if (force) setRefreshing(true);
        try {
            // Fetch Analysis (with force flag) & Technicals in parallel
            const [analysisRes, techRes] = await Promise.all([
                api.post(`/analysis/${ticker}?force_refresh=${force}`),
                api.get(`/analysis/${ticker}/technicals`)
            ]);
            setData(analysisRes.data);
            setTechnicals(techRes.data);
        } catch (err) {
            console.error(err);
        }
        setLoading(false);
        setRefreshing(false);
    };

    const hasFetched = React.useRef(false);
    useEffect(() => {
        if (hasFetched.current) return;
        hasFetched.current = true;
        fetchData(false); // Default to cached view
    }, [ticker]);

    if (loading) return <div className="text-center p-10 text-gray-400">Analyzing Market Data for {ticker}...</div>;

    return (
        <div className="max-w-4xl mx-auto space-y-6 pb-20">
            <div className="flex justify-between items-center mb-4">
                <Link to="/" className="flex items-center gap-2 text-gray-400 hover:text-white">
                    <ArrowLeft size={18} /> Back to Dashboard
                </Link>
                <button
                    onClick={() => fetchData(true)}
                    disabled={refreshing}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg border border-primary/50 text-primary hover:bg-primary/10 transition-colors bg-surface ${refreshing ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                    <Radar size={18} className={refreshing ? "animate-spin" : ""} />
                    {refreshing ? "Rerunning AI Analysis..." : "Rerunning Analysis"}
                </button>
            </div>

            <header className="flex justify-between items-start">
                <div>
                    <h1 className="text-4xl font-bold text-white mb-2">{ticker}</h1>
                    {technicals && (
                        <div className="flex gap-4 items-center">
                            <span className={`px-2 py-0.5 rounded text-xs font-bold ${technicals.trend === 'BULLISH' ? 'bg-success/20 text-success border border-success' : technicals.trend === 'BEARISH' ? 'bg-danger/20 text-danger border border-danger' : 'bg-gray-700 text-gray-300 border border-gray-600'
                                }`}>
                                {technicals.trend} TREND
                            </span>
                            <span className="text-xl font-medium text-gray-400">${technicals.current_price}</span>
                        </div>
                    )}
                </div>
                {data && (
                    <div className={`px-4 py-2 rounded-lg border ${data.action === 'BUY' ? 'bg-success/20 border-success text-success' :
                        data.action === 'SELL' ? 'bg-danger/20 border-danger text-danger' :
                            'bg-yellow-500/20 border-yellow-500 text-yellow-500'
                        }`}>
                        <div className="text-xs font-bold uppercase tracking-wider">Bot Recommendation</div>
                        <div className="text-2xl font-bold">{data.action}</div>
                    </div>
                )}
            </header>

            {/* Technical Scorecard */}
            {technicals && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-surface rounded-xl p-4 border border-gray-700">
                        <div className="text-gray-400 text-xs mb-1">RSI (14)</div>
                        <div className={`text-xl font-bold ${technicals.rsi_14 < 30 ? 'text-success' : technicals.rsi_14 > 70 ? 'text-danger' : 'text-white'}`}>
                            {technicals.rsi_14}
                        </div>
                        <div className="text-[10px] text-gray-500 uppercase mt-1">
                            {technicals.rsi_14 < 30 ? 'Oversold' : technicals.rsi_14 > 70 ? 'Overbought' : 'Neutral'}
                        </div>
                    </div>
                    <div className="bg-surface rounded-xl p-4 border border-gray-700">
                        <div className="text-gray-400 text-xs mb-1">MACD</div>
                        <div className={`text-xl font-bold ${technicals.macd?.histogram > 0 ? 'text-success' : 'text-danger'}`}>
                            {technicals.macd?.histogram > 0 ? '+' : ''}{technicals.macd?.histogram}
                        </div>
                        <div className="text-[10px] text-gray-500 uppercase mt-1">
                            {technicals.macd?.histogram > 0 ? 'Bullish Pulse' : 'Bearish Pulse'}
                        </div>
                    </div>
                    <div className="bg-surface rounded-xl p-4 border border-gray-700">
                        <div className="text-gray-400 text-xs mb-1">Bollinger Bands</div>
                        <div className="text-sm font-bold text-white truncate">
                            {technicals.current_price > technicals.bollinger?.upper ? 'ABOVE UPPER' :
                                technicals.current_price < technicals.bollinger?.lower ? 'BELOW LOWER' : 'INSIDE BANDS'}
                        </div>
                        <div className="text-[10px] text-gray-500 uppercase mt-1">Volatility Check</div>
                    </div>
                    <div className="bg-surface rounded-xl p-4 border border-gray-700">
                        <div className="text-gray-400 text-xs mb-1">MA Trend</div>
                        <div className="text-sm font-bold text-white">
                            {technicals.ma_50} / {technicals.ma_200}
                        </div>
                        <div className="text-[10px] text-gray-500 uppercase mt-1">50D vs 200D SMA</div>
                    </div>
                </div>
            )}

            {/* AI Analysis Card */}
            {data && (
                <div className="bg-surface rounded-xl border border-gray-700 p-6 shadow-xl relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-primary/10 rounded-full blur-3xl -mr-10 -mt-10"></div>

                    <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                        <div className="bg-primary p-1.5 rounded text-white">
                            <TrendingUp size={18} />
                        </div>
                        AI Reasoning
                    </h3>

                    <div className="bg-background rounded p-6 border border-gray-700">
                        <div className="flex justify-between items-start mb-4">
                            <div className="text-gray-400 text-sm">Confidence: {data.confidence_score}/10</div>
                            <span className="text-xs text-gray-500">Generated: {new Date(data.date_generated).toLocaleString()}</span>
                        </div>
                        <p className="text-lg text-gray-200 leading-relaxed font-medium whitespace-pre-wrap">"{data.reasoning}"</p>
                    </div>
                </div>
            )}

            {/* Verified Sources */}
            <div className="bg-surface rounded-xl border border-gray-700 p-6">
                <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                    <FileText size={20} /> Verified Sources
                </h3>
                <div className="space-y-3">
                    <div className="flex items-start gap-3 p-3 hover:bg-background/50 rounded transition-colors cursor-pointer group">
                        <div className="mt-1"><CheckCircle size={16} className="text-success" /></div>
                        <div>
                            <h4 className="text-blue-400 group-hover:underline">Quarterly Earnings Report Q4</h4>
                            <p className="text-sm text-gray-400">Source: SEC.gov • Verified Impact: <span className="text-success">Positive</span></p>
                        </div>
                    </div>
                    {/* Mock More */}
                    <div className="flex items-start gap-3 p-3 hover:bg-background/50 rounded transition-colors cursor-pointer group">
                        <div className="mt-1"><AlertTriangle size={16} className="text-yellow-500" /></div>
                        <div>
                            <h4 className="text-blue-400 group-hover:underline">Analyst Downgrade by Goldman Sachs</h4>
                            <p className="text-sm text-gray-400">Source: Bloomberg • Verified Impact: <span className="text-yellow-500">Neutral</span></p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default StockDetail;
