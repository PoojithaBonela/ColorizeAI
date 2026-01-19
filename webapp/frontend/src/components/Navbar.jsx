import { Link, useLocation } from 'react-router-dom';
import { Camera, Github } from 'lucide-react';

const Navbar = () => {
    const location = useLocation();

    return (
        <nav className="sticky top-0 z-50 w-full glass border-b border-white/5">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-16">
                    <Link to="/" className="flex items-center space-x-2 group">
                        <div className="p-2 bg-primary-500 rounded-lg group-hover:bg-primary-400 transition-colors">
                            <Camera className="w-5 h-5 text-white" />
                        </div>
                        <span className="text-xl font-bold tracking-tight text-white">
                            Colorize<span className="text-primary-400">AI</span>
                        </span>
                    </Link>

                    <div className="hidden md:flex items-center space-x-8 text-sm font-medium">
                        <Link
                            to="/"
                            className={`transition-colors hover:text-primary-400 ${location.pathname === '/' ? 'text-primary-400' : 'text-slate-400'}`}
                        >
                            Home
                        </Link>
                        <Link
                            to="/app"
                            className={`transition-colors hover:text-primary-400 ${location.pathname === '/app' ? 'text-primary-400' : 'text-slate-400'}`}
                        >
                            Application
                        </Link>
                        <a
                            href="https://github.com"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-4 py-2 bg-slate-800 text-white rounded-full hover:bg-slate-700 transition-all flex items-center space-x-2"
                        >
                            <Github className="w-4 h-4" />
                            <span>Star on GitHub</span>
                        </a>
                    </div>

                    <div className="md:hidden">
                        <Link
                            to="/app"
                            className="px-4 py-2 bg-primary-500 text-white text-sm rounded-full hover:bg-primary-600 transition-colors"
                        >
                            Get Started
                        </Link>
                    </div>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
