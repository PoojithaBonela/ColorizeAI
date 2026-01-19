import { useState, useRef, useEffect } from 'react';

const CompareSlider = ({ before, after }) => {
    const [sliderPos, setSliderPos] = useState(50);
    const containerRef = useRef(null);

    const handleMove = (e) => {
        if (!containerRef.current) return;

        const rect = containerRef.current.getBoundingClientRect();
        const x = (e.pageX || e.touches?.[0]?.pageX) - rect.left;
        const position = Math.max(0, Math.min(100, (x / rect.width) * 100));
        setSliderPos(position);
    };

    return (
        <div
            ref={containerRef}
            className="relative w-full aspect-[4/3] rounded-2xl overflow-hidden cursor-ew-resize select-none glass-card"
            onMouseMove={handleMove}
            onTouchMove={handleMove}
        >
            {/* After image (Colorized) - Base layer */}
            <img
                src={after}
                alt="After"
                className="absolute inset-0 w-full h-full object-contain"
            />

            {/* Before image (B&W) - Overlay layer */}
            <div
                className="absolute inset-0 w-full h-full overflow-hidden"
                style={{ width: `${sliderPos}%`, borderRight: '2px solid white' }}
            >
                <img
                    src={before}
                    alt="Before"
                    className="absolute inset-0 h-full object-contain"
                    style={{ width: `${100 / (sliderPos / 100)}%`, maxWidth: 'none' }}
                />
            </div>

            {/* Handle */}
            <div
                className="absolute top-0 bottom-0 w-1 bg-white shadow-[0_0_10px_rgba(0,0,0,0.5)] flex items-center justify-center"
                style={{ left: `${sliderPos}%`, transform: 'translateX(-50%)' }}
            >
                <div className="w-8 h-8 bg-white rounded-full shadow-lg flex items-center justify-center space-x-0.5">
                    <div className="w-0.5 h-4 bg-slate-300"></div>
                    <div className="w-0.5 h-4 bg-slate-400"></div>
                    <div className="w-0.5 h-4 bg-slate-300"></div>
                </div>
            </div>

            {/* Labels */}
            <div className="absolute bottom-4 left-4 px-3 py-1 bg-black/50 backdrop-blur-md rounded-md text-xs font-bold text-white pointer-events-none uppercase tracking-wider">
                Original
            </div>
            <div className="absolute bottom-4 right-4 px-3 py-1 bg-primary-500/80 backdrop-blur-md rounded-md text-xs font-bold text-white pointer-events-none uppercase tracking-wider">
                AI Colorized
            </div>
        </div>
    );
};

export default CompareSlider;
