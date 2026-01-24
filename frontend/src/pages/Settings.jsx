import React, { useState, useEffect } from 'react';
import api from '../api';
import { Server, Layers, CheckCircle2 } from 'lucide-react';

const Settings = () => {
    const [activeSectors, setActiveSectors] = useState([]);
    const [loading, setLoading] = useState(true);
    const [saveStatus, setSaveStatus] = useState('');

    useEffect(() => {
        const fetchSettings = async () => {
            try {
                const res = await api.get('/users/settings');
                setActiveSectors(res.data.active_sectors || []);
            } catch (err) {
                console.error("Failed to load settings", err);
            }
            setLoading(false);
        };
        fetchSettings();
    }, []);

    const toggleSector = async (sector) => {
        const newSectors = activeSectors.includes(sector)
            ? activeSectors.filter(s => s !== sector)
            : [...activeSectors, sector];

        setActiveSectors(newSectors);
        setSaveStatus('Saving...');

        try {
            await api.put('/users/settings', { active_sectors: newSectors });
            setSaveStatus('Saved!');
            setTimeout(() => setSaveStatus(''), 2000);
        } catch (err) {
            console.error("Failed to save settings", err);
            setSaveStatus('Error saving');
        }
    };

    if (loading) return <div className="p-8 text-gray-400">Loading settings...</div>;

    const sectors = [
        'Technology', 'Financials', 'Healthcare', 'Energy',
        'Consumer Discretionary', 'Real Estate', 'Communication Services',
        'Semiconductor', 'Biotech', 'Cybersecurity', 'Robotics & AI', 'Defense',
        'Consumer Staples', 'Industrials', 'Materials', 'Utilities', 'Clean Energy',
        'Critical Materials', 'Strategic Metals', 'Transportation', 'Retail', 'Homebuilders',
        'Regional Banking', 'Oil & Gas Exploration', 'Gold Miners', 'Cloud Computing', 'Solar',
    ];

    return (
        <div className="max-w-2xl mx-auto space-y-6 pb-12">
            <div className="flex justify-between items-center mb-8">
                <h2 className="text-3xl font-bold text-white">Settings</h2>
                {saveStatus && (
                    <div className="flex items-center gap-2 text-success text-sm font-medium animate-pulse">
                        <CheckCircle2 size={16} />
                        {saveStatus}
                    </div>
                )}
            </div>

            {/* AI Model Preference */}
            <div className="bg-surface rounded-xl border border-gray-700 p-6">
                <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                    <Server size={20} className="text-primary" /> AI Model Engine
                </h3>

                <div className="space-y-4 text-left">
                    <div className="flex items-center gap-4 p-4 rounded-lg border border-primary bg-primary/10">
                        <div className="w-5 h-5 rounded-full border-4 border-primary flex items-center justify-center">
                            <div className="w-2 h-2 bg-primary rounded-full"></div>
                        </div>
                        <div className="flex-1">
                            <div className="font-bold text-white">Local (Ollama)</div>
                            <div className="text-sm text-gray-300">Run Llama 3.2 locally. Free & Private.</div>
                        </div>
                        <div className="text-xs font-bold bg-success/20 text-success px-2 py-1 rounded">ACTIVE</div>
                    </div>

                    <div className="flex items-center gap-4 p-4 rounded-lg border border-gray-700 opacity-50 grayscale cursor-not-allowed">
                        <div className="w-5 h-5 rounded-full border-2 border-gray-700"></div>
                        <div className="flex-1">
                            <div className="font-bold text-gray-400">Cloud (OpenAI / Claude)</div>
                            <div className="text-sm text-gray-500">Requires API Key. Higher accuracy.</div>
                        </div>
                        <div className="text-xs font-bold bg-gray-700 text-gray-400 px-2 py-1 rounded">LOCKED</div>
                    </div>
                </div>
            </div>

            {/* Sectors */}
            <div className="bg-surface rounded-xl border border-gray-700 p-6">
                <div className="mb-4">
                    <h3 className="text-xl font-bold text-white flex items-center gap-2">
                        <Layers size={20} className="text-accent" /> Active Sectors
                    </h3>
                    <p className="text-sm text-gray-500 mt-1">Select sectors to monitor for news and recommendations.</p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                    {sectors.map(sector => {
                        const isChecked = activeSectors.includes(sector);
                        return (
                            <label
                                key={sector}
                                className={`flex items-center justify-between p-3 rounded-lg border transition-all cursor-pointer ${isChecked
                                        ? 'border-accent bg-accent/10'
                                        : 'border-gray-700 hover:border-gray-500 hover:bg-white/5'
                                    }`}
                            >
                                <span className={isChecked ? 'text-white' : 'text-gray-400'}>{sector}</span>
                                <input
                                    type="checkbox"
                                    checked={isChecked}
                                    onChange={() => toggleSector(sector)}
                                    className="w-4 h-4 rounded border-gray-600 text-accent focus:ring-accent bg-transparent"
                                />
                            </label>
                        );
                    })}
                </div>
            </div>
        </div>
    );
};

export default Settings;
