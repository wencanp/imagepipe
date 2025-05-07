import React, { useState } from 'react';
import UploadForm from './components/UploadForm';
import StatusDisplay from './components/StatusDisplay';

function App() {
  const [taskId, setTaskId] = useState(null);

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <h1 className="text-3xl font-bold mb-6 text-center">ImagePipe</h1>
      <UploadForm onTaskSubmitted={setTaskId} />
      <StatusDisplay taskId={taskId} />
    </div>
  );
}

export default App;
