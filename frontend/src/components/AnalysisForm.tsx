import { useRef, useState } from 'react'
import { streamAnalysis } from '../api/client'
import { useAppStore } from '../store/appStore'
import type { AnalyzeRequest } from '../types'

const BUILDING_TYPES = ['Residential', 'Commercial', 'Industrial', 'School', 'Hospital', 'Warehouse', 'Mixed-use']
const MATERIALS = ['Reinforced concrete', 'Steel', 'Brick', 'Wood', 'Panel', 'Monolithic']
const CITIES = ['Almaty', 'Astana', 'Shymkent', 'Karaganda', 'Aktobe', 'Pavlodar', 'Other']

export default function AnalysisForm() {
  const [form, setForm] = useState<AnalyzeRequest>({
    building_type: '',
    floors: 5,
    city: '',
    material: 'Reinforced concrete',
    purpose: '',
    notes: '',
  })

  const { setResult, setIsAnalyzing, setError, resetProgress, addAgentStep } = useAppStore()
  const [isPending, setIsPending] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  const isValid = form.building_type && form.city && form.floors > 0

  const handleRun = () => {
    if (!isValid) return
    abortRef.current?.abort()
    resetProgress()
    setIsAnalyzing(true)
    setError(null)
    setIsPending(true)

    streamAnalysis(form, {
      onAgentStep: (step) => addAgentStep(step),
      onComplete: (data) => {
        setResult(data)
        setIsAnalyzing(false)
        setIsPending(false)
      },
      onError: (msg) => {
        setError(msg || 'Analysis failed. Please try again.')
        setIsAnalyzing(false)
        setIsPending(false)
      },
    })
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
      <h2 className="text-lg font-semibold text-slate-800 mb-4">Building Parameters</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Building Type */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Building Type *</label>
          <select
            value={form.building_type}
            onChange={(e) => setForm({ ...form, building_type: e.target.value })}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select type...</option>
            {BUILDING_TYPES.map((t) => <option key={t}>{t}</option>)}
          </select>
        </div>

        {/* Floors */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Number of Floors *</label>
          <input
            type="number"
            min={1}
            max={200}
            value={form.floors}
            onChange={(e) => setForm({ ...form, floors: parseInt(e.target.value) || 1 })}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* City */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">City *</label>
          <select
            value={form.city}
            onChange={(e) => setForm({ ...form, city: e.target.value })}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select city...</option>
            {CITIES.map((c) => <option key={c}>{c}</option>)}
          </select>
        </div>

        {/* Material */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Primary Material</label>
          <select
            value={form.material}
            onChange={(e) => setForm({ ...form, material: e.target.value })}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {MATERIALS.map((m) => <option key={m}>{m}</option>)}
          </select>
        </div>

        {/* Purpose */}
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-slate-700 mb-1">Purpose / Use</label>
          <input
            type="text"
            placeholder="e.g., Apartments, Office space, Retail"
            value={form.purpose}
            onChange={(e) => setForm({ ...form, purpose: e.target.value })}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Notes */}
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-slate-700 mb-1">Additional Notes</label>
          <textarea
            rows={2}
            placeholder="Special requirements, concerns, or questions..."
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
        </div>
      </div>

      <button
        disabled={!isValid || isPending}
        onClick={handleRun}
        className="mt-5 w-full bg-blue-700 hover:bg-blue-800 disabled:opacity-40 text-white font-semibold py-2.5 rounded-xl transition-colors text-sm"
      >
        {isPending ? 'Analyzing…' : 'Run Compliance Analysis'}
      </button>
    </div>
  )
}
