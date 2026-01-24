import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Wand2, Download, RefreshCw, Loader2, Image as ImageIcon, MousePointer2, Undo2, Redo2, Info } from 'lucide-react';
import UploadZone from '../components/UploadZone';
import CompareSlider from '../components/CompareSlider';
import InteractiveBrush from '../components/InteractiveBrush';

const AppPage = () => {
    const [file, setFile] = useState(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [isRefining, setIsRefining] = useState(false);

    // History State
    const [history, setHistory] = useState([]);
    const [historyIndex, setHistoryIndex] = useState(-1);

    // Metrics State
    const [metrics, setMetrics] = useState({ global: 0, tiles: [], brush: null });

    // Helper for Base64 to Blob
    const base64ToBlob = (b64Data, contentType = 'image/jpeg') => {
        const byteCharacters = atob(b64Data);
        const byteArrays = [];
        for (let offset = 0; offset < byteCharacters.length; offset += 512) {
            const slice = byteCharacters.slice(offset, offset + 512);
            const byteNumbers = new Array(slice.length);
            for (let i = 0; i < slice.length; i++) {
                byteNumbers[i] = slice.charCodeAt(i);
            }
            const byteArray = new Uint8Array(byteNumbers);
            byteArrays.push(byteArray);
        }
        return new Blob(byteArrays, { type: contentType });
    };

    // Derived state from history
    const result = historyIndex >= 0 ? history[historyIndex].url : null;
    const resultBlob = historyIndex >= 0 ? history[historyIndex].blob : null;

    const [isRefineMode, setIsRefineMode] = useState(false);

    const pushToHistory = (blob) => {
        const url = URL.createObjectURL(blob);
        const nextHistory = history.slice(0, historyIndex + 1);
        nextHistory.push({ blob, url });
        setHistory(nextHistory);
        setHistoryIndex(nextHistory.length - 1);
    };

    const undo = () => {
        if (historyIndex > 0) {
            setHistoryIndex(historyIndex - 1);
        }
    };

    const redo = () => {
        if (historyIndex < history.length - 1) {
            setHistoryIndex(historyIndex + 1);
        }
    };

    const handleUpload = (uploadedFile) => {
        setFile(uploadedFile);
        setHistory([]);
        setHistoryIndex(-1);
        setIsRefineMode(false);
        setMetrics({ global: 0, tiles: [], brush: null });
        setShowConfidence(false);
    };

    const handleRefine = async (maskBlob, targetColor) => {
        if (!file || !resultBlob) return;
        setIsRefining(true);

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('mask', maskBlob);
            formData.append('base', resultBlob); // Send the PREVIOUS result
            if (targetColor) {
                formData.append('target_color', targetColor);
            }

            const response = await fetch('http://localhost:8000/refine', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) throw new Error('Refinement failed');

            const data = await response.json();
            const blob = base64ToBlob(data.image);

            // Update Brush Confidence
            setMetrics(prev => ({
                ...prev,
                brush: data.metrics.brush_confidence
            }));

            pushToHistory(blob);
        } catch (error) {
            console.error('Error refining image:', error);
            alert('Failed to refine image areas.');
        } finally {
            setIsRefining(false);
        }
    };

    const handleColorize = async () => {
        if (!file) return;
        setIsProcessing(true);

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('http://localhost:8000/colorize', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) throw new Error('Colorization failed');

            const data = await response.json();
            const blob = base64ToBlob(data.image);

            // Set Metrics
            setMetrics({
                global: data.metrics.global_color_strength,
                tiles: data.metrics.tile_confidence_map,
                brush: null
            });

            pushToHistory(blob);
        } catch (error) {
            console.error('Error colorizing image:', error);
            alert('Failed to colorize image. Please ensure the backend server is running.');
        } finally {
            setIsProcessing(false);
        }
    };

    const reset = () => {
        setFile(null);
        setHistory([]);
        setHistoryIndex(-1);
        setMetrics({ global: 0, tiles: [], brush: null });
        setShowConfidence(false);
    };

    return (
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-4 pb-8">
            <div className="mb-6 text-center md:text-left">
                <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">Transform Your Photos</h1>
                <p className="text-slate-400">Upload a black and white image and let our AI do the magic.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
                {/* Left Side: Upload & Input */}
                <div className="space-y-6">
                    <UploadZone
                        onUpload={handleUpload}
                        selectedFile={file}
                        onClear={reset}
                    />

                    <div className="flex flex-col space-y-4">
                        <button
                            onClick={handleColorize}
                            disabled={!file || isProcessing}
                            className={`w-full py-3 rounded-xl font-bold flex items-center justify-center transition-all shadow-xl
                ${!file || isProcessing
                                    ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                                    : 'bg-primary-500 text-white hover:bg-primary-600 shadow-primary-500/20 active:scale-[0.98]'
                                }`}
                        >
                            {isProcessing ? (
                                <>
                                    <Loader2 className="w-5 h-5 mr-3 animate-spin" />
                                    Colorizing with AI...
                                </>
                            ) : (
                                <>
                                    <Wand2 className="w-5 h-5 mr-3" />
                                    Colorize Photo
                                </>
                            )}
                        </button>

                        <p className="text-center text-xs text-slate-500">
                            Processing time: ~5 seconds. Results may vary depending on image quality.
                        </p>
                    </div>
                </div>

                {/* Right Side: Result Area */}
                <div className="space-y-4">
                    <AnimatePresence mode="wait">
                        {!result ? (
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                className="w-full aspect-[4/3] rounded-2xl border-2 border-dashed border-white/5 flex flex-col items-center justify-center text-slate-500 bg-slate-900/20"
                            >
                                <div className="p-6 rounded-full bg-slate-800/50 mb-4">
                                    <ImageIcon className="w-12 h-12 opacity-20" />
                                </div>
                                <p className="text-sm font-medium">Result will appear here</p>
                                <p className="text-xs opacity-50 mt-1">Ready to create magic</p>
                            </motion.div>
                        ) : (
                            <motion.div
                                initial={{ opacity: 0, scale: 0.95 }}
                                animate={{ opacity: 1, scale: 1 }}
                                className="space-y-3"
                            >
                                <div className="flex flex-wrap items-center justify-between bg-slate-800/50 p-1 rounded-lg border border-white/5 gap-2">
                                    <div className="flex p-0.5 space-x-1">
                                        <button
                                            onClick={() => setIsRefineMode(false)}
                                            className={`px-3 py-1.5 text-xs sm:px-4 sm:py-2 sm:text-sm rounded-md font-bold transition-all ${!isRefineMode ? 'bg-primary-500 text-white shadow-lg' : 'text-slate-400 hover:text-white'}`}
                                        >
                                            Compare
                                        </button>
                                        <button
                                            onClick={() => setIsRefineMode(true)}
                                            className={`px-3 py-1.5 text-xs sm:px-4 sm:py-2 sm:text-sm rounded-md font-bold transition-all ${isRefineMode ? 'bg-emerald-500 text-white shadow-lg' : 'text-slate-400 hover:text-white'}`}
                                        >
                                            Smart Brush
                                        </button>
                                    </div>

                                    <div className="flex items-center space-x-2 px-2">

                                        <button
                                            onClick={undo}
                                            disabled={historyIndex <= 0}
                                            className="p-1.5 sm:p-2 rounded-full bg-slate-700/50 text-white disabled:opacity-30 hover:bg-slate-700 transition-all border border-white/5"
                                            title="Undo"
                                        >
                                            <Undo2 className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                                        </button>
                                        <button
                                            onClick={redo}
                                            disabled={historyIndex >= history.length - 1}
                                            className="p-1.5 sm:p-2 rounded-full bg-slate-700/50 text-white disabled:opacity-30 hover:bg-slate-700 transition-all border border-white/5"
                                            title="Redo"
                                        >
                                            <Redo2 className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                                        </button>
                                    </div>
                                </div>

                                {/* Metrics Bar */}
                                <div className="bg-slate-800/50 p-2.5 rounded-xl border border-white/5 flex flex-col md:flex-row gap-4 items-center">
                                    <div className="flex-1 w-full">
                                        <div className="flex items-center justify-between mb-2">
                                            <div className="flex items-center text-sm font-medium text-slate-300">
                                                Color Vibrancy
                                                <div className="group relative ml-2">
                                                    <Info className="w-4 h-4 text-slate-500 cursor-help" />
                                                    <div className="absolute right-0 sm:right-auto sm:bottom-full sm:left-1/2 sm:-translate-x-1/2 mb-2 w-56 sm:w-64 p-2 bg-slate-900 text-xs text-slate-300 rounded-lg border border-white/10 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-xl">
                                                        Indicates the richness of the restored colors. Higher values mean more vibrant, saturated results.
                                                    </div>
                                                </div>
                                            </div>
                                            <span className="text-sm font-bold text-primary-400">{Math.round(metrics.global)}/100</span>
                                        </div>
                                        <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-gradient-to-r from-red-500 via-yellow-500 to-emerald-500 transition-all duration-1000 ease-out"
                                                style={{ width: `${metrics.global}%` }}
                                            />
                                        </div>
                                    </div>

                                    {metrics.brush !== null && (
                                        <div className="flex items-center gap-3 bg-slate-900/50 px-4 py-2 rounded-lg border border-white/5">
                                            <span className="text-sm text-slate-400">Refinement Confidence:</span>
                                            <span className={`text-sm font-bold ${metrics.brush > 45 ? 'text-emerald-400' :
                                                metrics.brush > 20 ? 'text-amber-400' : 'text-red-400'
                                                }`}>
                                                {metrics.brush > 45 ? 'High' : metrics.brush > 20 ? 'Medium' : 'Low'}
                                            </span>
                                        </div>
                                    )}
                                </div>

                                <div className="relative rounded-2xl overflow-hidden border border-white/10 shadow-2xl max-h-[70vh] sm:max-h-none">


                                    {isRefineMode ? (
                                        <InteractiveBrush
                                            image={result}
                                            onRefine={handleRefine}
                                            isRefining={isRefining}
                                        />
                                    ) : (
                                        <CompareSlider
                                            before={file ? URL.createObjectURL(file) : ''}
                                            after={result}
                                        />
                                    )}
                                </div>

                                <div className="flex flex-col sm:flex-row gap-4">
                                    <button
                                        onClick={() => {
                                            const link = document.createElement('a');
                                            link.href = result;
                                            link.download = 'colorized_photo.jpg';
                                            link.click();
                                        }}
                                        className="flex-grow py-3 bg-emerald-500 text-white rounded-xl font-bold flex items-center justify-center hover:bg-emerald-600 transition-all shadow-lg shadow-emerald-500/20"
                                    >
                                        <Download className="w-5 h-5 mr-3" />
                                        Download Result
                                    </button>
                                    <button
                                        onClick={reset}
                                        className="px-6 py-3 bg-slate-800 text-white rounded-xl font-bold flex items-center justify-center hover:bg-slate-700 transition-all border border-white/5"
                                    >
                                        <RefreshCw className="w-5 h-5 mr-3" />
                                        Try Another
                                    </button>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
};

export default AppPage;
