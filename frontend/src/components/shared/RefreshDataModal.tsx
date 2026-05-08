import React, { useState } from 'react';

interface RefreshDataModalProps {
  isOpen: boolean;
  onClose: () => void;
  entityId: string;
  entityType: 'match' | 'player' | 'team';
}

export const RefreshDataModal: React.FC<RefreshDataModalProps> = ({ isOpen, onClose, entityId, entityType }) => {
  const [provider, setProvider] = useState('opta');

  if (!isOpen) return null;

  const handleRefresh = () => {
    console.log(`Triggering refresh for ${entityType} ${entityId} from provider ${provider}`);
    // Simulate triggering a batch backfill/refresh job
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true" onClick={onClose}></div>
        <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
        <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-sm sm:w-full sm:p-6">
          <div>
            <div className="mt-3 text-center sm:mt-5">
              <h3 className="text-lg leading-6 font-medium text-gray-900" id="modal-title">
                Refresh {entityType.toUpperCase()} Data
              </h3>
              <div className="mt-2">
                <p className="text-sm text-gray-500">
                  Select the provider you wish to refresh and backfill data from. This will trigger a background sync.
                </p>
                <div className="mt-4">
                  <select 
                    value={provider} 
                    onChange={e => setProvider(e.target.value)}
                    className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                  >
                    <option value="opta">Opta</option>
                    <option value="statsbomb">StatsBomb</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
          <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
            <button type="button" onClick={handleRefresh} className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:col-start-2 sm:text-sm">
              Sync Data
            </button>
            <button type="button" onClick={onClose} className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:col-start-1 sm:text-sm">
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
