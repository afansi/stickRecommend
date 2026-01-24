import React, { useState, useEffect } from 'react';
import api from '../api';
import { Wallet, ArrowRight, PlusCircle, CheckCircle } from 'lucide-react';

const Portfolio = () => {
    const [holdings, setHoldings] = useState([]);
    const [freshFunds, setFreshFunds] = useState('');
    const [allocationPlan, setAllocationPlan] = useState(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        // Fetch Holdings
        const fetchHoldings = async () => {
            try {
                const res = await api.get('/portfolio');
                setHoldings(res.data);
            } catch (err) {
                console.error("Failed to fetch portfolio", err);
            }
        };
        fetchHoldings();
    }, []);

    const handleCalculate = async () => {
        if (!freshFunds) return;
        setLoading(true);
        try {
            const res = await api.post(`/portfolio/inject_funds?amount=${freshFunds}`);
            setAllocationPlan(res.data);
        } catch (err) {
            console.error("Failed to calculate", err);
        }
        setLoading(false);
    };

    return (
        <div className="space-y-6">
            <h2 className="text-3xl font-bold text-white">Portfolio Management</h2>

            {/* Fund Injection Widget */}
            <div className="bg-surface p-6 rounded-xl border border-gray-700 shadow-xl">
                <div className="flex items-center gap-3 mb-6">
                    <div className="bg-primary/20 p-3 rounded-full text-primary">
                        <Wallet size={24} />
                    </div>
                    <div>
                        <h3 className="text-xl font-bold text-white">Smart Fund Injection</h3>
                        <p className="text-gray-400 text-sm">Distribute capital based on AI Strategy</p>
                    </div>
                </div>

                <div className="flex items-end gap-4 mb-6">
                    <div className="flex-1">
                        <label className="block text-gray-400 mb-2 text-sm">Amount to Inject ($)</label>
                        <input
                            type="number"
                            className="w-full bg-background border border-gray-700 rounded-lg p-3 text-white focus:border-primary focus:outline-none"
                            placeholder="e.g. 1000"
                            value={freshFunds}
                            onChange={(e) => setFreshFunds(e.target.value)}
                        />
                    </div>
                    <button
                        onClick={handleCalculate}
                        disabled={loading}
                        className="bg-primary hover:bg-blue-600 text-white font-semibold py-3 px-6 rounded-lg transition-colors disabled:opacity-50"
                    >
                        {loading ? "Calculating..." : "Calculate Allocation"}
                    </button>
                </div>

                {allocationPlan && (
                    <div className="bg-background/50 rounded-lg p-4 border border-gray-700 animate-in fade-in slide-in-from-top-4">
                        <h4 className="font-bold text-white mb-3 flex items-center gap-2">
                            <CheckCircle size={16} className="text-success" />
                            Proposed Strategy
                        </h4>
                        <div className="space-y-3">
                            {allocationPlan.length === 0 && <p className="text-gray-400">No suitable allocation found. Hold as Cash.</p>}
                            {allocationPlan.map((item, idx) => (
                                <div key={idx} className="flex justify-between items-center p-3 bg-surface rounded border border-gray-700">
                                    <div className="flex items-center gap-3">
                                        <div className="bg-blue-500/20 text-blue-400 font-bold px-2 py-1 rounded text-sm">{item.ticker}</div>
                                        <div className="text-sm text-gray-400">{item.reason}</div>
                                    </div>
                                    <div className="font-bold text-success">+${item.amount}</div>
                                </div>
                            ))}
                        </div>
                        <div className="mt-4 flex justify-end">
                            <button className="text-sm text-primary hover:text-white transition-colors">Confirm & Execute Strategy</button>
                        </div>
                    </div>
                )}
            </div>

            {/* Current Holdings Table */}
            <div className="bg-surface rounded-xl border border-gray-700 overflow-hidden">
                <div className="p-4 border-b border-gray-700 flex justify-between items-center">
                    <h3 className="font-bold text-white">Current Holdings</h3>
                    <button className="flex items-center gap-2 text-sm text-primary hover:text-white bg-primary/10 hover:bg-primary/20 px-3 py-1.5 rounded transition-all">
                        <PlusCircle size={16} /> Add Stock Manually
                    </button>
                </div>
                <table className="w-full text-left">
                    <thead className="bg-background text-gray-400 text-sm">
                        <tr>
                            <th className="p-4">Ticker</th>
                            <th className="p-4">Qty</th>
                            <th className="p-4">Avg Cost</th>
                            <th className="p-4">Value</th>
                            <th className="p-4">Action</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-700">
                        {holdings.length === 0 ? (
                            <tr><td colSpan="5" className="p-8 text-center text-gray-500">No holdings yet. Start investing!</td></tr>
                        ) : (
                            holdings.map((h) => (
                                <tr key={h.id} className="hover:bg-gray-800/50 transition-colors">
                                    <td className="p-4 font-bold text-white">{h.ticker}</td>
                                    <td className="p-4 text-gray-300">{h.quantity}</td>
                                    <td className="p-4 text-gray-300">${h.avg_cost}</td>
                                    <td className="p-4 text-white font-mono">${(h.quantity * h.avg_cost * 1.05).toFixed(2)}</td>
                                    <td className="p-4">
                                        <a href={`/analysis/${h.ticker}`} className="text-primary hover:underline text-sm flex items-center gap-1">
                                            Analyze <ArrowRight size={14} />
                                        </a>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default Portfolio;
