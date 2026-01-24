import React, { useRef, useEffect, useState } from 'react';
import { Eraser, Paintbrush, Loader2, Pipette } from 'lucide-react';

const InteractiveBrush = ({ image, onRefine, isRefining }) => {
    const canvasRef = useRef(null);
    const containerRef = useRef(null);
    const imageCanvasRef = useRef(null); // Hidden canvas for color sampling
    const [isDrawing, setIsDrawing] = useState(false);
    const [brushSize, setBrushSize] = useState(30);
    const [isEyedropper, setIsEyedropper] = useState(false);
    const [selectedColor, setSelectedColor] = useState(null);

    useEffect(() => {
        if (!image) return;
        const img = new Image();
        img.src = image;
        img.crossOrigin = "Anonymous"; // Crucial for reading pixel data
        img.onload = () => {
            const canvas = canvasRef.current;
            if (canvas) {
                canvas.width = img.naturalWidth;
                canvas.height = img.naturalHeight;

                const ctx = canvas.getContext('2d');
                ctx.lineJoin = 'round';
                ctx.lineCap = 'round';
                ctx.strokeStyle = 'white';
                ctx.lineWidth = brushSize * (img.naturalWidth / 800);
            }

            // Also draw to hidden canvas for color picking
            const imgCanvas = document.createElement('canvas');
            imgCanvas.width = img.naturalWidth;
            imgCanvas.height = img.naturalHeight;
            const imgCtx = imgCanvas.getContext('2d');
            imgCtx.drawImage(img, 0, 0);
            imageCanvasRef.current = imgCanvas;
        };
    }, [image, brushSize]);

    const sampleColor = (e) => {
        if (!imageCanvasRef.current) return;
        const rect = canvasRef.current.getBoundingClientRect();

        const scaleX = imageCanvasRef.current.width / rect.width;
        const scaleY = imageCanvasRef.current.height / rect.height;

        const x = ((e.clientX || e.touches?.[0]?.clientX) - rect.left) * scaleX;
        const y = ((e.clientY || e.touches?.[0]?.clientY) - rect.top) * scaleY;

        const ctx = imageCanvasRef.current.getContext('2d');
        const pixel = ctx.getImageData(x, y, 1, 1).data;
        const hex = "#" + ("000000" + ((pixel[0] << 16) | (pixel[1] << 8) | pixel[2]).toString(16)).slice(-6);

        setSelectedColor(hex);
        setIsEyedropper(false); // Switch back to brush after picking
    };

    const startDrawing = (e) => {
        if (isEyedropper) {
            sampleColor(e);
            return;
        }
        setIsDrawing(true);
        draw(e);
    };

    const stopDrawing = () => {
        setIsDrawing(false);
        if (canvasRef.current) {
            const ctx = canvasRef.current.getContext('2d');
            ctx.beginPath();
        }
    };

    const draw = (e) => {
        if (!isDrawing || isEyedropper) return;
        const canvas = canvasRef.current;
        const rect = canvas.getBoundingClientRect();

        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;

        const x = ((e.clientX || e.touches?.[0]?.clientX) - rect.left) * scaleX;
        const y = ((e.clientY || e.touches?.[0]?.clientY) - rect.top) * scaleY;

        const ctx = canvas.getContext('2d');
        ctx.lineTo(x, y);
        ctx.stroke();
    };

    const handleRefine = () => {
        const canvas = canvasRef.current;
        const maskCanvas = document.createElement('canvas');
        maskCanvas.width = canvas.width;
        maskCanvas.height = canvas.height;
        const mCtx = maskCanvas.getContext('2d');
        mCtx.fillStyle = 'black';
        mCtx.fillRect(0, 0, maskCanvas.width, maskCanvas.height);
        mCtx.drawImage(canvas, 0, 0);

        maskCanvas.toBlob((blob) => {
            onRefine(blob, selectedColor); // Pass selectedColor back
        }, 'image/png');
    };

    const clear = () => {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    };

    return (
        <div className="space-y-4">
            <div
                ref={containerRef}
                className="relative w-full aspect-[4/3] rounded-2xl overflow-hidden glass-card bg-slate-900"
            >
                <img
                    src={image}
                    alt="Target for refinement"
                    className="absolute inset-0 w-full h-full object-contain pointer-events-none"
                />
                <canvas
                    ref={canvasRef}
                    className="absolute inset-0 w-full h-full touch-none transition-all"
                    style={{ cursor: isEyedropper ? 'copy' : 'crosshair' }}
                    onMouseDown={startDrawing}
                    onMouseMove={draw}
                    onMouseUp={stopDrawing}
                    onMouseLeave={stopDrawing}
                    onTouchStart={startDrawing}
                    onTouchMove={draw}
                    onTouchEnd={stopDrawing}
                />

                {isRefining && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-sm z-10">
                        <div className="flex flex-col items-center">
                            <Loader2 className="w-10 h-10 text-primary-500 animate-spin mb-2" />
                            <p className="text-white font-medium">Refining area...</p>
                        </div>
                    </div>
                )}
            </div>

            <div className="flex flex-wrap items-center justify-center sm:justify-between gap-3 sm:gap-4 p-3 sm:p-4 bg-slate-800/50 rounded-xl border border-white/5">
                <div className="flex items-center space-x-2">
                    <button
                        onClick={() => setIsEyedropper(!isEyedropper)}
                        className={`p-3 sm:p-2 rounded-lg transition-all ${isEyedropper ? 'bg-amber-500 text-white' : 'bg-slate-700 text-slate-300 hover:text-white'}`}
                        title="Pick color from image"
                    >
                        <Pipette className="w-5 h-5 sm:w-4 sm:h-4" />
                    </button>

                    {selectedColor && (
                        <div className="flex items-center space-x-2 bg-slate-700/50 pr-3 rounded-lg overflow-hidden border border-white/10">
                            <div
                                className="w-8 h-8 sm:w-8 sm:h-8"
                                style={{ backgroundColor: selectedColor }}
                            />
                            <span className="text-xs font-mono text-slate-300 uppercase hidden sm:block">{selectedColor}</span>
                            <button
                                onClick={() => setSelectedColor(null)}
                                className="text-slate-500 hover:text-rose-400 p-2 sm:p-1"
                            >
                                <Eraser className="w-4 h-4 sm:w-3 sm:h-3" />
                            </button>
                        </div>
                    )}
                </div>

                <div className="h-6 w-px bg-white/10 hidden sm:block"></div>

                <div className="flex items-center space-x-2">
                    <Paintbrush className="w-5 h-5 sm:w-4 sm:h-4 text-slate-400" />
                    <input
                        type="range"
                        min="10"
                        max="80"
                        value={brushSize}
                        onChange={(e) => setBrushSize(parseInt(e.target.value))}
                        className="w-32 sm:w-24 h-2 sm:h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-primary-500"
                    />
                </div>

                <div className="h-6 w-px bg-white/10 hidden sm:block"></div>

                <button
                    onClick={clear}
                    className="px-4 py-3 sm:py-2 text-sm font-medium text-slate-300 hover:text-white flex items-center bg-slate-700/30 rounded-lg sm:bg-transparent"
                >
                    <Eraser className="w-5 h-5 sm:w-4 sm:h-4 mr-2" />
                    Clear
                </button>

                <div className="w-full sm:w-auto flex-grow flex justify-center sm:justify-end mt-2 sm:mt-0">
                    <button
                        onClick={handleRefine}
                        disabled={isRefining}
                        className="w-full sm:w-auto px-6 py-3 sm:py-2 bg-primary-500 hover:bg-primary-600 disabled:bg-slate-700 text-white rounded-lg font-bold transition-all shadow-lg shadow-primary-500/20 text-sm sm:text-base"
                    >
                        Apply Refinement
                    </button>
                </div>
            </div>

            <p className="text-xs text-slate-500 italic px-2">
                Tip: Brush over the gray areas (like skin or petals) and click "Apply Refinement" to focus the AI there.
            </p>
        </div>
    );
};

export default InteractiveBrush;
