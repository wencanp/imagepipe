import React, { useEffect, useState, useRef } from 'react';
import axios from 'axios';

const StatusDisplay = ({ taskId }) => {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [downloadUrl, setDownloadUrl] = useState(null);
  const intervalRef = useRef(null);
  const API_BASE = process.env.REACT_APP_API_BASE;

  useEffect(() => {
    if (!taskId) return;
    // clean up previous interval
    if (intervalRef.current) clearInterval(intervalRef.current);

    const checkStatus = async () => {
      try {
        const res = await axios.get(`${API_BASE}/api/status/${taskId}`);
        setStatus(res.data);
        if (res.data.message === 'SUCCESS') {
          setDownloadUrl(`${API_BASE}/api/download/task/${taskId}`);
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        } else if (res.data.message === 'FAILED') {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      } catch (err) {
        setError('Failed to fetch status');
        if (intervalRef.current) clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };

    intervalRef.current = setInterval(checkStatus, 2000);
    checkStatus();

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = null;
    };
  }, [taskId]);

  if (!taskId) return null;
  if (error) return <p className="text-red-500 text-center mt-4">{error}</p>;
  if (!status) return <p className="text-gray-900 text-center mt-4">Pending...</p>;

  return (
    <div className="w-full max-w-sm mx-auto mt-6 p-4 bg-[#eaf5e3] rounded-xl shadow flex flex-col items-center">
      <p className="text-green-800 font-semibold mb-2">Status: {status.message}</p>
      {downloadUrl === 'SUCCESS' && (
        <a href={downloadUrl} download target="_blank" rel="noreferrer" className="bg-green-700 hover:bg-green-600 text-white px-4 py-2 rounded-lg font-semibold shadow transition-colors mt-2">
          Download the result
        </a>
      )}
    </div>
  );
};

export default StatusDisplay;
