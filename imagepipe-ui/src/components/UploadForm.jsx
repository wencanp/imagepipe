import React, { useState } from 'react';
import axios from 'axios';

const UploadForm = ({ onTaskSubmitted }) => {
  const [file, setFile] = useState(null);
  const [processType, setProcessType] = useState('convert');
  const [convertType, setConvertType] = useState('.png');
  const [quality, setQuality] = useState(60);
  const [filterType, setFilterType] = useState('BLUR');

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
      const res = await axios.post("/api/upload", formData);
      onTaskSubmitted(res.data.task_id);
    } catch (err) {
      console.error(err);
      alert('Failed to upload file. Please try again.');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 p-4 bg-white rounded shadow-md">
      <input type="file" onChange={(e) => setFile(e.target.files[0])} className="block w-full" />
      <select value={processType} onChange={(e) => setProcessType(e.target.value)} className="block w-full p-2 border rounded">
        <option value="convert">Convert</option>
        <option value="filter">Filter</option>
        <option value="ocr">OCR</option>
      </select>
      {processType === 'convert' && (
        <div className="space-y-2">
          <label className="block">Target format: </label>
          <select value={convertType} onChange={e => setConvertType(e.target.value)} className="block w-full p-2 border rounded">
            <option value=".png">PNG</option>
            <option value=".jpeg">JPEG</option>
            <option value=".gif">GIF</option>
            <option value=".bmp">BMP</option>
          </select>
          <label className="block mt-2">Compress quality (1-95): </label>
          <input type="number" min="1" max="100" value={quality} onChange={e => setQuality(e.target.value)} className="block w-full p-2 border rounded" />
        </div>
      )}
      {processType === 'filter' && (
        <div className="space-y-2">
          <label className="block">Filter type: </label>
          <select value={filterType} onChange={e => setFilterType(e.target.value)} className="block w-full p-2 border rounded">
            <option value="BLUR">BLUR</option>
            <option value="CONTOUR">CONTOUR</option>
            <option value="DETAIL">DETAIL</option>
            <option value="SHARPEN">SHARPEN</option>
          </select>
        </div>
      )}
      <button type="submit" className="bg-blue-500 text-white px-4 py-2 rounded">Upload</button>
    </form>
  );
};

export default UploadForm;
