import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, AreaChart, Area, ComposedChart, Bar, Legend, Scatter } from 'recharts';
import { Brain, Filter, Download, ArrowRight, Activity, Target, CheckCircle2 } from 'lucide-react';

interface TrajectoryData {
  player_id: string;
  historical_trajectory: Array<{
    period: string;
    cluster_id: number;
    cluster_name: string;
    metrics_snapshot: Record<string, number>;
  }>;
  forecast: Array<{
    forecast_period: string;
    predicted_cluster_id: number;
    predicted_cluster_name: string;
    confidence_distribution: Record<string, number>;
  }>;
  baseline_peers: Array<{
    player_id: string;
    name: string;
    similarity_score: number;
  }>;
}

export default function PlayerTrajectory({ playerId = 'p123' }: { playerId?: string }) {
  const [data, setData] = useState<TrajectoryData | null>(null);
  const [provider, setProvider] = useState<string>('opta');
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchTrajectory = async () => {
      setLoading(true);
      try {
        const response = await fetch(`/api/players/${playerId}/trajectory?provider=${provider}`);
        if(response.ok) {
           const json = await response.json();
           setData(json);
        } else {
            console.error('Failed to fetch trajectory data');
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchTrajectory();
  }, [playerId, provider]);

  if (loading) return <div className="p-8 text-center text-gray-500">Loading trajectory...</div>;
  if (!data) return <div className="p-8 text-center text-red-500">Failed to load data.</div>;

  // Transform data for charting
  const chartData = [
    ...data.historical_trajectory.map((h, i) => ({
      season: h.period,
      confidence: 1.0, // Historical is certain
      type: 'history',
      cluster_name: h.cluster_name,
      lower: 0.95,
      upper: 1.0
    })),
    ...data.forecast.map((f, i) => {
      // Find the confidence for the predicted class
      const conf = f.confidence_distribution[f.predicted_cluster_name] || 0.5;
      return {
        season: f.forecast_period,
        confidence: conf,
        type: 'forecast',
        cluster_name: f.predicted_cluster_name,
        lower: Math.max(0, conf - 0.2),
        upper: Math.min(1, conf + 0.2)
      };
    })
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Activity className="w-6 h-6 text-blue-500" />
            Player Trajectory & Forecasting
          </h2>
          <p className="text-gray-500">Analysis using Markov-chain clustering across seasons</p>
        </div>
        <div className="flex gap-4 items-center">
            <select 
                value={provider} 
                onChange={(e) => setProvider(e.target.value)}
                className="bg-white border text-sm rounded-lg px-3 py-2"
            >
                <option value="opta">Opta Data</option>
                <option value="statsbomb">StatsBomb Data</option>
                <option value="wyscout">Wyscout Data</option>
            </select>
            <button className="flex items-center gap-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm">
                <Download className="w-4 h-4"/> Export Report
            </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="col-span-2 bg-white rounded-xl shadow-sm border p-6">
            <h3 className="font-semibold mb-4 text-gray-800 flex items-center gap-2">
                <Target className="w-5 h-5 text-indigo-500"/>
                Trajectory Forecast Confidence Bands
            </h3>
            <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={chartData} margin={{top: 5, right: 30, left: 20, bottom: 5}}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB"/>
                        <XAxis dataKey="season" />
                        <YAxis domain={[0, 1]} />
                        <RechartsTooltip />
                        <Legend />
                        <Area type="monotone" dataKey="upper" fill="#818CF8" stroke="none" fillOpacity={0.1} name="Confidence Upper" />
                        <Area type="monotone" dataKey="lower" fill="#fff" stroke="none" fillOpacity={1} name="Confidence Lower" />
                        <Line type="monotone" dataKey="confidence" stroke="#4F46E5" strokeWidth={2} name="Cluster Confidence" dot={{r: 4}} />
                    </ComposedChart>
                </ResponsiveContainer>
            </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border p-6">
            <h3 className="font-semibold mb-4 text-gray-800 flex items-center gap-2">
                <Brain className="w-5 h-5 text-emerald-500"/>
                Comparable Peers
            </h3>
            <div className="space-y-4">
                {data.baseline_peers.map((peer, idx) => (
                    <div key={idx} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                        <span className="font-medium text-gray-700">{peer.name}</span>
                        <div className="flex items-center gap-2">
                            <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                                <div className="h-full bg-emerald-500" style={{width: `${peer.similarity_score * 100}%`}}></div>
                            </div>
                            <span className="text-xs text-gray-500">{(peer.similarity_score * 100).toFixed(0)}%</span>
                        </div>
                    </div>
                ))}
                
                <button className="w-full mt-4 flex items-center justify-center gap-2 text-sm text-indigo-600 font-medium hover:text-indigo-800 py-2 border border-indigo-100 bg-indigo-50/50 rounded-lg transition-colors">
                    Explore Clustering <ArrowRight className="w-4 h-4"/>
                </button>
            </div>
        </div>
      </div>
      
      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        <table className="w-full text-sm text-left">
            <thead className="bg-gray-50 text-gray-600 font-medium border-b text-xs uppercase">
                <tr>
                    <th className="px-6 py-4">Season</th>
                    <th className="px-6 py-4">Cluster Type</th>
                    <th className="px-6 py-4">Confidence</th>
                    <th className="px-6 py-4">Status</th>
                </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
                {data.historical_trajectory.map((h, i) => (
                    <tr key={`h-${i}`}>
                        <td className="px-6 py-4 font-medium">{h.period}</td>
                        <td className="px-6 py-4">
                            <span className="px-2.5 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-medium">
                                {h.cluster_name}
                            </span>
                        </td>
                        <td className="px-6 py-4">100.0%</td>
                        <td className="px-6 py-4 text-gray-500 flex items-center gap-1"><CheckCircle2 className="w-4 h-4 text-green-500"/> Historical</td>
                    </tr>
                ))}
                {data.forecast.map((f, i) => {
                    const conf = f.confidence_distribution[f.predicted_cluster_name] || 0;
                    return (
                        <tr key={`f-${i}`} className="bg-indigo-50/10">
                            <td className="px-6 py-4 font-medium text-indigo-900">{f.forecast_period}</td>
                            <td className="px-6 py-4">
                                <span className="px-2.5 py-1 bg-indigo-100 text-indigo-800 rounded-full text-xs font-medium border border-indigo-200">
                                    {f.predicted_cluster_name}
                                </span>
                            </td>
                            <td className="px-6 py-4">{(conf * 100).toFixed(1)}%</td>
                            <td className="px-6 py-4 text-indigo-500 flex items-center gap-1">Forecast</td>
                        </tr>
                    );
                })}
            </tbody>
        </table>
      </div>
    </div>
  );
}
