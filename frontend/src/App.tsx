import { useState } from 'react'
import AnalysisForm from './components/AnalysisForm'
import AgentStatusPanel from './components/AgentStatusPanel'
import ComplianceReport from './components/ComplianceReport'
import FeedbackWidget from './components/FeedbackWidget'
import PromptInput from './components/PromptInput'
import SearchPanel from './components/SearchPanel'
import { useAppStore } from './store/appStore'

type InputMode = 'prompt' | 'form'

export default function App() {
  const { result, error } = useAppStore()
  const [mode, setMode] = useState<InputMode>('prompt')

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-blue-800 text-white py-4 px-6 shadow-md">
        <div className="max-w-7xl mx-auto flex items-center gap-3">
          <span className="text-2xl">🏗️</span>
          <div>
            <h1 className="text-xl font-bold tracking-tight">DEREK-AI</h1>
            <p className="text-xs text-blue-200">
              AI Regulatory Intelligence · Kazakhstan Construction Norms
            </p>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 space-y-6">
        {/* Mode tabs */}
        <div className="flex gap-1 bg-white rounded-xl border border-slate-200 p-1 w-fit shadow-sm">
          <button
            onClick={() => setMode('prompt')}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              mode === 'prompt'
                ? 'bg-blue-700 text-white shadow-sm'
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            💬 Natural Language
          </button>
          <button
            onClick={() => setMode('form')}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              mode === 'form'
                ? 'bg-blue-700 text-white shadow-sm'
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            📝 Structured Form
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Left column: input + search */}
          <div className="lg:col-span-2 space-y-5">
            {mode === 'prompt' ? (
              <PromptInput />
            ) : (
              <AnalysisForm />
            )}
            <AgentStatusPanel />
            <SearchPanel />
          </div>

          {/* Right column: results */}
          <div className="lg:col-span-3 space-y-5">
            {error && (
              <div className="rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-800">
                ⚠️ {error}
              </div>
            )}

            {result && (
              <>
                <ComplianceReport report={result} />
                <FeedbackWidget />
              </>
            )}

            {!result && !error && (
              <div className="rounded-2xl bg-white border border-slate-200 shadow-sm p-10 text-center text-slate-400">
                <div className="text-4xl mb-3">📋</div>
                {mode === 'prompt' ? (
                  <p className="text-sm">
                    Describe your project in the text box and click{' '}
                    <span className="font-semibold text-slate-600">Check Compliance</span>.
                    <br />
                    <span className="text-xs mt-1 block">
                      Supports Russian, Kazakh, and English.
                    </span>
                  </p>
                ) : (
                  <p className="text-sm">
                    Fill in the building parameters and click{' '}
                    <span className="font-semibold text-slate-600">Run Compliance Analysis</span>
                    .
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
