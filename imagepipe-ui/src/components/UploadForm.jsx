import React, { useState } from 'react';
import axios from 'axios';

const UploadForm = ({ onTaskSubmitted }) => {
  const [file, setFile] = useState(null);
  const [processType, setProcessType] = useState('compress');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('process_type', processType);
    if (processType === 'filter') formData.append('filter_type', 'SHARPEN');

    try {
      const res = await axios.post('http://localhost:5000/upload', formData);
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
        <option value="compress">Compress</option>
        <option value="filter">Filter</option>
        <option value="ocr">OCR</option>
      </select>
      <button type="submit" className="bg-blue-500 text-white px-4 py-2 rounded">Upload</button>
    </form>
  );
};

export default UploadForm;
