import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import { Lock, User } from 'lucide-react';

const Login = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isRegister, setIsRegister] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        try {
            if (isRegister) {
                // Register new user
                await api.post('/auth/register', { username, password });
                alert('Account created successfully! Please log in.');
                setIsRegister(false);
                setPassword('');
            } else {
                // Login
                const formData = new FormData();
                formData.append('username', username);
                formData.append('password', password);

                const response = await api.post('/auth/token', formData);
                localStorage.setItem('token', response.data.access_token);
                navigate('/');
            }
        } catch (err) {
            setError(err.response?.data?.detail || (isRegister ? 'Registration failed. Username may already exist.' : 'Login failed'));
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-background">
            <div className="w-full max-w-md p-8 bg-surface rounded-xl shadow-2xl border border-gray-700">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-white mb-2">
                        {isRegister ? 'Create Account' : 'Welcome Back'}
                    </h1>
                    <p className="text-gray-400">
                        {isRegister ? 'Join the intelligent portfolio' : 'Sign in to your intelligent portfolio'}
                    </p>
                </div>

                {error && (
                    <div className="bg-danger/10 text-danger p-3 rounded-lg mb-4 text-center">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                        <label className="block text-gray-400 mb-2">Username</label>
                        <div className="relative">
                            <User className="absolute left-3 top-3 text-gray-500" size={20} />
                            <input
                                type="text"
                                className="w-full bg-background border border-gray-700 rounded-lg py-2.5 pl-10 text-white focus:outline-none focus:border-primary"
                                placeholder="Enter username"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                required
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-gray-400 mb-2">Password</label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-3 text-gray-500" size={20} />
                            <input
                                type="password"
                                className="w-full bg-background border border-gray-700 rounded-lg py-2.5 pl-10 text-white focus:outline-none focus:border-primary"
                                placeholder="Enter password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        className="w-full bg-primary hover:bg-blue-600 text-white font-semibold py-3 rounded-lg transition-colors"
                    >
                        {isRegister ? 'Create Account' : 'Login'}
                    </button>

                    <div className="text-center">
                        <button
                            type="button"
                            onClick={() => {
                                setIsRegister(!isRegister);
                                setError('');
                            }}
                            className="text-primary hover:text-accent transition-colors text-sm"
                        >
                            {isRegister ? 'Already have an account? Login' : "Don't have an account? Register"}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default Login;
