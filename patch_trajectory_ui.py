import re

with open('frontend/src/components/PlayerTrajectory.tsx', 'r') as f:
    content = f.read()

# Interface updates
old_interface = """interface TrajectoryData {
  player_id: string;
  history: Array<{
    season: string;
    metrics: Record<string, number>;
    cluster: {
      cluster_id: number;
      cluster_name: string;
      confidence: number;
    };
  }>;
  forecast: Array<{
    season: string;
    predicted_cluster: {
      cluster_id: number;
      cluster_name: string;
      confidence: number;
    };
    confidence_band: {
      lower: number;
      upper: number;
    };
  }>;
  comparable_players: Array<{
    player_id: string;
    similarity: number;
  }>;
}"""

new_interface = """interface TrajectoryData {
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
}"""

content = content.replace(old_interface, new_interface)

# Transform data updates
old_transform = """  const chartData = [
    ...data.history.map((h, i) => ({
      season: h.season,
      confidence: h.cluster.confidence,
      type: 'history',
      cluster_name: h.cluster.cluster_name,
      lower: h.cluster.confidence - 0.05,
      upper: h.cluster.confidence + 0.05
    })),
    ...data.forecast.map((f, i) => ({
      season: f.season,
      confidence: f.predicted_cluster.confidence,
      type: 'forecast',
      cluster_name: f.predicted_cluster.cluster_name,
      lower: f.confidence_band.lower,
      upper: f.confidence_band.upper
    }))
  ];"""

new_transform = """  const chartData = [
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
  ];"""

content = content.replace(old_transform, new_transform)

# Peer map updates
content = content.replace("data.comparable_players.map((peer, idx) => (", "data.baseline_peers.map((peer, idx) => (")
content = content.replace("{peer.player_id}", "{peer.name}")
content = content.replace("peer.similarity", "peer.similarity_score")

# Table updates
old_table_body = """            <tbody className="divide-y divide-gray-100">
                {data.history.map((h, i) => (
                    <tr key={`h-${i}`}>
                        <td className="px-6 py-4 font-medium">{h.season}</td>
                        <td className="px-6 py-4">
                            <span className="px-2.5 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-medium">
                                {h.cluster.cluster_name}
                            </span>
                        </td>
                        <td className="px-6 py-4">{(h.cluster.confidence * 100).toFixed(1)}%</td>
                        <td className="px-6 py-4 text-gray-500 flex items-center gap-1"><CheckCircle2 className="w-4 h-4 text-green-500"/> Historical</td>
                    </tr>
                ))}
                {data.forecast.map((f, i) => (
                    <tr key={`f-${i}`} className="bg-indigo-50/10">
                        <td className="px-6 py-4 font-medium text-indigo-900">{f.season}</td>
                        <td className="px-6 py-4">
                            <span className="px-2.5 py-1 bg-indigo-100 text-indigo-800 rounded-full text-xs font-medium border border-indigo-200">
                                {f.predicted_cluster.cluster_name}
                            </span>
                        </td>
                        <td className="px-6 py-4">{(f.predicted_cluster.confidence * 100).toFixed(1)}%</td>
                        <td className="px-6 py-4 text-indigo-500 flex items-center gap-1">Forecast</td>
                    </tr>
                ))}
            </tbody>"""

new_table_body = """            <tbody className="divide-y divide-gray-100">
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
            </tbody>"""

content = content.replace(old_table_body, new_table_body)

with open('frontend/src/components/PlayerTrajectory.tsx', 'w') as f:
    f.write(content)
