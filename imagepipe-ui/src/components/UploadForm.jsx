import React, { useState } from 'react';
import axios from 'axios';

const UploadForm = ({ onTaskSubmitted }) => {
  const [file, setFile] = useState(null);
  const [processType, setProcessType] = useState('convert');
  const [convertType, setConvertType] = useState('.png');
  const [quality, setQuality] = useState(60);
  const [filterType, setFilterType] = useState('BLUR');
  const API_BASE = process.env.REACT_APP_API_BASE || 'http://frontend.railway.internal';

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('process_type', processType);
    if (processType === 'convert') {
      formData.append('convert_type', convertType);
      formData.append('quality', quality);
    }
    if (processType === 'filter') {
      formData.append('filter_type', filterType);
    }
    // ocr has no additional parameters

    try {
      const res = await axios.post(`${API_BASE}/api/upload`, formData, {
        transitional: {
          clarifyTimeoutError: true
        },
        validateStatus: function (status) {
          return status < 500; 
        }
    });
      onTaskSubmitted(res.data.task_id);
    } catch (err) {
      console.error(err);
      alert('Failed to upload file. Please try again.');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 w-full max-w-sm mx-auto p-4 bg-[#eaf5e3] rounded-xl shadow-md flex flex-col items-center">
      <input type="file" onChange={(e) => setFile(e.target.files[0])} className="block w-full text-gray-600 bg-white border border-green-200 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-400" />
      <select value={processType} onChange={(e) => setProcessType(e.target.value)} className="block w-full p-2 border border-green-200 rounded bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-green-900">
        <option value="convert">Convert</option>
        <option value="filter">Filter</option>
        <option value="ocr">OCR</option>
      </select>
      {processType === 'convert' && (
        <div className="space-y-2 w-full">
          <label className="block text-gray-800 font-medium">Target format</label>
          <select value={convertType} onChange={e => setConvertType(e.target.value)} className="block w-full p-2 border border-green-200 rounded bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-green-900">
            <option value=".png">PNG</option>
            <option value=".jpeg">JPEG</option>
            <option value=".gif">GIF</option>
            <option value=".bmp">BMP</option>
          </select>
          <label className="block mt-2 text-gray-800 font-medium">Compress quality (1-95)</label>
          <input type="number" min="1" max="100" value={quality} onChange={e => setQuality(e.target.value)} className="block w-full p-2 border border-green-200 rounded bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-green-900" />
        </div>
      )}
      {processType === 'filter' && (
        <div className="space-y-2 w-full">
          <label className="block text-gray-800 font-medium">Filter type</label>
          <select value={filterType} onChange={e => setFilterType(e.target.value)} className="block w-full p-2 border border-green-200 rounded bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-green-900">
            <option value="BLUR">BLUR</option>
            <option value="CONTOUR">CONTOUR</option>
            <option value="DETAIL">DETAIL</option>
            <option value="SHARPEN">SHARPEN</option>
          </select>
        </div>
      )}
      <button type="submit" className="bg-green-700 hover:bg-green-600 text-white px-6 py-2 rounded-lg font-semibold shadow transition-colors w-full">Upload</button>
    </form>
  );
};

export default UploadForm;
