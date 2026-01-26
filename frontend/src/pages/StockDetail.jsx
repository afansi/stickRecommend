import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api';
import { ArrowLeft, TrendingUp, FileText, CheckCircle, AlertTriangle } from 'lucide-react';

const StockDetail = () => {
    const { ticker } = useParams();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    const hasFetched = React.useRef(false);
    useEffect(() => {
        if (hasFetched.current) return;
        hasFetched.current = true;

        const fetchAnalysis = async () => {
            try {
                const res = await api.post(`/analysis/${ticker}`);
                setData(res.data);
            } catch (err) {
                console.error(err);
            }
            setLoading(false);
        };
        fetchAnalysis();
    }, [ticker]);

    if (loading) return <div className="text-center p-10 text-gray-400">Analyzing Market Data for {ticker}...</div>;

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <Link to="/" className="flex items-center gap-2 text-gray-400 hover:text-white mb-4">
                <ArrowLeft size={18} /> Back to Dashboard
            </Link>

            <header className="flex justify-between items-start">
                <div>
                    <h1 className="text-4xl font-bold text-white mb-2">{ticker}</h1>
                    <div className="flex gap-2">
                        <span className="bg-surface border border-gray-600 px-2 py-1 rounded text-sm text-gray-300">Technology</span>
                        <span className="bg-surface border border-gray-600 px-2 py-1 rounded text-sm text-gray-300">Mega Cap</span>
                    </div>
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

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                        <div className="bg-background rounded p-4 border border-gray-700">
                            <div className="text-gray-400 text-sm">Confidence</div>
                            <div className="text-2xl font-bold text-white">{data.confidence_score}/10</div>
                        </div>
                        <div className="bg-background rounded p-4 border border-gray-700 col-span-2">
                            <div className="text-gray-400 text-sm">Summary</div>
                            <p className="text-gray-200 mt-1">{data.reasoning}</p>
                        </div>
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
