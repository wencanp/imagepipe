import React, { useEffect, useState } from 'react';
import axios from 'axios';

const StatusDisplay = ({ taskId }) => {
  const [status, setStatus] = useState(null);

  useEffect(() => {
    if (!taskId) return;

    const interval = setInterval(async () => {
      try {
        // const res = await axios.get(`http://localhost:5000/status/${taskId}`);
        const res = await axios.get(`/api/status/${taskId}`);
        setStatus(res.data);
        if (res.data.state === 'SUCCESS' || res.data.state === 'FAILURE') {
          clearInterval(interval);
        }
      } catch (err) {
        console.error('Failed to check status', err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [taskId]);

  if (!taskId) return null;
  if (!status) return <p>Checking...</p>;

  return (
    <div className="mt-4">
      <p>Status: {status.state}</p>
      {status.result && (
        <a href={status.result.url || status.result} target="_blank" rel="noreferrer" className="text-blue-600 underline">
          Download the result
        </a>
      )}
      {status.error && <p className="text-red-500">{status.error}</p>}
    </div>
  );
};

export default StatusDisplay;
