import { MLAlgorithm, MLDataset, MLExperiment } from '../types';

export const mockMLAlgorithms: MLAlgorithm[] = [
  {
    id: 'rf-001',
    name: 'Random Forest',
    type: 'Ensemble',
    description: 'Ensemble learning method using multiple decision trees',
    accuracy: 87.5,
    speed: 'Fast',
    interpretability: 'Medium',
    bestFor: ['Classification', 'Feature Importance'],
    parameters: {
      n_estimators: 100,
      max_depth: 10,
      min_samples_split: 2,
      criterion: 'gini'
    }
  },
  {
    id: 'xgb-001',
    name: 'XGBoost',
    type: 'Gradient Boosting',
    description: 'Optimized distributed gradient boosting library',
    accuracy: 91.2,
    speed: 'Medium',
    interpretability: 'Medium',
    bestFor: ['Regression', 'Classification', 'Ranking'],
    parameters: {
      max_depth: 6,
      learning_rate: 0.1,
      n_estimators: 200,
      objective: 'reg:squarederror'
    }
  },
  {
    id: 'nn-001',
    name: 'Neural Network',
    type: 'Deep Learning',
    description: 'Multi-layer perceptron with backpropagation',
    accuracy: 89.8,
    speed: 'Slow',
    interpretability: 'Low',
    bestFor: ['Complex Patterns', 'High Dimensional Data'],
    parameters: {
      hidden_layers: [128, 64, 32],
      activation: 'relu',
      learning_rate: 0.001,
      epochs: 100
    }
  },
  {
    id: 'lr-001',
    name: 'Linear Regression',
    type: 'Linear Model',
    description: 'Simple linear approach for continuous predictions',
    accuracy: 76.3,
    speed: 'Very Fast',
    interpretability: 'High',
    bestFor: ['Linear Relationships', 'Quick Baseline'],
    parameters: {
      fit_intercept: true,
      normalize: false,
      regularization: 'none'
    }
  },
  {
    id: 'svm-001',
    name: 'Support Vector Machine',
    type: 'Kernel Method',
    description: 'Finds optimal hyperplane for classification',
    accuracy: 84.7,
    speed: 'Medium',
    interpretability: 'Low',
    bestFor: ['High Dimensional', 'Non-linear Boundaries'],
    parameters: {
      kernel: 'rbf',
      C: 1.0,
      gamma: 'scale',
      degree: 3
    }
  }
];

export const mockMLDatasets: MLDataset[] = [
  {
    id: 'ds-player-stats',
    name: 'Player Performance Dataset',
    size: '2.3 GB',
    records: '15,000',
    features: 47,
    timespan: '5 seasons',
    description: 'Comprehensive player statistics across multiple leagues',
    quality: 94,
    lastUpdated: '2 hours ago'
  },
  {
    id: 'ds-match-events',
    name: 'Match Events Dataset',
    size: '4.1 GB',
    records: '250,000',
    features: 35,
    timespan: '3 seasons',
    description: 'Detailed match event data including passes, shots, and tackles',
    quality: 91,
    lastUpdated: '5 hours ago'
  },
  {
    id: 'ds-market-values',
    name: 'Transfer Market Dataset',
    size: '890 MB',
    records: '50,000',
    features: 28,
    timespan: '10 years',
    description: 'Historical transfer market valuations and trends',
    quality: 88,
    lastUpdated: '1 day ago'
  },
  {
    id: 'ds-tactical',
    name: 'Tactical Patterns Dataset',
    size: '1.7 GB',
    records: '8,500',
    features: 62,
    timespan: '2 seasons',
    description: 'Team formations, pressing patterns, and positional data',
    quality: 96,
    lastUpdated: '3 hours ago'
  },
  {
    id: 'ds-injury-risk',
    name: 'Injury Risk Dataset',
    size: '450 MB',
    records: '12,000',
    features: 31,
    timespan: '7 seasons',
    description: 'Player injury history and workload metrics',
    quality: 85,
    lastUpdated: '6 hours ago'
  }
];

export const mockMLExperiments: MLExperiment[] = [
  {
    id: 'exp-001',
    name: 'Player Potential v3.2',
    algorithm: 'XGBoost',
    dataset: 'Player Performance Dataset',
    status: 'completed',
    accuracy: 91.2,
    runtime: '3m 42s',
    created: '2 hours ago',
    insights: [
      'Strong correlation between age and potential growth',
      'League coefficient is a key predictor',
      'Model performs better for attacking players'
    ]
  },
  {
    id: 'exp-002',
    name: 'Market Value Predictor',
    algorithm: 'Neural Network',
    dataset: 'Transfer Market Dataset',
    status: 'completed',
    accuracy: 88.7,
    runtime: '12m 18s',
    created: '5 hours ago',
    insights: [
      'Goals per game most influential for forwards',
      'Pass accuracy critical for midfielders',
      'Age shows non-linear relationship'
    ]
  },
  {
    id: 'exp-003',
    name: 'Injury Risk Analysis',
    algorithm: 'Random Forest',
    dataset: 'Injury Risk Dataset',
    status: 'running',
    accuracy: 0,
    runtime: '1m 35s',
    created: '10 minutes ago',
    insights: []
  },
  {
    id: 'exp-004',
    name: 'Performance Prediction Q1',
    algorithm: 'SVM',
    dataset: 'Match Events Dataset',
    status: 'completed',
    accuracy: 84.3,
    runtime: '8m 51s',
    created: '1 day ago',
    insights: [
      'Previous match performance highly predictive',
      'Home advantage varies by league',
      'Weather conditions show minimal impact'
    ]
  },
  {
    id: 'exp-005',
    name: 'Tactical Pattern Recognition',
    algorithm: 'Neural Network',
    dataset: 'Tactical Patterns Dataset',
    status: 'failed',
    accuracy: 0,
    runtime: '0m 0s',
    created: '3 days ago',
    insights: []
  },
  {
    id: 'exp-006',
    name: 'Transfer Target Finder',
    algorithm: 'XGBoost',
    dataset: 'Player Performance Dataset',
    status: 'completed',
    accuracy: 89.5,
    runtime: '5m 23s',
    created: '1 week ago',
    insights: [
      'Position-specific metrics crucial',
      'Contract length affects value significantly',
      'International experience adds premium'
    ]
  }
];
