import React, { useState } from 'react';
import UploadForm from './components/UploadForm';
import StatusDisplay from './components/StatusDisplay';

function App() {
  const [taskId, setTaskId] = useState(null);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#F5F5F5] px-2 py-6">
      <div className="w-full max-w-md mx-auto bg-white/90 rounded-2xl shadow-xl p-6 flex flex-col items-center">
        <h1 className="text-3xl font-bold mb-6 text-center text-green-800 drop-shadow">ImagePipe</h1>
        <UploadForm onTaskSubmitted={setTaskId} />
        <StatusDisplay taskId={taskId} />
      </div>
      <footer className="mt-8 text-green-900 text-xs opacity-70 text-center">&copy; 2025 ImagePipe Demo</footer>
    </div>
  );
}

export default App;
