import React, { useState } from 'react';
import {
  Brain, Play, Pause, Settings, Download, Upload,
  BarChart3, Target, Zap, Activity, TrendingUp,
  Database, Code, Cpu, Eye, RefreshCw, CheckCircle,
  AlertTriangle, XCircle, Clock, Users, Star
} from 'lucide-react';
import { useApi } from '../hooks/useApi'; // Import useApi
import apiService from '../services/api'; // Import apiService
import { MLAlgorithm, MLDataset, MLExperiment } from '../types'; // Import new types
import PotentialChart from './PotentialChart';
import PerformancePrediction from './PerformancePrediction';
import { exportService } from '../services/exportService';

const MLLaboratory: React.FC = () => {
  const [selectedModel, setSelectedModel] = useState('potential');
  const [selectedAlgorithm, setSelectedAlgorithm] = useState<string>('');
  const [selectedDataset, setSelectedDataset] = useState<string>('');
  const [isTraining, setIsTraining] = useState(false);
  const [trainingProgress, setTrainingProgress] = useState(0);
  // const [activeExperiment, setActiveExperiment] = useState(null); // Not used currently

  // Fetch data using useApi
  const { data: algorithms, loading: algorithmsLoading, error: algorithmsError } = useApi<MLAlgorithm[]>(
    () => apiService.getMLAlgorithms(), []
  );
  const { data: datasets, loading: datasetsLoading, error: datasetsError } = useApi<MLDataset[]>(
    () => apiService.getMLDatasets(), []
  );
  const { data: experiments, loading: experimentsLoading, error: experimentsError } = useApi<MLExperiment[]>(
    () => apiService.getMLExperiments(), []
  );

  const models = [
    { id: 'potential', name: 'Player Potential', icon: Star },
    { id: 'performance', name: 'Performance Prediction', icon: Activity },
    { id: 'injury', name: 'Injury Risk Analysis', icon: Target },
    { id: 'market', name: 'Market Value Prediction', icon: TrendingUp },
  ];

  const startTraining = () => {
    setIsTraining(true);
    setTrainingProgress(0);
    
    const interval = setInterval(() => {
      setTrainingProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsTraining(false);
          return 100;
        }
        return prev + Math.random() * 10;
      });
    }, 500);
  };

  const selectedAlgorithmData = algorithms?.find(alg => alg.id === selectedAlgorithm);
  const selectedDatasetData = datasets?.find(ds => ds.id === selectedDataset);

  const handleExport = async () => {
    if (!experiments || experiments.length === 0) {
      alert('No experiments to export');
      return;
    }

    const exportData = experiments.map(exp => ({
      Experiment: exp.name,
      Algorithm: exp.algorithm,
      Dataset: exp.dataset,
      Status: exp.status,
      Accuracy: exp.accuracy > 0 ? `${exp.accuracy}%` : '-',
      Runtime: exp.runtime,
      Created: exp.created,
    }));

    try {
      await exportService.export({
        format: 'pdf',
        fileName: `ml_experiments_${Date.now()}.pdf`,
        data: exportData,
        header: 'ML Laboratory - Experiment History',
        branding: {
          companyName: 'ScoutPro',
          colors: { primary: '#10b981' },
        },
      });
      alert('ML experiments exported successfully!');
    } catch (error) {
      console.error('Export error:', error);
      alert('Export failed. Please try again.');
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center">
          <Brain className="h-8 w-8 mr-3 text-purple-500" />
          ML Laboratory
        </h1>
        <div className="flex items-center space-x-4">
          <button className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors">
            <Upload className="h-4 w-4" />
            <span>Import Dataset</span>
          </button>
          <button onClick={handleExport} className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors">
            <Download className="h-4 w-4" />
            <span>Export Model</span>
          </button>
        </div>
      </div>

      {/* Experiment Setup */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Algorithm Selection */}
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <Cpu className="h-6 w-6 mr-2 text-blue-400" />
            Algorithm Selection
          </h3>
          {algorithmsLoading && <p className="text-slate-400">Loading algorithms...</p>}
          {algorithmsError && <p className="text-red-400">Error: {algorithmsError}</p>}
          {!algorithmsLoading && !algorithmsError && algorithms && (
            <div className="space-y-3">
              {algorithms.map((algorithm) => (
                <div
                  key={algorithm.id}
                  onClick={() => setSelectedAlgorithm(algorithm.id)}
                  className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                    selectedAlgorithm === algorithm.id
                      ? 'border-blue-500 bg-blue-500/10'
                      : 'border-slate-700 hover:border-slate-600'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold">{algorithm.name}</span>
                    <span className="text-xs bg-slate-600 px-2 py-1 rounded">{algorithm.type}</span>
                  </div>
                  <div className="text-sm text-slate-400 mb-2">{algorithm.description}</div>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div>
                      <div className="text-slate-500">Accuracy</div>
                      <div className="font-bold text-green-400">{algorithm.accuracy}%</div>
                    </div>
                    <div>
                      <div className="text-slate-500">Speed</div>
                      <div className="font-bold">{algorithm.speed}</div>
                    </div>
                    <div>
                      <div className="text-slate-500">Interpret</div>
                      <div className="font-bold">{algorithm.interpretability}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Dataset Selection */}
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <Database className="h-6 w-6 mr-2 text-green-400" />
            Dataset Selection
          </h3>
          {datasetsLoading && <p className="text-slate-400">Loading datasets...</p>}
          {datasetsError && <p className="text-red-400">Error: {datasetsError}</p>}
          {!datasetsLoading && !datasetsError && datasets && (
            <div className="space-y-3">
              {datasets.map((dataset) => (
                <div
                  key={dataset.id}
                  onClick={() => setSelectedDataset(dataset.id)}
                  className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                    selectedDataset === dataset.id
                      ? 'border-green-500 bg-green-500/10'
                      : 'border-slate-700 hover:border-slate-600'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-sm">{dataset.name}</span>
                    <span className="text-xs text-green-400">{dataset.quality}% quality</span>
                  </div>
                  <div className="text-xs text-slate-400 mb-2">{dataset.description}</div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <div className="text-slate-500">Size</div>
                      <div className="font-bold">{dataset.size}</div>
                    </div>
                    <div>
                      <div className="text-slate-500">Features</div>
                      <div className="font-bold">{dataset.features}</div>
                    </div>
                  </div>
                  <div className="text-xs text-slate-500 mt-2">
                    Updated: {dataset.lastUpdated}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Configuration & Training */}
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <Settings className="h-6 w-6 mr-2 text-yellow-400" />
            Configuration
          </h3>
          
          {selectedAlgorithmData && (
            <div className="space-y-4">
              <div className="p-4 bg-slate-700 rounded-lg">
                <h4 className="font-semibold mb-3">Algorithm Parameters</h4>
                <div className="space-y-2">
                  {Object.entries(selectedAlgorithmData.parameters).map(([key, value]) => (
                    <div key={key} className="flex justify-between text-sm">
                      <span className="text-slate-400">{key}:</span>
                      <span className="font-mono">{JSON.stringify(value)}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-4 bg-slate-700 rounded-lg">
                <h4 className="font-semibold mb-3">Training Configuration</h4>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm text-slate-400 mb-1">Train/Test Split</label>
                    <select className="w-full px-3 py-2 bg-slate-600 rounded text-sm">
                      <option>80/20</option>
                      <option>70/30</option>
                      <option>90/10</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm text-slate-400 mb-1">Cross Validation</label>
                    <select className="w-full px-3 py-2 bg-slate-600 rounded text-sm">
                      <option>5-Fold</option>
                      <option>10-Fold</option>
                      <option>Leave-One-Out</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm text-slate-400 mb-1">Optimization Metric</label>
                    <select className="w-full px-3 py-2 bg-slate-600 rounded text-sm">
                      <option>Accuracy</option>
                      <option>F1-Score</option>
                      <option>ROC-AUC</option>
                      <option>Mean Squared Error</option>
                    </select>
                  </div>
                </div>
              </div>

              <button
                onClick={startTraining}
                disabled={isTraining}
                className="w-full flex items-center justify-center space-x-2 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-600 rounded-lg font-semibold transition-colors"
              >
                {isTraining ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    <span>Training... {trainingProgress.toFixed(1)}%</span>
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4" />
                    <span>Start Training</span>
                  </>
                )}
              </button>

              {isTraining && (
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div
                    className="bg-purple-400 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${trainingProgress}%` }}
                  ></div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Experiment History */}
      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6 flex items-center">
          <Activity className="h-6 w-6 mr-2 text-green-400" />
          Experiment History
        </h3>
        {experimentsLoading && <p className="text-slate-400">Loading experiments...</p>}
        {experimentsError && <p className="text-red-400">Error: {experimentsError}</p>}
        {!experimentsLoading && !experimentsError && experiments && (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left py-3 px-2">Experiment</th>
                  <th className="text-left py-3 px-2">Algorithm</th>
                  <th className="text-left py-3 px-2">Dataset</th>
                  <th className="text-left py-3 px-2">Status</th>
                  <th className="text-left py-3 px-2">Accuracy</th>
                  <th className="text-left py-3 px-2">Runtime</th>
                  <th className="text-left py-3 px-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {experiments.map((experiment) => (
                  <tr key={experiment.id} className="border-b border-slate-700 hover:bg-slate-700">
                    <td className="py-3 px-2">
                      <div>
                        <div className="font-semibold">{experiment.name}</div>
                        <div className="text-xs text-slate-400">{experiment.created}</div>
                      </div>
                    </td>
                    <td className="py-3 px-2">{experiment.algorithm}</td>
                    <td className="py-3 px-2 text-sm">{experiment.dataset}</td>
                    <td className="py-3 px-2">
                      <div className="flex items-center space-x-2">
                        {experiment.status === 'completed' && <CheckCircle className="h-4 w-4 text-green-400" />}
                        {experiment.status === 'running' && <RefreshCw className="h-4 w-4 text-blue-400 animate-spin" />}
                        {experiment.status === 'failed' && <XCircle className="h-4 w-4 text-red-400" />}
                        <span className={`text-sm capitalize ${
                          experiment.status === 'completed' ? 'text-green-400' :
                          experiment.status === 'running' ? 'text-blue-400' : 'text-red-400'
                        }`}>
                          {experiment.status}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-2">
                      {experiment.accuracy > 0 ? (
                        <span className="font-bold text-green-400">{experiment.accuracy}%</span>
                      ) : (
                        <span className="text-slate-500">-</span>
                      )}
                    </td>
                    <td className="py-3 px-2 text-sm text-slate-400">{experiment.runtime}</td>
                    <td className="py-3 px-2">
                      <div className="flex space-x-2">
                        <button className="px-2 py-1 bg-blue-600 hover:bg-blue-700 rounded text-xs transition-colors">
                          View
                        </button>
                        {experiment.status === 'completed' && (
                          <button className="px-2 py-1 bg-green-600 hover:bg-green-700 rounded text-xs transition-colors">
                            Deploy
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Model Performance Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <BarChart3 className="h-6 w-6 mr-2 text-blue-400" />
            Algorithm Performance Comparison
          </h3>
          {algorithmsLoading && <p className="text-slate-400">Loading algorithms...</p>}
          {algorithmsError && <p className="text-red-400">Error: {algorithmsError}</p>}
          {!algorithmsLoading && !algorithmsError && algorithms && (
            <div className="space-y-4">
              {algorithms.slice(0, 4).map((algorithm) => (
                <div key={algorithm.id} className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">{algorithm.name}</span>
                    <span className="text-sm font-bold text-green-400">{algorithm.accuracy}%</span>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-3">
                    <div
                      className="bg-gradient-to-r from-blue-500 to-green-500 h-3 rounded-full"
                      style={{ width: `${algorithm.accuracy}%` }}
                    ></div>
                  </div>
                  <div className="flex justify-between text-xs text-slate-400">
                    <span>Speed: {algorithm.speed}</span>
                    <span>Interpretability: {algorithm.interpretability}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <Target className="h-6 w-6 mr-2 text-purple-400" />
            Feature Importance Analysis
          </h3>
          {/* This section still uses static data as there's no specific API for feature importance */}
          <div className="space-y-4">
            {[
              { feature: 'Goals per Game', importance: 0.23, impact: 'High' },
              { feature: 'Pass Accuracy', importance: 0.19, impact: 'High' },
              { feature: 'Age', importance: 0.15, impact: 'Medium' },
              { feature: 'League Coefficient', importance: 0.12, impact: 'Medium' },
              { feature: 'Position', importance: 0.10, impact: 'Medium' },
              { feature: 'Contract Length', importance: 0.08, impact: 'Low' },
              { feature: 'Height', importance: 0.05, impact: 'Low' },
              { feature: 'Nationality', importance: 0.04, impact: 'Low' },
            ].map((item, index) => (
              <div key={index} className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm">{item.feature}</span>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-bold">{(item.importance * 100).toFixed(1)}%</span>
                    <span className={`px-2 py-1 rounded text-xs ${
                      item.impact === 'High' ? 'bg-red-600 text-red-100' :
                      item.impact === 'Medium' ? 'bg-yellow-600 text-yellow-100' :
                      'bg-green-600 text-green-100'
                    }`}>
                      {item.impact}
                    </span>
                  </div>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div
                    className="bg-purple-400 h-2 rounded-full"
                    style={{ width: `${item.importance * 100}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Real-time Model Monitoring */}
      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6 flex items-center">
          <Eye className="h-6 w-6 mr-2 text-green-400" />
          Real-time Model Monitoring
        </h3>
        {/* This section still uses static data as there's no specific API for model monitoring */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="p-4 bg-slate-700 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-400">Active Models</span>
              <Activity className="h-4 w-4 text-green-400" />
            </div>
            <div className="text-2xl font-bold text-white">7</div>
            <div className="text-xs text-green-400">All healthy</div>
          </div>
          
          <div className="p-4 bg-slate-700 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-400">Predictions/Hour</span>
              <TrendingUp className="h-4 w-4 text-blue-400" />
            </div>
            <div className="text-2xl font-bold text-white">2.4K</div>
            <div className="text-xs text-blue-400">+12% from yesterday</div>
          </div>
          
          <div className="p-4 bg-slate-700 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-400">Avg Response Time</span>
              <Clock className="h-4 w-4 text-yellow-400" />
            </div>
            <div className="text-2xl font-bold text-white">45ms</div>
            <div className="text-xs text-yellow-400">Within SLA</div>
          </div>
          
          <div className="p-4 bg-slate-700 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-400">Model Accuracy</span>
              <Star className="h-4 w-4 text-purple-400" />
            </div>
            <div className="text-2xl font-bold text-white">94.7%</div>
            <div className="text-xs text-purple-400">Above baseline</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MLLaboratory;