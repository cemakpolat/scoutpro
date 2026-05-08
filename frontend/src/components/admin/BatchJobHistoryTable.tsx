import React, { useState, useEffect } from 'react';

interface BatchJob {
  job_id: string;
  status: string;
  progress?: number;
  request?: {
    provider: string;
    resource_type: string;
    start_date: string;
    end_date: string;
  };
}

export const BatchJobHistoryTable = () => {
  const [jobs, setJobs] = useState<BatchJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const response = await fetch('/api/v2/batch-jobs');
        if (!response.ok) {
          throw new Error(`Failed to fetch jobs: ${response.statusText}`);
        }
        const data = await response.json();
        
        // Handle both direct array response and wrapped response
        const jobsList = Array.isArray(data) ? data : (data.jobs || []);
        setJobs(jobsList);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch batch jobs');
        console.error('Error fetching batch jobs:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchJobs();

    // Poll for updates every 5 seconds
    const interval = setInterval(fetchJobs, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="bg-white shadow overflow-hidden sm:rounded-md p-6 text-center text-gray-500">
        Loading batch jobs...
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white shadow overflow-hidden sm:rounded-md p-6 text-center text-red-500">
        {error}
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <div className="bg-white shadow overflow-hidden sm:rounded-md p-6 text-center text-gray-500">
        No batch jobs yet. Create one using the form above.
      </div>
    );
  }

  return (
    <div className="bg-white shadow overflow-hidden sm:rounded-md">
      <ul role="list" className="divide-y divide-gray-200">
        {jobs.map((job) => (
          <li key={job.job_id}>
            <div className="px-4 py-4 sm:px-6">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-indigo-600 truncate">{job.job_id}</p>
                <div className="ml-2 flex-shrink-0 flex">
                  <p className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                    ${job.status === 'completed' ? 'bg-green-100 text-green-800' : 
                      job.status === 'in_progress' || job.status === 'pending' ? 'bg-blue-100 text-blue-800' : 
                      'bg-red-100 text-red-800'}`}>
                    {job.status.replace('_', ' ').toUpperCase()}
                  </p>
                </div>
              </div>
              <div className="mt-2 sm:flex sm:justify-between">
                <div className="sm:flex">
                  <p className="flex items-center text-sm text-gray-500">
                    Provider: <span className="font-bold ml-1 uppercase">{job.request?.provider || 'N/A'}</span>
                  </p>
                  <p className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0 sm:ml-6">
                    Resource: <span className="capitalize ml-1">{job.request?.resource_type || 'N/A'}</span>
                  </p>
                </div>
                <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                  <p>
                    Period: {job.request?.start_date} to {job.request?.end_date}
                  </p>
                </div>
              </div>
              {job.status === 'in_progress' && job.progress !== undefined && (
                <div className="mt-4 w-full bg-gray-200 rounded-full h-2.5">
                  <div className="bg-blue-600 h-2.5 rounded-full" style={{ width: `${job.progress}%` }}></div>
                </div>
              )}
              {job.status === 'failed' && (
                <div className="mt-2 text-right">
                  <button 
                    onClick={() => console.log(`Triggering retry for job ${job.job_id}`)}
                    className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded shadow-sm text-white bg-red-600 hover:bg-red-700"
                  >
                    Retry Job
                  </button>
                </div>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};
