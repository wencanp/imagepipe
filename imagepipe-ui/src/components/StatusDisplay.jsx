import React, { useEffect, useState, useRef } from 'react';
import axios from 'axios';

const StatusDisplay = ({ taskId }) => {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (!taskId) return;
    // clean up previous interval
    if (intervalRef.current) clearInterval(intervalRef.current);

    const checkStatus = async () => {
      try {
        const res = await axios.get(`/api/status/${taskId}`);
        setStatus(res.data);
        if (res.data.message === 'SUCCESS' || res.data.message === 'FAILED') {
          if (intervalRef.current) clearInterval(intervalRef.current);
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
  if (error) return <p className="text-red-500">{error}</p>;
  if (!status) return <p>Pending...</p>;

  return (
    <div className="mt-4">
      <p>Status: {status.message}</p>
      {status.url && (
        <a href={status.url} download target="_blank" rel="noreferrer" className="text-blue-600 underline">
          Download the result
        </a>
      )}
    </div>
  );
};

export default StatusDisplay;
