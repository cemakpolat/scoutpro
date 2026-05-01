import sys
import re

filepath = "frontend/src/components/PlayerDetail.tsx"
with open(filepath, 'r') as f:
    content = f.read()

# 1. State + Effect logic
state_injection = "const [formData, setFormData] = useState<any>(null);"
if state_injection not in content:
    content = content.replace(
        "const [expectedMetrics, setExpectedMetrics] = useState<any>(null);",
        "const [expectedMetrics, setExpectedMetrics] = useState<any>(null);\n  const [formData, setFormData] = useState<any>(null);"
    )

fetch_injection = """
        // Fetch ML form data
        try {
          const formRes = await fetch(`http://localhost:3001/api/ml/form/${player.id}`);
          const fd = await formRes.json();
          if (fd && fd.success && fd.data) {
            setFormData(fd.data);
          }
        } catch(e) {}
"""
if "http://localhost:3001/api/ml/form/" not in content:
    content = content.replace(
        "// Parallel fetch for Enhanced Strategy Metrics",
        fetch_injection + "\n        // Parallel fetch for Enhanced Strategy Metrics"
    )

ui_injection = """
        {/* Phase 4 Form Widget */}
        {formData && (
          <div className="bg-slate-800 rounded-lg shadow-sm border-t-4 border-indigo-500 p-6 mb-6">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center">
              <TrendingUp className="h-5 w-5 text-indigo-400 mr-2" />
              Live Form Momentum (ML)
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-slate-700/50 rounded-lg p-4 text-center">
                <p className="text-sm text-slate-400 font-medium">Matches</p>
                <p className="text-2xl font-bold text-white mt-1">{formData.matches_played || 0}</p>
              </div>
              <div className="bg-slate-700/50 rounded-lg p-4 text-center">
                <p className="text-sm text-slate-400 font-medium">Rolling xG</p>
                <p className="text-2xl font-bold text-indigo-400 mt-1">{(formData.rolling_xg || 0).toFixed(2)}</p>
              </div>
              <div className="bg-slate-700/50 rounded-lg p-4 text-center">
                <p className="text-sm text-slate-400 font-medium">xG Momentum</p>
                <p className={`text-2xl font-bold mt-1 ${(formData.momentum_xg || 0) > 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {(formData.momentum_xg || 0) > 0 ? '+' : ''}{(formData.momentum_xg || 0).toFixed(2)}
                </p>
              </div>
              <div className="bg-slate-700/50 rounded-lg p-4 text-center">
                <p className="text-sm text-slate-400 font-medium">Rolling Pass Acc</p>
                <p className="text-2xl font-bold text-sky-400 mt-1">{((formData.rolling_pass_accuracy || 0) * 100).toFixed(1)}%</p>
              </div>
            </div>
          </div>
        )}
"""

if "Phase 4 Form Widget" not in content:
    content = content.replace(
        '<div className="mt-8 space-y-8">',
        '<div className="mt-8 space-y-8">\n' + ui_injection
    )

with open(filepath, 'w') as f:
    f.write(content)
print("v3 patch done")
