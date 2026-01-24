import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Portfolio from './pages/Portfolio';
import StockDetail from './pages/StockDetail';
import Settings from './pages/Settings';
import Recommendations from './pages/Recommendations';
import Sidebar from './components/Sidebar';

// Layout for protected routes
const Layout = () => {
    return (
        <div className="flex h-screen bg-background text-white">
            <Sidebar />
            <main className="flex-1 overflow-auto p-6">
                <Outlet />
            </main>
        </div>
    );
};

// Private Route Guard
const PrivateRoute = () => {
    const token = localStorage.getItem('token');
    return token ? <Layout /> : <Navigate to="/login" replace />;
};

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/login" element={<Login />} />

                {/* Protected Routes */}
                <Route element={<PrivateRoute />}>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/portfolio" element={<Portfolio />} />
                    <Route path="/analysis/:ticker" element={<StockDetail />} />
                    <Route path="/recommendations" element={<Recommendations />} />
                    <Route path="/settings" element={<Settings />} />
                </Route>
            </Routes>
        </Router>
    );
}

export default App;
