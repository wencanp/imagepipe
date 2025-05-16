import React, { useEffect, useState } from 'react';
import axios from 'axios';

const StatusDisplay = ({ taskId }) => {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!taskId) return;
    let interval;

    const checkStatus = async () => {
      try {
        // check the status
        const res = await axios.get(`/api/status/${taskId}`);
        setStatus(res.data);
        if (res.data.message === 'SUCCESS' || res.data.message === 'FAILED') {
          clearInterval(interval);
        }
      } catch (err) {
        setError('Failed to fetch status');
        clearInterval(interval);
      }
    };

    interval = setInterval(checkStatus, 2000);
    checkStatus();

    return () => clearInterval(interval);
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
