import React, { useState } from 'react';
import { FileText, Download, Share2, BookTemplate as Template, Wand2, BarChart3, Users, Target, TrendingUp, Eye } from 'lucide-react';
import { exportService } from '../services/exportService';

const ReportBuilder: React.FC = () => {
  const [selectedTemplate, setSelectedTemplate] = useState('player-analysis');
  const [reportTitle, setReportTitle] = useState('Player Analysis Report');
  const [targetPlayer, setTargetPlayer] = useState('Kylian Mbappé');
  const [timePeriod, setTimePeriod] = useState('Current Season');
  const [comparisonPlayers, setComparisonPlayers] = useState<string[]>([]);

  const templates = [
    {
      id: 'player-analysis',
      name: 'Player Analysis',
      description: 'Comprehensive individual player evaluation',
      sections: ['Performance Metrics', 'Strengths & Weaknesses', 'Market Value', 'Recommendations'],
      icon: Users,
      premium: false,
    },
    {
      id: 'team-tactical',
      name: 'Team Tactical Report',
      description: 'In-depth tactical analysis of team performance',
      sections: ['Formation Analysis', 'Playing Style', 'Key Players', 'Tactical Recommendations'],
      icon: Target,
      premium: false,
    },
    {
      id: 'market-intelligence',
      name: 'Market Intelligence',
      description: 'Transfer market insights and valuations',
      sections: ['Market Trends', 'Player Valuations', 'Transfer Predictions', 'Investment Opportunities'],
      icon: TrendingUp,
      premium: true,
    },
    {
      id: 'match-analysis',
      name: 'Match Analysis',
      description: 'Detailed post-match performance breakdown',
      sections: ['Key Events', 'Player Ratings', 'Tactical Analysis', 'Performance Insights'],
      icon: BarChart3,
      premium: false,
    },
  ];

  const reportSections = [
    {
      id: 'executive-summary',
      title: 'Executive Summary',
      content: 'AI-generated overview of key findings and recommendations',
      status: 'completed',
    },
    {
      id: 'performance-metrics',
      title: 'Performance Metrics',
      content: 'Statistical analysis and performance indicators',
      status: 'completed',
    },
    {
      id: 'tactical-analysis',
      title: 'Tactical Analysis',
      content: 'Playing style, positioning, and tactical contributions',
      status: 'in-progress',
    },
    {
      id: 'market-valuation',
      title: 'Market Valuation',
      content: 'Current market value and transfer predictions',
      status: 'pending',
    },
    {
      id: 'recommendations',
      title: 'Recommendations',
      content: 'Strategic recommendations and next steps',
      status: 'pending',
    },
  ];

  const handleExport = async () => {
    const selectedTemplateData = templates.find(t => t.id === selectedTemplate);

    const exportData = reportSections.map(section => ({
      Section: section.title,
      Status: section.status,
      Content: section.content,
    }));

    try {
      await exportService.export({
        format: 'pdf',
        fileName: `${reportTitle.replace(/\s+/g, '_')}_${Date.now()}.pdf`,
        data: exportData,
        header: reportTitle,
        branding: {
          companyName: 'ScoutPro',
          colors: { primary: '#10b981' },
        },
      });
      alert('Report exported successfully!');
    } catch (error) {
      console.error('Export error:', error);
      alert('Export failed. Please try again.');
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center">
          <FileText className="h-8 w-8 mr-3 text-green-500" />
          Report Builder
        </h1>
        <div className="flex items-center space-x-4">
          <button
            onClick={() => {
              alert('🤖 AI Report Generation\n\nGenerating comprehensive report for ' + targetPlayer + '...\n\nAnalyzing:\n- Performance metrics\n- Tactical contributions\n- Market value trends\n- Recommendations\n\n(AI generation will be available once backend is connected)');
            }}
            className="flex items-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors"
          >
            <Wand2 className="h-4 w-4" />
            <span>AI Generate</span>
          </button>
          <button onClick={handleExport} className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors">
            <Download className="h-4 w-4" />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* Template Selection */}
      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6 flex items-center">
          <Template className="h-6 w-6 mr-2 text-blue-400" />
          Choose Report Template
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {templates.map((template) => {
            const Icon = template.icon;
            return (
              <div
                key={template.id}
                onClick={() => setSelectedTemplate(template.id)}
                className={`p-6 rounded-xl border-2 cursor-pointer transition-all ${
                  selectedTemplate === template.id
                    ? 'border-blue-500 bg-blue-500/10'
                    : 'border-slate-700 hover:border-slate-600'
                }`}
              >
                <div className="flex items-center justify-between mb-4">
                  <Icon className={`h-8 w-8 ${
                    selectedTemplate === template.id ? 'text-blue-400' : 'text-slate-400'
                  }`} />
                  {template.premium && (
                    <span className="px-2 py-1 bg-yellow-600 text-yellow-100 text-xs rounded">
                      Premium
                    </span>
                  )}
                </div>
                <h4 className="font-semibold mb-2">{template.name}</h4>
                <p className="text-sm text-slate-400 mb-4">{template.description}</p>
                <div className="space-y-1">
                  {template.sections.map((section, index) => (
                    <div key={index} className="text-xs text-slate-500">
                      • {section}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Report Configuration */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-xl font-semibold mb-6">Report Configuration</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Report Title</label>
                <input
                  type="text"
                  value={reportTitle}
                  onChange={(e) => setReportTitle(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Target Player</label>
                <select
                  value={targetPlayer}
                  onChange={(e) => setTargetPlayer(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg"
                >
                  <option>Kylian Mbappé</option>
                  <option>Erling Haaland</option>
                  <option>Pedri González</option>
                  <option>Jude Bellingham</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Time Period</label>
                <select
                  value={timePeriod}
                  onChange={(e) => setTimePeriod(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg"
                >
                  <option>Current Season</option>
                  <option>Last 6 Months</option>
                  <option>Last 12 Months</option>
                  <option>Career Overview</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Comparison Players</label>
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={comparisonPlayers.includes('Neymar Jr')}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setComparisonPlayers([...comparisonPlayers, 'Neymar Jr']);
                        } else {
                          setComparisonPlayers(comparisonPlayers.filter(p => p !== 'Neymar Jr'));
                        }
                      }}
                      className="rounded"
                    />
                    <span className="text-sm">Neymar Jr</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={comparisonPlayers.includes('Vinícius Jr')}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setComparisonPlayers([...comparisonPlayers, 'Vinícius Jr']);
                        } else {
                          setComparisonPlayers(comparisonPlayers.filter(p => p !== 'Vinícius Jr'));
                        }
                      }}
                      className="rounded"
                    />
                    <span className="text-sm">Vinícius Jr</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={comparisonPlayers.includes('Mohamed Salah')}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setComparisonPlayers([...comparisonPlayers, 'Mohamed Salah']);
                        } else {
                          setComparisonPlayers(comparisonPlayers.filter(p => p !== 'Mohamed Salah'));
                        }
                      }}
                      className="rounded"
                    />
                    <span className="text-sm">Mohamed Salah</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-xl font-semibold mb-6">AI Narrative Generator</h3>
            <div className="space-y-4">
              <div className="p-4 bg-purple-600/10 border border-purple-600/20 rounded-lg">
                <div className="flex items-center space-x-2 mb-2">
                  <Wand2 className="h-5 w-5 text-purple-400" />
                  <span className="font-semibold text-purple-400">AI Summary</span>
                </div>
                <p className="text-sm text-slate-300">
                  "Mbappé demonstrates exceptional pace and finishing ability, consistently 
                  outperforming xG metrics. His versatility across front positions makes him 
                  a valuable tactical asset."
                </p>
              </div>
              
              <button
                onClick={() => {
                  alert('🤖 Generating new AI summary for ' + targetPlayer + '...\n\n(AI summary generation will be available once backend is connected)');
                }}
                className="w-full bg-purple-600 hover:bg-purple-700 py-2 rounded-lg text-sm font-medium transition-colors"
              >
                Generate New Summary
              </button>
            </div>
          </div>
        </div>

        {/* Report Preview */}
        <div className="lg:col-span-2">
          <div className="bg-slate-800 rounded-xl p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold">Report Preview</h3>
              <div className="flex items-center space-x-2">
                <Eye className="h-5 w-5 text-slate-400" />
                <span className="text-sm text-slate-400">Live Preview</span>
              </div>
            </div>
            
            {/* Report Header */}
            <div className="border-b border-slate-700 pb-6 mb-6">
              <h1 className="text-2xl font-bold mb-2">{reportTitle}</h1>
              <div className="flex items-center space-x-4 text-sm text-slate-400">
                <span>Generated: {new Date().toLocaleDateString()}</span>
                <span>•</span>
                <span>Player: Kylian Mbappé</span>
                <span>•</span>
                <span>Period: Current Season</span>
              </div>
            </div>

            {/* Report Sections */}
            <div className="space-y-6">
              {reportSections.map((section) => (
                <div key={section.id} className="border border-slate-700 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-semibold">{section.title}</h4>
                    <span className={`px-2 py-1 rounded text-xs ${
                      section.status === 'completed' ? 'bg-green-600 text-green-100' :
                      section.status === 'in-progress' ? 'bg-yellow-600 text-yellow-100' :
                      'bg-slate-600 text-slate-100'
                    }`}>
                      {section.status.replace('-', ' ')}
                    </span>
                  </div>
                  <p className="text-sm text-slate-400">{section.content}</p>
                  
                  {section.status === 'completed' && (
                    <div className="mt-4 p-3 bg-slate-700 rounded">
                      <div className="text-sm">
                        {section.id === 'executive-summary' && (
                          <div>
                            <p className="mb-2">
                              <strong>Key Finding:</strong> Mbappé's performance metrics indicate 
                              elite-level consistency with 94% shot accuracy and 2.1 goals per game.
                            </p>
                            <p>
                              <strong>Recommendation:</strong> Immediate acquisition recommended 
                              based on current form and market value trajectory.
                            </p>
                          </div>
                        )}
                        {section.id === 'performance-metrics' && (
                          <div className="grid grid-cols-3 gap-4">
                            <div className="text-center">
                              <div className="text-lg font-bold text-green-400">2.1</div>
                              <div className="text-xs text-slate-400">Goals/Game</div>
                            </div>
                            <div className="text-center">
                              <div className="text-lg font-bold text-blue-400">1.3</div>
                              <div className="text-xs text-slate-400">Assists/Game</div>
                            </div>
                            <div className="text-center">
                              <div className="text-lg font-bold text-yellow-400">94%</div>
                              <div className="text-xs text-slate-400">Shot Accuracy</div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-between mt-8 pt-6 border-t border-slate-700">
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => {
                    alert('📤 Share Report\n\nShare "' + reportTitle + '" with team members.\n\n(Sharing will be available once backend is connected)');
                  }}
                  className="flex items-center space-x-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
                >
                  <Share2 className="h-4 w-4" />
                  <span>Share</span>
                </button>
                <button
                  onClick={() => {
                    alert('💾 Save as Template\n\nSaving "' + reportTitle + '" as a reusable template...\n\n(Template saving will be available once backend is connected)');
                  }}
                  className="flex items-center space-x-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
                >
                  <Template className="h-4 w-4" />
                  <span>Save as Template</span>
                </button>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleExport}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
                >
                  Generate PDF
                </button>
                <button
                  onClick={() => {
                    alert('📢 Publish Report\n\nPublishing "' + reportTitle + '" to your team dashboard...\n\n(Publishing will be available once backend is connected)');
                  }}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
                >
                  Publish Report
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Template Marketplace */}
      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6 flex items-center">
          <Template className="h-6 w-6 mr-2 text-green-400" />
          Template Marketplace
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { name: 'Premier League Scout Report', author: 'Manchester City FC', price: '€29', rating: 4.8 },
            { name: 'Youth Development Analysis', author: 'Ajax Academy', price: '€19', rating: 4.9 },
            { name: 'Set Piece Specialist Report', author: 'Liverpool FC', price: '€15', rating: 4.7 },
          ].map((template, index) => (
            <div key={index} className="p-4 bg-slate-700 rounded-lg">
              <div className="flex justify-between items-start mb-3">
                <h4 className="font-semibold">{template.name}</h4>
                <span className="text-green-400 font-bold">{template.price}</span>
              </div>
              <p className="text-sm text-slate-400 mb-3">by {template.author}</p>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-1">
                  {[1,2,3,4,5].map(star => (
                    <div key={star} className={`w-3 h-3 ${
                      star <= Math.floor(template.rating) ? 'text-yellow-400' : 'text-slate-500'
                    }`}>★</div>
                  ))}
                  <span className="text-sm text-slate-400 ml-1">{template.rating}</span>
                </div>
                <button
                  onClick={() => {
                    alert(`🛒 Purchase Template\n\n"${template.name}"\nBy: ${template.author}\nPrice: ${template.price}\n\n(Template marketplace will be available once backend is connected)`);
                  }}
                  className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm transition-colors"
                >
                  Purchase
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ReportBuilder;