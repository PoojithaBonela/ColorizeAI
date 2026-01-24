import { Camera } from 'lucide-react';

const Footer = () => {
    return (
        <footer className="border-t border-white/5 py-12 mt-20">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex flex-col md:flex-row justify-between items-center space-y-6 md:space-y-0">
                    <div className="flex items-center space-x-2">
                        <div className="p-1.5 bg-slate-800 rounded-md">
                            <Camera className="w-4 h-4 text-slate-400" />
                        </div>
                        <span className="text-lg font-bold text-white">ColorizeAI</span>
                    </div>

                    <p className="text-slate-500 text-sm">
                        © {new Date().getFullYear()} ColorizeAI. Built with passion for memories.
                    </p>


                </div>
            </div>
        </footer>
    );
};

export default Footer;
