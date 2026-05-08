import { useEffect, useState } from 'react';

// Mock hook to represent WebSocket subscriptions to task-worker-service progress
export const useBatchJobNotifications = () => {
  const [lastMessage, setLastMessage] = useState<any>(null);

  useEffect(() => {
    // In a real implementation: new WebSocket('ws://gateway/api/v2/ws/batch-jobs')
    console.log("[WebSocket] Connecting to batch job notification stream...");
    
    // Simulating incoming messages for toast notifications
    const mockInterval = setInterval(() => {
      const statuses = ['started', 'progress', 'completed', 'failed'];
      const randomStatus = statuses[Math.floor(Math.random() * statuses.length)];
      
      const evt = {
        type: 'BATCH_JOB',
        jobId: `job_${Math.floor(Math.random() * 1000)}_opta`,
        status: randomStatus,
        progress: randomStatus === 'progress' ? Math.floor(Math.random() * 100) : (randomStatus === 'completed' ? 100 : 0),
        message: `Batch job ${randomStatus}...`
      };
      
      setLastMessage(evt);
      
      // Simulate toast trigger
      if (randomStatus === 'completed') {
        console.log(`🟢 [TOAST SUCCESS]: Job ${evt.jobId} completed successfully!`);
      } else if (randomStatus === 'failed') {
        console.error(`🔴 [TOAST ERROR]: Job ${evt.jobId} failed to import.`);
      }
    }, 30000); // 30 sec interval for mock

    return () => {
      clearInterval(mockInterval);
      console.log("[WebSocket] Disconnecting from batch stream.");
    };
  }, []);

  return { lastMessage };
};
