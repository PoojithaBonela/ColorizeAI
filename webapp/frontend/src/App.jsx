import { Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import AppPage from './pages/AppPage';
import Navbar from './components/Navbar';
import Footer from './components/Footer';

function App() {
    return (
        <div className="min-h-screen bg-[#0f172a] text-slate-200 flex flex-col font-sans selection:bg-primary-500/30">
            <Navbar />
            <main className="flex-grow">
                <Routes>
                    <Route path="/" element={<LandingPage />} />
                    <Route path="/app" element={<AppPage />} />
                </Routes>
            </main>
            <Footer />
        </div>
    );
}

export default App;
