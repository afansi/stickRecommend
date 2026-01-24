import React, { useEffect, useState } from 'react';
import api from '../api';
import { TrendingUp, AlertTriangle, Activity, Radar } from 'lucide-react';

const Dashboard = () => {
    // Mock Data for "Premium" Feel (In prod, fetch these from backend endpoints)
    const stats = {
        portfolioValue: "$45,200",
        dailyChange: "+1.2%",
        fearIndex: "65 (Greed)"
    };

    const [news, setNews] = useState([]);
    const [recommendations, setRecommendations] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [loadingNews, setLoadingNews] = useState(true);
    const [scanning, setScanning] = useState(false);

    const fetchRecommendations = async () => {
        try {
            const recsRes = await api.get('/analysis/recommendations');
            setRecommendations(recsRes.data);
        } catch (err) {
            console.error("Failed to load recommendations", err);
        }
    };

    const fetchAlerts = async () => {
        try {
            const alertsRes = await api.get('/alerts');
            setAlerts(alertsRes.data);
        } catch (err) {
            console.error("Failed to load alerts", err);
        }
    };

    const handleAlertClick = async (alertId) => {
        try {
            await api.patch(`/alerts/${alertId}/read`);
            await fetchAlerts();
        } catch (err) {
            console.error("Failed to mark alert as read", err);
        }
    };

    useEffect(() => {
        const fetchData = async () => {
            try {
                // Fetch News
                const newsRes = await api.get('/users/news');
                setNews(newsRes.data);

                await fetchRecommendations();
                await fetchAlerts();

            } catch (err) {
                console.error("Failed to load dashboard data", err);
            }
            setLoadingNews(false);
        };
        fetchData();
    }, []);

    const handleScan = async () => {
        setScanning(true);
        try {
            const res = await api.post('/analysis/scan');
            if (res.data.new_recommendations > 0) {
                alert(`Scan Complete! Found ${res.data.new_recommendations} new opportunities.`);
                await fetchRecommendations();
                await fetchAlerts();
            } else {
                alert("Scan Complete. No new strong buy signals found in your sectors.");
            }
        } catch (err) {
            alert("Scan failed to trigger.");
            console.error(err);
        }
        setScanning(false);
    };

    return (
        <div className="space-y-6">
            <header className="flex justify-between items-center mb-8">
                <div>
                    <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                        Mission Control
                    </h2>
                    <p className="text-gray-400">Market Status: <span className="text-success">OPEN</span></p>
                </div>

                <button
                    onClick={handleScan}
                    disabled={scanning}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold transition-all ${scanning
                        ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                        : 'bg-accent/20 text-accent hover:bg-accent hover:text-white border border-accent/50'
                        }`}
                >
                    <Radar size={20} className={scanning ? "animate-spin" : ""} />
                    {scanning ? "Scanning..." : "Scan Market"}
                </button>
            </header>

            {/* Widgets Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Widget 1: Health */}
                <div className="bg-surface p-6 rounded-xl border border-gray-700 shadow-lg relative overflow-hidden group hover:border-primary/50 transition-colors">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <TrendingUp size={64} />
                    </div>
                    <div className="flex items-center gap-2 mb-2">
                        <Activity className="text-primary" size={20} />
                        <h3 className="text-gray-400 font-medium">Portfolio Health</h3>
                    </div>
                    <div className="text-3xl font-bold text-white mb-1">{stats.portfolioValue}</div>
                    <div className="text-success text-sm bg-success/10 inline-block px-2 py-1 rounded">
                        {stats.dailyChange} Today
                    </div>
                </div>

                {/* Widget 2: Action Items */}
                <div className="bg-surface p-6 rounded-xl border border-gray-700 shadow-lg hover:border-accent/50 transition-colors">
                    <div className="flex items-center gap-2 mb-4">
                        <AlertTriangle className="text-accent" size={20} />
                        <h3 className="text-gray-400 font-medium">Smart Alerts</h3>
                    </div>
                    <div className="space-y-3">
                        {alerts.length === 0 ? (
                            <p className="text-gray-500 text-sm">No active alerts</p>
                        ) : (
                            alerts.slice(0, 3).map((alert) => (
                                <div
                                    key={alert.id}
                                    onClick={() => handleAlertClick(alert.id)}
                                    className="flex justify-between items-start border-b border-gray-700 pb-2 last:border-0 cursor-pointer hover:bg-gray-800 p-2 rounded transition-colors"
                                >
                                    <div>
                                        <span className="text-white font-semibold">{alert.ticker}</span>
                                        <p className="text-xs text-gray-400">{alert.message}</p>
                                    </div>
                                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${alert.severity === 'HIGH' ? 'text-red-400 bg-red-500/10' :
                                            alert.severity === 'MEDIUM' ? 'text-yellow-500 bg-yellow-500/10' :
                                                'text-gray-400 bg-gray-500/10'
                                        }`}>{alert.severity}</span>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {/* Widget 3: Top Recommendations */}
                <div className="bg-gradient-to-br from-surface to-background p-6 rounded-xl border border-gray-700 shadow-lg flex flex-col h-full">
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="text-gray-400 font-medium">Top Recommendations</h3>
                        <a href="/recommendations" className="text-primary text-xs hover:text-white transition-colors">View All</a>
                    </div>

                    {recommendations.length === 0 ? (
                        <div className="flex-1 flex flex-col items-center justify-center text-gray-500">
                            <p>No active signals.</p>
                            <span className="text-xs">Analyze a stock to see it here.</span>
                        </div>
                    ) : (
                        <div className="space-y-4 flex-1">
                            {recommendations.sort((a, b) => b.confidence_score - a.confidence_score).slice(0, 3).map((rec, i) => (
                                <div key={i} className="border-b border-gray-700 last:border-0 pb-3 last:pb-0">
                                    <div className="flex justify-between items-center mb-1">
                                        <div>
                                            <div className="flex items-center gap-2">
                                                <h4 className="text-xl font-bold text-white">{rec.ticker}</h4>
                                                <span className="text-[10px] text-gray-500">
                                                    {(() => {
                                                        const diff = (new Date() - new Date(rec.date_generated)) / 1000;
                                                        if (diff < 60) return 'Just now';
                                                        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
                                                        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
                                                        return `${Math.floor(diff / 86400)}d ago`;
                                                    })()}
                                                </span>
                                            </div>
                                            <span className={`text-xs px-1.5 py-0.5 rounded font-bold ${rec.action === 'BUY' ? 'bg-green-500/20 text-green-400' : rec.action === 'SELL' ? 'bg-red-500/20 text-red-400' : 'bg-gray-500/20 text-gray-400'}`}>
                                                {rec.action}
                                            </span>
                                        </div>
                                        <div className="text-right">
                                            <div className="text-xl font-bold text-primary">{rec.confidence_score}</div>
                                            <span className="text-[10px] text-gray-500">Score</span>
                                        </div>
                                    </div>
                                    <p className="text-xs text-gray-400 line-clamp-2">{rec.reasoning}</p>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Live News Stream */}
            <div className="bg-surface rounded-xl border border-gray-700 p-6">
                <h3 className="text-xl font-bold text-white mb-4">Your Personalized News Feed</h3>
                {loadingNews ? (
                    <p className="text-gray-500">Loading tailored news...</p>
                ) : (
                    <div className="space-y-4">
                        {news.length === 0 && <p className="text-gray-500">No news found for your active sectors.</p>}
                        {news.map((item, idx) => (
                            <a key={idx} href={item.link} target="_blank" rel="noopener noreferrer" className="flex gap-4 items-start p-3 hover:bg-gray-800 rounded-lg transition-colors cursor-pointer group">
                                <div className="w-2 h-2 rounded-full bg-blue-500 mt-2 flex-shrink-0"></div>
                                <div className="flex-1">
                                    <h4 className="text-white font-medium group-hover:text-primary transition-colors">{item.title}</h4>

                                    {/* Related Tickers (The Discovery Lead) */}
                                    {item.relatedTickers && item.relatedTickers.length > 0 && (
                                        <div className="flex flex-wrap gap-2 mt-2">
                                            {item.relatedTickers.slice(0, 4).map(ticker => (
                                                <span
                                                    key={ticker}
                                                    onClick={(e) => {
                                                        e.preventDefault(); // Prevent opening news link
                                                        window.location.href = `/analysis/${ticker}`;
                                                    }}
                                                    className="text-[10px] font-bold bg-primary/20 text-primary px-1.5 py-0.5 rounded hover:bg-primary hover:text-white transition-colors cursor-pointer"
                                                >
                                                    ${ticker}
                                                </span>
                                            ))}
                                        </div>
                                    )}

                                    <div className="flex gap-2 mt-2 text-xs text-gray-500">
                                        <span className="bg-white/10 px-1.5 rounded">{item.sector_tag}</span>
                                        <span>{item.publisher}</span>
                                        <span>•</span>
                                        <span>{new Date(item.providerPublishTime * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                    </div>
                                </div>
                            </a>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default Dashboard;
