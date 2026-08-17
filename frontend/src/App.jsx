import { useState, useEffect } from 'react';

function App() {
  const [businessDesc, setBusinessDesc] = useState('');
  const [tone, setTone] = useState('Professional');
  const [colors, setColors] = useState('');
  
  const [status, setStatus] = useState('idle');
  const [stateData, setStateData] = useState(null);
  const [isPaused, setIsPaused] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [isRefining, setIsRefining] = useState(false);
  const [previewKey, setPreviewKey] = useState(Date.now());
  const [deviceView, setDeviceView] = useState('desktop');

  // Deployment state
  const [deployModalOpen, setDeployModalOpen] = useState(false);
  const [deployService, setDeployService] = useState('netlify');
  const [deployPlan, setDeployPlan] = useState(null);
  const [deployedResult, setDeployedResult] = useState(null);
  const [isDeploying, setIsDeploying] = useState(false);
  const [copiedLink, setCopiedLink] = useState(false);

  // Settings state (.env configuration)
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [settings, setSettings] = useState({
    GOOGLE_API_KEY: '',
    NETLIFY_AUTH_TOKEN: '',
    MISTRAL_API_KEY: '',
    VERCEL_TOKEN: ''
  });
  const [savingSettings, setSavingSettings] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Fetch settings on load
  useEffect(() => {
    fetch('http://localhost:8000/api/settings')
      .then(res => res.json())
      .then(data => setSettings(data))
      .catch(err => console.error("Error fetching settings:", err));
  }, []);

  // Poll the backend status
  useEffect(() => {
    if (status === 'idle' || status === 'completed' || status === 'denied') return;
    
    const interval = setInterval(async () => {
      try {
        const res = await fetch('http://localhost:8000/api/status');
        const data = await res.json();
        setIsPaused(data.is_paused);
        setStateData(data.state);
        
        if (data.status === 'completed' || data.status === 'denied') {
          setStatus(data.status);
          setIsRefining(false);
          setPreviewKey(Date.now());
          clearInterval(interval);
        } else {
          setStatus(data.status);
        }
      } catch (e) {
        console.error("Error polling status:", e);
      }
    }, 1500);
    
    return () => clearInterval(interval);
  }, [status]);

  const startGeneration = async (e) => {
    e.preventDefault();
    setStateData(null);
    setDeployedResult(null);
    setStatus('starting');
    
    try {
      await fetch('http://localhost:8000/api/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          business_description: businessDesc,
          tone: tone,
          brand_colors: colors ? colors.split(',').map(c => c.trim()) : []
        })
      });
      setStatus('running');
    } catch (err) {
      console.error("Error starting generation:", err);
      setStatus('idle');
    }
  };

  const handleApproval = async (approved) => {
    await fetch('http://localhost:8000/api/approve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ approved })
    });
    setIsPaused(false);
  };

  const handleSendFeedback = async (e) => {
    e.preventDefault();
    if (!feedback.trim()) return;
    
    setIsRefining(true);
    const feedbackText = feedback;
    setFeedback('');
    setStatus('running');
    
    try {
      await fetch('http://localhost:8000/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ feedback: feedbackText })
      });
    } catch (err) {
      console.error("Error sending feedback:", err);
      setIsRefining(false);
      setStatus('completed');
    }
  };

  // Open deployment preparation
  const handleOpenDeploy = async (service = 'netlify') => {
    setDeployService(service);
    try {
      const res = await fetch('http://localhost:8000/api/deploy/prepare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ service })
      });
      const data = await res.json();
      setDeployPlan(data);
      setDeployModalOpen(true);
    } catch (e) {
      console.error("Error preparing deploy:", e);
    }
  };

  // Execute deployment after approval
  const handleConfirmDeploy = async (approved) => {
    if (!approved) {
      setDeployModalOpen(false);
      return;
    }
    
    setIsDeploying(true);
    try {
      const res = await fetch('http://localhost:8000/api/deploy/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ service: deployService, approved: true })
      });
      const data = await res.json();
      setDeployedResult(data);
      setDeployModalOpen(false);
    } catch (e) {
      console.error("Deployment error:", e);
    } finally {
      setIsDeploying(false);
    }
  };

  const copyToClipboard = (url) => {
    navigator.clipboard.writeText(url);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  const handleSaveSettings = async (e) => {
    e.preventDefault();
    setSavingSettings(true);
    try {
      await fetch('http://localhost:8000/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2500);
    } catch (err) {
      console.error("Error saving settings:", err);
    } finally {
      setSavingSettings(false);
    }
  };

  const stages = [
    { id: 'planning', label: '1. Architecture' },
    { id: 'generating_assets', label: '2. Assets & Icons' },
    { id: 'coding_frontend', label: '3. React & Design' },
    { id: 'coding_backend', label: '4. Express API' },
    { id: 'reviewing', label: '5. AI QA Review' },
    { id: 'awaiting_approval', label: '6. Execution Approval' },
    { id: 'completed', label: '7. Saved & Live' }
  ];

  const getCurrentStepIndex = () => {
    const stage = stateData?.current_stage;
    if (stage === 'completed') return 6;
    if (stage === 'awaiting_approval' || isPaused) return 5;
    if (stage === 'reviewing') return 4;
    if (stage === 'coding_backend') return 3;
    if (stage === 'coding_frontend') return 2;
    if (stage === 'generating_assets') return 1;
    return 0;
  };

  const isCompleted = status === 'completed' || stateData?.current_stage === 'completed';

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 font-sans p-4 sm:p-8 selection:bg-blue-600 selection:text-white">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Top Header */}
        <header className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div className="flex items-center space-x-3">
            <div className="w-11 h-11 bg-gradient-to-tr from-blue-600 to-emerald-500 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20 font-black text-xl text-white">
              ⚡
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">AI Website Builder Agent</h1>
              <p className="text-xs sm:text-sm text-slate-400">Autonomous design, coding, Git checkpointing & cloud deployment engine</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Settings Button */}
            <button 
              onClick={() => setSettingsOpen(true)}
              className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs sm:text-sm font-semibold rounded-lg border border-slate-700 transition flex items-center gap-1.5"
            >
              <span>⚙️ Settings (.env)</span>
            </button>

            {isCompleted && (
              <button 
                onClick={() => handleOpenDeploy('netlify')}
                className="px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white text-xs sm:text-sm font-bold rounded-lg shadow-lg shadow-emerald-600/20 transition flex items-center gap-1.5"
              >
                <span>🚀 Put Page Online</span>
              </button>
            )}

            {status !== 'idle' && (
              <button 
                onClick={() => { setStatus('idle'); setStateData(null); setDeployedResult(null); }}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs sm:text-sm font-semibold rounded-lg border border-slate-700 transition"
              >
                + Create New Website
              </button>
            )}
          </div>
        </header>

        {/* Live Public URL Banner (if deployed) */}
        {deployedResult && (
          <div className="bg-gradient-to-r from-emerald-950/80 to-slate-900 border-2 border-emerald-500/50 rounded-2xl p-6 shadow-2xl space-y-4 animate-in fade-in zoom-in duration-300">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-xl font-bold">
                  🌐
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">Your Website is Live Online!</h3>
                  <p className="text-xs text-emerald-300/90">Published via {deployedResult.service_name} with public shareable link</p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <a 
                  href={deployedResult.deployed_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs sm:text-sm rounded-lg shadow-lg transition flex items-center gap-1.5"
                >
                  <span>🔗 Open Live Site</span>
                </a>
                <button 
                  onClick={() => copyToClipboard(deployedResult.deployed_url)}
                  className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs sm:text-sm font-semibold rounded-lg border border-slate-700 transition"
                >
                  {copiedLink ? '✓ Copied!' : '📋 Copy Link'}
                </button>
              </div>
            </div>
            
            <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800 text-xs font-mono text-emerald-400 break-all">
              {deployedResult.deployed_url}
            </div>
          </div>
        )}

        {/* 1. Intake Form */}
        {status === 'idle' && (
          <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-6 sm:p-10 shadow-2xl backdrop-blur-sm max-w-2xl mx-auto">
            <h2 className="text-xl font-bold text-white mb-2">Build Your Next Website</h2>
            <p className="text-sm text-slate-400 mb-6">Describe your business, choose your tone, and our team of AI agents will architect, design, code, and test your landing page.</p>

            <form onSubmit={startGeneration} className="space-y-5">
              <div>
                <label className="block text-sm font-semibold text-slate-200 mb-1.5">What is your business?</label>
                <textarea 
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3.5 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition text-sm leading-relaxed"
                  rows="4"
                  value={businessDesc}
                  onChange={(e) => setBusinessDesc(e.target.value)}
                  placeholder="e.g. A luxury artisanal coffee roastery with ethically sourced beans in downtown Seattle..."
                  required
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-slate-200 mb-1.5">Brand Tone</label>
                  <select 
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-white focus:outline-none focus:border-blue-500 text-sm"
                    value={tone}
                    onChange={(e) => setTone(e.target.value)}
                  >
                    <option>Professional & Trustworthy</option>
                    <option>Warm, Cozy & Artisanal</option>
                    <option>Bold, High-Energy & Vibrant</option>
                    <option>Clean, Minimalist & Modern</option>
                    <option>Playful, Friendly & Creative</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-slate-200 mb-1.5">Brand Colors (Optional)</label>
                  <input 
                    type="text"
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 text-sm"
                    value={colors}
                    onChange={(e) => setColors(e.target.value)}
                    placeholder="e.g. #3B82F6, #10B981"
                  />
                </div>
              </div>

              <button 
                type="submit" 
                className="w-full bg-gradient-to-r from-blue-600 to-emerald-500 hover:from-blue-500 hover:to-emerald-400 text-white font-bold py-4 rounded-xl shadow-xl shadow-blue-500/25 transition-all text-base tracking-wide cursor-pointer hover:scale-[1.01]"
              >
                🚀 Generate Complete Website
              </button>
            </form>
          </div>
        )}

        {/* 2. Generation Progress Pipeline */}
        {status !== 'idle' && (
          <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-6 shadow-xl space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-700/60 pb-4">
              <div>
                <span className="text-xs uppercase font-bold tracking-widest text-emerald-400">Agent Pipeline</span>
                <h3 className="text-lg font-bold text-white">Current Stage: <span className="text-blue-400 capitalize">{stateData?.current_stage?.replace(/_/g, ' ') || 'Initializing...'}</span></h3>
              </div>
              <div className="flex items-center gap-2">
                <span className="relative flex h-3 w-3">
                  <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${isCompleted ? 'bg-emerald-400' : 'bg-blue-400'} opacity-75`}></span>
                  <span className={`relative inline-flex rounded-full h-3 w-3 ${isCompleted ? 'bg-emerald-500' : 'bg-blue-500'}`}></span>
                </span>
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">{(status || 'RUNNING').toUpperCase()}</span>
              </div>
            </div>

            {/* Stage Steps Bar */}
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
              {stages.map((st, idx) => {
                const currentIdx = getCurrentStepIndex();
                const isPassed = idx < currentIdx;
                const isCurrent = idx === currentIdx;
                
                return (
                  <div 
                    key={st.id}
                    className={`p-2.5 rounded-xl border text-xs font-medium transition flex flex-col justify-between ${
                      isPassed 
                        ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300' 
                        : isCurrent 
                          ? 'bg-blue-900/40 border-blue-500 text-blue-200 ring-2 ring-blue-500/20' 
                          : 'bg-slate-900/40 border-slate-800 text-slate-500'
                    }`}
                  >
                    <span>{st.label}</span>
                    <span className="mt-1 text-[10px] uppercase font-bold tracking-wider">
                      {isPassed ? '✓ Done' : isCurrent ? '● Active' : 'Waiting'}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* 3. Live Interactive Preview & Natural Language Feedback Loop */}
        {status !== 'idle' && (
          <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-6 shadow-2xl space-y-6">
            
            {/* Preview Toolbar */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <span>🖥️ Live Website Preview</span>
                  {isCompleted && (
                    <span className="bg-emerald-500/20 text-emerald-400 text-xs px-2.5 py-0.5 rounded-full font-semibold border border-emerald-500/30">
                      Git Checkpointed
                    </span>
                  )}
                </h2>
                <p className="text-xs text-slate-400">Interactive live render compiled directly from generated React & Tailwind code.</p>
              </div>

              <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end">
                {/* Device switch */}
                <div className="flex bg-slate-900 rounded-lg p-1 border border-slate-700 text-xs">
                  <button 
                    onClick={() => setDeviceView('desktop')}
                    className={`px-3 py-1 rounded font-medium transition ${deviceView === 'desktop' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
                  >
                    💻 Desktop
                  </button>
                  <button 
                    onClick={() => setDeviceView('mobile')}
                    className={`px-3 py-1 rounded font-medium transition ${deviceView === 'mobile' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
                  >
                    📱 Mobile
                  </button>
                </div>

                {/* Deploy Button */}
                {isCompleted && (
                  <button 
                    onClick={() => handleOpenDeploy('netlify')}
                    className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg flex items-center gap-1.5 transition shadow"
                  >
                    <span>🚀 Deploy Online</span>
                  </button>
                )}

                {/* Open In New Tab */}
                <a 
                  href="http://localhost:8000/api/preview" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="px-3.5 py-1.5 bg-slate-700 hover:bg-slate-600 text-white text-xs font-semibold rounded-lg flex items-center gap-1.5 border border-slate-600 transition"
                >
                  <span>↗ Fullscreen Tab</span>
                </a>
              </div>
            </div>

            {/* Responsive iFrame Frame or Generating State */}
            <div className={`mx-auto bg-slate-950 rounded-2xl border-2 border-slate-700 overflow-hidden shadow-2xl transition-all duration-300 ${
              deviceView === 'mobile' ? 'max-w-sm h-[650px]' : 'w-full h-[700px]'
            }`}>
              {(status === 'starting' || (status === 'running' && !stateData?.frontend_code)) ? (
                <div className="w-full h-full flex flex-col items-center justify-center p-8 text-center space-y-5 bg-gradient-to-b from-slate-900 to-slate-950">
                  <div className="w-16 h-16 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-3xl animate-bounce">
                    ⚡
                  </div>
                  <div className="space-y-2 max-w-md">
                    <h3 className="text-xl font-bold text-white">Crafting Your New Website</h3>
                    <p className="text-xs text-slate-400 leading-relaxed">
                      The AI Architect, Designer, and QA agents are generating custom layouts, color schemes, and React components based on your prompt...
                    </p>
                  </div>
                  <div className="w-56 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <div className="w-full h-full bg-gradient-to-r from-blue-500 via-emerald-400 to-blue-500 animate-pulse"></div>
                  </div>
                  <div className="text-xs font-mono text-slate-400">
                    Active Agent: <span className="text-blue-400 font-bold capitalize">{stateData?.current_stage?.replace(/_/g, ' ') || 'Planning Architecture'}</span>
                  </div>
                </div>
              ) : (
                <iframe 
                  key={previewKey}
                  src="http://localhost:8000/api/preview" 
                  title="Website Live Preview"
                  className="w-full h-full border-0 bg-slate-900"
                />
              )}
            </div>

            {/* 4. Natural Language Feedback & Refinement Loop */}
            <div className="bg-slate-900 border border-slate-700/80 rounded-xl p-5 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-lg">💬</span>
                  <h4 className="text-sm font-bold text-white">Describe Changes to Refine Design</h4>
                </div>
                <span className="text-[11px] text-slate-400">Orchestrator will direct the Design Agent to update the code</span>
              </div>

              <form onSubmit={handleSendFeedback} className="flex gap-2">
                <input 
                  type="text"
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                  placeholder="e.g., 'Make the headline bolder, use warm golden colors, and add an espresso specialty card'..."
                  disabled={isRefining || status === 'running'}
                  className="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 disabled:opacity-50"
                />
                <button 
                  type="submit"
                  disabled={isRefining || status === 'running' || !feedback.trim()}
                  className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 text-white text-sm font-bold px-5 py-2.5 rounded-xl shadow-lg transition disabled:cursor-not-allowed"
                >
                  {isRefining ? 'Applying Changes...' : 'Apply Changes'}
                </button>
              </form>
            </div>
          </div>
        )}

        {/* 5. Safe Execution Approval Modal (Local Code Saving) */}
        {isPaused && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
            <div className="bg-slate-800 border-2 border-red-500/50 rounded-2xl shadow-2xl p-6 sm:p-8 max-w-xl w-full space-y-5 animate-in fade-in zoom-in duration-200">
              
              <div className="flex items-center space-x-3 text-red-400">
                <div className="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center text-red-400 font-black text-xl">
                  ⚠️
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white">Execution Approval Required</h3>
                  <p className="text-xs text-slate-400">The execution agent requests permission to run commands on your machine</p>
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-700 p-4 rounded-xl space-y-2 text-xs font-mono text-slate-300 overflow-x-auto">
                <div className="text-[11px] uppercase font-bold text-slate-500 tracking-wider font-sans mb-1">Commands to run:</div>
                {stateData?.pending_commands?.map((cmd, i) => (
                  <div key={i} className="text-emerald-400 flex items-start gap-2">
                    <span className="text-slate-600 select-none">&gt;</span>
                    <span className="break-all">{cmd}</span>
                  </div>
                ))}
              </div>

              <div className="bg-amber-950/30 border border-amber-500/30 p-3.5 rounded-xl text-xs text-amber-200/90 leading-relaxed">
                <strong>🛡️ Safety Check:</strong> These commands will write generated React and backend files to the <code className="bg-slate-900 px-1 py-0.5 rounded text-amber-300">generated-sites/</code> directory and initialize a Git repository to save your version checkpoint.
              </div>

              <div className="flex gap-3 pt-2">
                <button 
                  onClick={() => handleApproval(false)} 
                  className="flex-1 bg-slate-700 hover:bg-slate-600 text-slate-200 p-3 rounded-xl font-bold text-sm transition"
                >
                  Deny Execution
                </button>
                <button 
                  onClick={() => handleApproval(true)} 
                  className="flex-1 bg-red-600 hover:bg-red-500 text-white p-3 rounded-xl font-bold text-sm shadow-lg shadow-red-600/30 transition"
                >
                  Approve & Execute Commands
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 6. Cloud Deployment Approval Modal */}
        {deployModalOpen && deployPlan && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
            <div className="bg-slate-800 border-2 border-emerald-500/50 rounded-2xl shadow-2xl p-6 sm:p-8 max-w-xl w-full space-y-5 animate-in fade-in zoom-in duration-200">
              
              <div className="flex items-center space-x-3 text-emerald-400">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-400 font-black text-xl">
                  🚀
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white">Deploy Website Online</h3>
                  <p className="text-xs text-slate-400">The execution agent will publish your site to free cloud hosting</p>
                </div>
              </div>

              {/* Service Selection */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-2">Select Free Cloud Hosting Service:</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: 'netlify', name: '💠 Netlify API (1-Click)' },
                    { id: 'netlify_drop', name: '📦 Netlify Drop' },
                    { id: 'vercel', name: '▲ Vercel' }
                  ].map((srv) => (
                    <button
                      key={srv.id}
                      onClick={() => handleOpenDeploy(srv.id)}
                      className={`p-2.5 rounded-xl border text-xs font-bold transition ${
                        deployService === srv.id
                          ? 'bg-emerald-600 border-emerald-500 text-white'
                          : 'bg-slate-900 border-slate-700 text-slate-400 hover:text-white'
                      }`}
                    >
                      {srv.name}
                    </button>
                  ))}
                </div>
              </div>

              {/* Exact Terminal Command */}
              <div className="bg-slate-900 border border-slate-700 p-4 rounded-xl space-y-2 text-xs font-mono text-slate-300 overflow-x-auto">
                <div className="text-[11px] uppercase font-bold text-slate-500 tracking-wider font-sans mb-1">Execution Action:</div>
                <div className="text-emerald-400 flex items-start gap-2">
                  <span className="text-slate-600 select-none">&gt;</span>
                  <span className="break-all">{deployPlan.command}</span>
                </div>
              </div>

              <div className="bg-emerald-950/30 border border-emerald-500/30 p-3.5 rounded-xl text-xs text-emerald-200/90 leading-relaxed">
                <strong>🛡️ Safety Notice:</strong> {deployPlan.safety_note}
              </div>

              <div className="flex gap-3 pt-2">
                <button 
                  onClick={() => handleConfirmDeploy(false)} 
                  disabled={isDeploying}
                  className="flex-1 bg-slate-700 hover:bg-slate-600 text-slate-200 p-3 rounded-xl font-bold text-sm transition"
                >
                  Cancel
                </button>
                <button 
                  onClick={() => handleConfirmDeploy(true)} 
                  disabled={isDeploying}
                  className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white p-3 rounded-xl font-bold text-sm shadow-lg shadow-emerald-600/30 transition disabled:opacity-50"
                >
                  {isDeploying ? 'Publishing to Cloud...' : 'Approve & Put Online'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 7. Settings Modal (.env Configuration) */}
        {settingsOpen && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
            <div className="bg-slate-800 border-2 border-blue-500/50 rounded-2xl shadow-2xl p-6 sm:p-8 max-w-xl w-full space-y-5 animate-in fade-in zoom-in duration-200">
              
              <div className="flex items-center justify-between border-b border-slate-700 pb-4">
                <div className="flex items-center space-x-3 text-blue-400">
                  <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-400 font-black text-xl">
                    ⚙️
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white">Environment Settings (.env)</h3>
                    <p className="text-xs text-slate-400">Configure your API keys and tokens for AI agents and cloud deployment</p>
                  </div>
                </div>
                <button 
                  onClick={() => setSettingsOpen(false)}
                  className="text-slate-400 hover:text-white text-lg font-bold p-1"
                >
                  ✕
                </button>
              </div>

              {saveSuccess && (
                <div className="bg-emerald-950/40 border border-emerald-500/50 text-emerald-300 text-xs p-3 rounded-xl flex items-center gap-2">
                  <span>✓ Settings saved successfully to .env!</span>
                </div>
              )}

              <form onSubmit={handleSaveSettings} className="space-y-4 text-xs sm:text-sm">
                <div>
                  <label className="block font-semibold text-slate-300 mb-1">Google Gemini API Key (GOOGLE_API_KEY)</label>
                  <input 
                    type="password"
                    value={settings.GOOGLE_API_KEY || ''}
                    onChange={(e) => setSettings({...settings, GOOGLE_API_KEY: e.target.value})}
                    placeholder="AQ.Ab8..."
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-white focus:outline-none focus:border-blue-500 font-mono text-xs"
                  />
                  <p className="text-[10px] text-slate-500 mt-1">Powers the Architect, Designer, and Reviewer agents.</p>
                </div>

                <div>
                  <label className="block font-semibold text-slate-300 mb-1">Netlify Personal Access Token (NETLIFY_AUTH_TOKEN)</label>
                  <input 
                    type="password"
                    value={settings.NETLIFY_AUTH_TOKEN || ''}
                    onChange={(e) => setSettings({...settings, NETLIFY_AUTH_TOKEN: e.target.value})}
                    placeholder="nfp_..."
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-white focus:outline-none focus:border-blue-500 font-mono text-xs"
                  />
                  <p className="text-[10px] text-slate-500 mt-1">Powers 1-click autonomous cloud deployment directly to .netlify.app.</p>
                </div>

                <div>
                  <label className="block font-semibold text-slate-300 mb-1">Mistral API Key (MISTRAL_API_KEY)</label>
                  <input 
                    type="password"
                    value={settings.MISTRAL_API_KEY || ''}
                    onChange={(e) => setSettings({...settings, MISTRAL_API_KEY: e.target.value})}
                    placeholder="Optional Mistral key..."
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-white focus:outline-none focus:border-blue-500 font-mono text-xs"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-300 mb-1">Vercel API Token (VERCEL_TOKEN)</label>
                  <input 
                    type="password"
                    value={settings.VERCEL_TOKEN || ''}
                    onChange={(e) => setSettings({...settings, VERCEL_TOKEN: e.target.value})}
                    placeholder="Optional Vercel token..."
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-white focus:outline-none focus:border-blue-500 font-mono text-xs"
                  />
                </div>

                <div className="flex gap-3 pt-3">
                  <button 
                    type="button"
                    onClick={() => setSettingsOpen(false)}
                    className="flex-1 bg-slate-700 hover:bg-slate-600 text-slate-200 p-3 rounded-xl font-bold text-xs sm:text-sm transition"
                  >
                    Close
                  </button>
                  <button 
                    type="submit"
                    disabled={savingSettings}
                    className="flex-1 bg-blue-600 hover:bg-blue-500 text-white p-3 rounded-xl font-bold text-xs sm:text-sm shadow-lg shadow-blue-600/30 transition disabled:opacity-50"
                  >
                    {savingSettings ? 'Saving...' : '💾 Save Settings'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

export default App;
