import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { runPromptAnalysis } from '../api/client'
import { useAppStore } from '../store/appStore'

const EXAMPLE_PROMPTS = [
  'I want to design a 12-storey residential building in Almaty with a 2-level basement. Primary material is reinforced concrete. The public road is 10 metres from the site. MEP communications are underground and need relocation.',
  'Планирую построить торговый центр в Астане, 5 этажей, каркасная конструкция из стали, площадь участка 0.5 га, рядом жилой квартал.',
  'Small office building, 3 floors, brick construction, Shymkent city, parking for 50 cars on ground level, fire exit requirements.',
]

export default function PromptInput() {
  const [prompt, setPrompt] = useState('')
  const [showExamples, setShowExamples] = useState(false)
  const { setResult, setIsAnalyzing, setError, resetProgress, addAgentStep } = useAppStore()

  const mutation = useMutation({
    mutationFn: runPromptAnalysis,
    onMutate: () => {
      resetProgress()
      setIsAnalyzing(true)
      setError(null)
    },
    onSuccess: (data) => {
      data.agent_trace?.forEach((step) => addAgentStep(step))
      setResult(data)
      setIsAnalyzing(false)
    },
    onError: (err: any) => {
      setError(err?.response?.data?.detail || 'Analysis failed. Please try again.')
      setIsAnalyzing(false)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (prompt.trim().length < 10) return
    mutation.mutate({ prompt: prompt.trim() })
  }

  const charCount = prompt.length
  const isValid = charCount >= 10

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold text-slate-800">Describe Your Project</h2>
        <button
          type="button"
          onClick={() => setShowExamples(!showExamples)}
          className="text-xs text-blue-600 hover:text-blue-800 underline"
        >
          {showExamples ? 'Hide examples' : 'Show examples'}
        </button>
      </div>

      {showExamples && (
        <div className="mb-4 space-y-2">
          {EXAMPLE_PROMPTS.map((ex, i) => (
            <button
              key={i}
              type="button"
              onClick={() => { setPrompt(ex); setShowExamples(false) }}
              className="w-full text-left text-xs bg-slate-50 hover:bg-blue-50 border border-slate-200 hover:border-blue-300 rounded-lg px-3 py-2 text-slate-600 transition-colors"
            >
              {ex}
            </button>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="relative">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={6}
            placeholder={
              'Describe your construction project in plain language.\n\n' +
              'Include: building type, number of floors, city, primary material, ' +
              'intended use, site conditions, special requirements...\n\n' +
              'Supports Russian (Русский), Kazakh (Қазақша), and English.'
            }
            className="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm text-slate-800 placeholder-slate-400 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent leading-relaxed"
          />
          <span className={`absolute bottom-2 right-3 text-xs ${charCount > 3800 ? 'text-red-500' : 'text-slate-400'}`}>
            {charCount}/4000
          </span>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={!isValid || mutation.isPending}
            className="flex-1 rounded-xl bg-blue-700 hover:bg-blue-800 disabled:bg-slate-300 text-white text-sm font-semibold py-2.5 px-4 transition-colors flex items-center justify-center gap-2"
          >
            {mutation.isPending ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                </svg>
                Analysing…
              </>
            ) : (
              <>
                <span>🔍</span>
                Check Compliance
              </>
            )}
          </button>
          {prompt && (
            <button
              type="button"
              onClick={() => setPrompt('')}
              className="text-xs text-slate-500 hover:text-slate-700 px-3 py-2 rounded-lg border border-slate-200 hover:border-slate-300"
            >
              Clear
            </button>
          )}
        </div>
      </form>

      <p className="mt-3 text-xs text-slate-400 leading-relaxed">
        AI extracts your parameters, searches Kazakhstan's regulatory database (СП РК, СН РК),
        and returns a plain-language compliance report with document references.
      </p>
    </div>
  )
}
