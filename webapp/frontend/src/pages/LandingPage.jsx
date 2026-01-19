import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight, Sparkles, Zap, Shield } from 'lucide-react';

const LandingPage = () => {
    const navigate = useNavigate();

    return (
        <div className="relative overflow-hidden">
            {/* Background Blobs */}
            <div className="absolute top-0 -left-4 w-72 h-72 bg-primary-500/20 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob"></div>
            <div className="absolute top-0 -right-4 w-72 h-72 bg-purple-500/20 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-2000"></div>

            {/* Hero Section */}
            <section className="relative pt-20 pb-32 sm:pt-32 sm:pb-40">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5 }}
                    >
                        <span className="inline-flex items-center px-4 py-1.5 rounded-full text-sm font-medium bg-primary-500/10 text-primary-400 border border-primary-500/20 mb-8">
                            <Sparkles className="w-4 h-4 mr-2" />
                            AI-Powered Colorization
                        </span>
                        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-white mb-6">
                            Colorize Your <span className="text-gradient">Memories</span> <br />
                            with AI
                        </h1>
                        <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-10">
                            Bring black & white photos back to life using state-of-the-art deep learning.
                            Restore lost moments with stunning accuracy and detail.
                        </p>
                        <div className="flex flex-col sm:flex-row items-center justify-center">
                            <button
                                onClick={() => navigate('/app')}
                                className="group relative px-10 py-5 bg-primary-500 text-white rounded-full font-bold text-lg hover:bg-primary-600 transition-all flex items-center shadow-xl shadow-primary-500/20 hover:scale-105 active:scale-95"
                            >
                                Get Started Free
                                <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
                            </button>
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* Features Grid */}
            <section className="py-16 relative overflow-hidden">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 max-w-7xl mx-auto">
                        <FeatureCard
                            icon={<Zap className="w-10 h-10 text-amber-400" />}
                            title="Instant Results"
                            description="Colorize your photos in seconds with our optimized AI inference engine. Experience lightning-fast restoration."
                            delay={0}
                            gradient="from-amber-500/20 to-orange-600/20"
                        />
                        <FeatureCard
                            icon={<Sparkles className="w-10 h-10 text-primary-400" />}
                            title="Expert Restoration"
                            description="Our AI interprets the scene to provide historically accurate and vibrant tones that feel naturally captured."
                            delay={0.1}
                            gradient="from-primary-500/20 to-blue-600/20"
                        />
                        <FeatureCard
                            icon={<Shield className="w-10 h-10 text-emerald-400" />}
                            title="Secure & Private"
                            description="Your precious memories never leave our secure environment. We use enterprise-grade encryption for all processing."
                            delay={0.2}
                            gradient="from-emerald-500/20 to-teal-600/20"
                        />
                    </div>
                </div>
            </section>
        </div>
    );
};

const FeatureCard = ({ icon, title, description, delay, gradient }) => (
    <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        whileInView={{ opacity: 1, scale: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6, delay }}
        whileHover={{ y: -10, transition: { duration: 0.3 } }}
        className="relative group p-1"
    >
        <div className={`absolute inset-0 bg-gradient-to-br ${gradient} rounded-[2rem] blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500`}></div>

        <div className="glass-card rounded-[2rem] p-10 h-full border border-white/[0.08] group-hover:border-primary-500/50 transition-all duration-500 relative z-10 overflow-hidden bg-slate-900/40 backdrop-blur-3xl">
            {/* Subtle Pattern Overlay */}
            <div className="absolute inset-0 opacity-[0.03] pointer-events-none bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')]"></div>

            <div className="flex flex-col items-start h-full">
                <div className="p-5 bg-white/5 rounded-2xl mb-8 group-hover:scale-110 group-hover:bg-white/10 transition-all duration-500 shadow-xl border border-white/10">
                    {icon}
                </div>
                <h3 className="text-2xl font-bold text-white mb-5 tracking-tight group-hover:text-primary-400 transition-colors duration-300">{title}</h3>
                <p className="text-base text-slate-400 leading-relaxed group-hover:text-slate-300 transition-colors duration-300">
                    {description}
                </p>
            </div>
        </div>
    </motion.div>
);

export default LandingPage;
