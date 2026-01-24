import React, { useEffect, useState } from 'react';
import api from '../api';
import { TrendingUp, AlertCircle, Clock } from 'lucide-react';

const Recommendations = () => {
    const [recs, setRecs] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchRecs = async () => {
            try {
                const res = await api.get('/analysis/recommendations');
                setRecs(res.data);
            } catch (err) {
                console.error(err);
            }
            setLoading(false);
        };
        fetchRecs();
    }, []);

    if (loading) return <div className="text-white">Loading recommendations...</div>;

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <h2 className="text-3xl font-bold text-white mb-8">Active Recommendations</h2>

            {recs.length === 0 ? (
                <div className="bg-surface p-12 rounded-xl border border-gray-700 text-center">
                    <p className="text-gray-400 text-lg">No active recommendations found.</p>
                    <p className="text-gray-500">Analyze a stock to generate trading signals.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 gap-4">
                    {recs.sort((a, b) => b.confidence_score - a.confidence_score).map((rec) => (
                        <div key={rec.id} className="bg-surface p-6 rounded-xl border border-gray-700 hover:border-gray-600 transition-colors">
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <div className="flex items-center gap-3">
                                        <h3 className="text-2xl font-bold text-white">{rec.ticker}</h3>
                                        <span className={`px-2 py-1 rounded text-xs font-bold ${rec.action === 'BUY' ? 'bg-green-500/20 text-green-400' :
                                                rec.action === 'SELL' ? 'bg-red-500/20 text-red-400' :
                                                    'bg-gray-500/20 text-gray-400'
                                            }`}>
                                            {rec.action}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-2 mt-1 text-gray-500 text-sm">
                                        <Clock size={14} />
                                        <span>{new Date(rec.date_generated).toLocaleDateString()}</span>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className="text-3xl font-bold text-primary">{rec.confidence_score}</div>
                                    <span className="text-xs text-gray-500">Confidence</span>
                                </div>
                            </div>

                            <div className="bg-background/50 p-4 rounded-lg border border-white/5">
                                <h4 className="text-sm font-semibold text-gray-300 mb-1 flex items-center gap-2">
                                    <TrendingUp size={16} className="text-accent" /> Analysis Summary
                                </h4>
                                <p className="text-gray-400 text-sm leading-relaxed">
                                    {rec.reasoning}
                                </p>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default Recommendations;
