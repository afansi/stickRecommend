import React, { useState, useEffect } from 'react';
import api from '../api';
import { Settings as SettingsIcon, Server, Cloud, Layers } from 'lucide-react';

const Settings = () => {
    return (
        <div className="max-w-2xl mx-auto space-y-6">
            <h2 className="text-3xl font-bold text-white mb-8">Settings</h2>

            {/* AI Model Preference */}
            <div className="bg-surface rounded-xl border border-gray-700 p-6">
                <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                    <Server size={20} className="text-primary" /> AI Model Engine
                </h3>

                <div className="space-y-4">
                    <label className="flex items-center gap-4 p-4 rounded-lg border border-primary bg-primary/10 cursor-pointer">
                        <input type="radio" name="ai-model" defaultChecked className="w-5 h-5 text-primary" />
                        <div className="flex-1">
                            <div className="font-bold text-white">Local (Ollama)</div>
                            <div className="text-sm text-gray-300">Run Llama 3.2 locally. Free & Private.</div>
                        </div>
                        <div className="text-xs font-bold bg-success/20 text-success px-2 py-1 rounded">ACTIVE</div>
                    </label>

                    <label className="flex items-center gap-4 p-4 rounded-lg border border-gray-700 hover:bg-background cursor-pointer transition-colors opacity-60">
                        <input type="radio" name="ai-model" disabled className="w-5 h-5 text-gray-500" />
                        <div className="flex-1">
                            <div className="font-bold text-gray-400">Cloud (OpenAI / Claude)</div>
                            <div className="text-sm text-gray-500">Requires API Key. Higher accuracy.</div>
                        </div>
                        <div className="text-xs font-bold bg-gray-700 text-gray-400 px-2 py-1 rounded">LOCKED</div>
                    </label>
                </div>
            </div>

            {/* Sectors */}
            <div className="bg-surface rounded-xl border border-gray-700 p-6">
                <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                    <Layers size={20} className="text-accent" /> Active Sectors
                </h3>
                <div className="grid grid-cols-2 gap-4">
                    {[
                        'Technology', 'Financials', 'Healthcare', 'Energy',
                        'Consumer Discretionary', 'Real Estate', 'Communication Services',
                        'Semiconductor', 'Biotech', 'Cybersecurity', 'Robotics & AI', 'Defence',

                        'Consumer Staples', 'Industrials', 'Materials', 'Utilities', 'Clean Energy',
                        'Critical Materials', 'Strategic Metals', 'Transportation', 'Retail', 'Homebuilders',
                        'Regional Banking', 'Oil & Gas Exploration', 'Gold Miners', 'Cloud Computing', 'Solar',
                    ].map(sector => (
                        <label key={sector} className="flex items-center gap-3 p-3 rounded-lg overflow-hidden border border-gray-700 hover:bg-background cursor-pointer">
                            <input type="checkbox" defaultChecked={['Technology', 'Financials', 'Cybersecurity'].includes(sector)} className="w-4 h-4 rounded text-accent focus:ring-accent" />
                            <span className="text-gray-300">{sector}</span>
                        </label>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default Settings;
