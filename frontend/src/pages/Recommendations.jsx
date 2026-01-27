import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
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

    // Helper for robust date parsing (Safari compatibility)
    const formatDisplayDate = (dateStr) => {
        if (!dateStr) return 'Recent';
        try {
            const iso = dateStr.includes('T') ? dateStr : dateStr.replace(' ', 'T');
            const d = new Date(iso);
            return isNaN(d.getTime()) ? 'Recent' : d.toLocaleDateString();
        } catch (e) {
            return 'Recent';
        }
    };

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
                    {recs.sort((a, b) => (b.confidence_score || 0) - (a.confidence_score || 0)).map((rec) => (
                        <div key={rec.id} className="bg-surface p-6 rounded-xl border border-gray-700 hover:border-gray-600 transition-colors">
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <div className="flex items-center gap-3">
                                        <Link to={`/analysis/${rec.ticker}`} className="text-2xl font-bold text-white hover:text-primary transition-colors">
                                            {rec.ticker}
                                        </Link>
                                        <span className="text-gray-400 font-medium">{rec.company_name}</span>
                                        <span className={`px-2 py-1 rounded text-xs font-bold ${rec.action === 'BUY' ? 'bg-green-500/20 text-green-400' :
                                            rec.action === 'SELL' ? 'bg-red-500/20 text-red-400' :
                                                'bg-gray-500/20 text-gray-400'
                                            }`}>
                                            {rec.action}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-2 mt-1 text-gray-500 text-sm">
                                        <Clock size={14} />
                                        <span>{formatDisplayDate(rec.date_generated)}</span>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className="text-3xl font-bold text-primary">{rec.confidence_score || 0}</div>
                                    <span className="text-xs text-gray-500">Confidence</span>
                                </div>
                            </div>

                            <div className="bg-background/50 p-4 rounded-lg border border-white/5 space-y-3">
                                <div>
                                    <h4 className="text-sm font-semibold text-gray-300 mb-1 flex items-center gap-2">
                                        <TrendingUp size={16} className="text-accent" /> Analysis Summary
                                    </h4>
                                    <p className="text-gray-400 text-sm leading-relaxed whitespace-pre-wrap">
                                        {rec.reasoning}
                                    </p>
                                </div>

                                {rec.source_news_url && (
                                    <div className="pt-2 border-t border-white/5">
                                        <a
                                            href={rec.source_news_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-xs text-primary hover:text-white transition-colors flex items-center gap-1"
                                        >
                                            View Source News Article →
                                        </a>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default Recommendations;

