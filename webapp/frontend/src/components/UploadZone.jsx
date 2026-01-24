import { useState, useCallback } from 'react';
import { Upload, X, Image as ImageIcon } from 'lucide-react';

const UploadZone = ({ onUpload, selectedFile, onClear }) => {
    const [isDragging, setIsDragging] = useState(false);

    const handleDragOver = useCallback((e) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    const validateAndUpload = (file) => {
        const validTypes = ['image/jpeg', 'image/png', 'image/jpg'];
        if (!validTypes.includes(file.type)) {
            alert('Only JPG and PNG files are allowed!');
            return;
        }
        onUpload(file);
    };

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        setIsDragging(false);
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            validateAndUpload(files[0]);
        }
    }, [onUpload]);

    const handleFileInput = (e) => {
        if (e.target.files.length > 0) {
            validateAndUpload(e.target.files[0]);
        }
    };

    if (selectedFile) {
        return (
            <div className="relative group w-full aspect-[4/3] rounded-2xl overflow-hidden glass-card">
                <img
                    src={URL.createObjectURL(selectedFile)}
                    alt="Preview"
                    className="w-full h-full object-contain"
                />
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <button
                        onClick={onClear}
                        className="p-3 bg-red-500 text-white rounded-full hover:bg-red-600 transition-all transform hover:scale-110"
                    >
                        <X className="w-6 h-6" />
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`relative w-full aspect-[4/3] rounded-2xl border-2 border-dashed transition-all flex flex-col items-center justify-center p-8 text-center cursor-pointer
        ${isDragging
                    ? 'border-primary-500 bg-primary-500/10'
                    : 'border-white/10 hover:border-white/20 hover:bg-white/5'
                }`}
            onClick={() => document.getElementById('file-input').click()}
        >
            <input
                id="file-input"
                type="file"
                className="hidden"
                accept="image/png, image/jpeg, image/jpg"
                onChange={handleFileInput}
            />
            <div className="p-4 bg-slate-800 rounded-2xl mb-4 group-hover:scale-110 transition-transform">
                <Upload className="w-8 h-8 text-primary-400" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Upload Photo</h3>
            <p className="text-slate-400 max-w-xs">
                Drag and drop your black & white photo here, or click to browse
            </p>
            <p className="mt-4 text-xs text-slate-500">
                Supports JPG, PNG (Max 10MB)
            </p>
        </div>
    );
};

export default UploadZone;
