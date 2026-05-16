import { useRef, useState } from 'react'
import { streamPromptAnalysis } from '../api/client'
import { useAppStore } from '../store/appStore'

type ExampleLang = 'en' | 'ru' | 'kk'

interface Example {
  title: string
  prompt: string
}

const EXAMPLES: Record<ExampleLang, Example[]> = {
  en: [
    {
      title: 'Mixed-use high-rise — Almaty',
      prompt:
        'We are designing a 22-storey mixed-use tower in Almaty with retail on floors 1–3, offices on floors 4–15, and residential apartments on floors 16–22. The structural system is reinforced concrete with a curtain-wall façade. Please assess compliance with fire safety, seismic, accessibility, and MEP requirements.',
    },
    {
      title: 'Industrial warehouse — Karaganda',
      prompt:
        'A single-storey prefabricated steel warehouse of 8 500 m² net area is planned in the Karaganda industrial zone. The facility will store non-hazardous dry goods. Provide a compliance review covering fire safety compartmentation, natural ventilation requirements, and site drainage standards.',
    },
    {
      title: 'Public school extension — Astana',
      prompt:
        'An existing 3-storey public school in Astana requires a new 2-storey classroom wing of approximately 1 200 m². Structural material is brick masonry. Identify all applicable СП РК and СН РК requirements for educational facilities, including accessibility, fire evacuation routes, and HVAC.',
    },
  ],
  ru: [
    {
      title: 'Жилой дом — Алматы',
      prompt:
        'Планируется строительство 9-этажного жилого дома в Алматы из монолитного железобетона общей площадью 12 000 м². Здание расположено в сейсмической зоне 8 баллов. Проведите анализ соответствия нормативным требованиям по сейсмостойкости, пожарной безопасности, доступности для маломобильных групп и инженерным системам.',
    },
    {
      title: 'Торговый центр — Астана',
      prompt:
        'Проектируется трёхэтажный торгово-развлекательный центр площадью 35 000 м² в Астане. Конструктивная схема — стальной каркас с навесным фасадом. Требуется оценка соответствия СП РК по пожарной безопасности, эвакуационным выходам, вентиляции и электрооборудованию.',
    },
    {
      title: 'Офисное здание — Шымкент',
      prompt:
        'Пятиэтажное офисное здание класса B+ из сборного железобетона, общая площадь 6 500 м², г. Шымкент. Здание предназначено для размещения 400 рабочих мест. Проверьте соответствие нормам по водоснабжению, канализации, отоплению и вентиляции, а также требованиям доступности.',
    },
    {
      title: 'Индивидуальный жилой дом — Актобе',
      prompt:
        'Проектирование двухэтажного индивидуального жилого дома из кирпича площадью 280 м² в г. Актобе. Участок находится в зоне умеренной сейсмичности. Необходим анализ требований СН РК по планировке территории, СП РК по пожарной безопасности и инженерным коммуникациям.',
    },
  ],
  kk: [
    {
      title: 'Тұрғын үй кешені — Алматы',
      prompt:
        'Алматы қаласында 14 қабатты тұрғын үй кешені жоспарлануда, жалпы ауданы 18 000 м², монолитті темірбетон конструкциясы. Ғимарат 8 балдық сейсмикалық аймақта орналасқан. Өрт қауіпсіздігі, сейсмикалық тұрақтылық, қолжетімділік және инженерлік жүйелер бойынша СП РК және СН РК нормаларының сақталуын тексеріңіз.',
    },
    {
      title: 'Әкімшілік ғимарат — Астана',
      prompt:
        'Астана қаласында болат каркасты 6 қабатты әкімшілік ғимарат салу жоспарлануда, жалпы ауданы 9 000 м². Ғимаратта 600 жұмысшы орналасады. Су жабдықтау, кәріз, жылыту, желдету және электр жабдықтары бойынша СП РК нормаларының талаптарын, сондай-ақ мүмкіндігі шектеулі адамдарға арналған қолжетімділік талаптарын бағалаңыз.',
    },
  ],
}

const LANG_LABELS: Record<ExampleLang, string> = {
  en: 'English',
  ru: 'Русский',
  kk: 'Қазақша',
}

export default function PromptInput() {
  const [prompt, setPrompt] = useState('')
  const [showExamples, setShowExamples] = useState(false)
  const [activeLang, setActiveLang] = useState<ExampleLang>('en')
  const { setResult, setIsAnalyzing, setError, resetProgress, addAgentStep } = useAppStore()

  const abortRef = useRef<AbortController | null>(null)
  const [isPending, setIsPending] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (prompt.trim().length < 10) return

    abortRef.current?.abort()
    resetProgress()
    setIsAnalyzing(true)
    setError(null)
    setIsPending(true)

    streamPromptAnalysis(
      { prompt: prompt.trim() },
      {
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
      }
    )
  }

  const selectExample = (ex: Example) => {
    setPrompt(ex.prompt)
    setShowExamples(false)
  }

  const charCount = prompt.length
  const isValid = charCount >= 10

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-slate-800">Describe Your Project</h2>
        <button
          type="button"
          onClick={() => setShowExamples(!showExamples)}
          className="inline-flex items-center gap-1.5 text-xs font-medium text-blue-700 hover:text-blue-900 bg-blue-50 hover:bg-blue-100 border border-blue-200 hover:border-blue-300 px-3 py-1.5 rounded-lg transition-colors"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          {showExamples ? 'Hide examples' : 'Show examples'}
        </button>
      </div>

      {showExamples && (
        <div className="mb-5 border border-slate-200 rounded-xl overflow-hidden">
          {/* Language tabs */}
          <div className="flex border-b border-slate-200 bg-slate-50">
            {(Object.keys(LANG_LABELS) as ExampleLang[]).map((lang) => (
              <button
                key={lang}
                type="button"
                onClick={() => setActiveLang(lang)}
                className={`flex-1 text-xs font-semibold py-2.5 transition-colors ${
                  activeLang === lang
                    ? 'bg-white text-blue-700 border-b-2 border-blue-600'
                    : 'text-slate-500 hover:text-slate-700 hover:bg-slate-100'
                }`}
              >
                {LANG_LABELS[lang]}
              </button>
            ))}
          </div>

          {/* Example cards */}
          <div className="divide-y divide-slate-100">
            {EXAMPLES[activeLang].map((ex, i) => (
              <button
                key={i}
                type="button"
                onClick={() => selectExample(ex)}
                className="w-full text-left px-4 py-3.5 hover:bg-blue-50 transition-colors group"
              >
                <p className="text-xs font-semibold text-slate-700 group-hover:text-blue-700 mb-1">
                  {ex.title}
                </p>
                <p className="text-xs text-slate-500 leading-relaxed line-clamp-2">
                  {ex.prompt}
                </p>
                <span className="inline-block mt-1.5 text-[10px] font-medium text-blue-600 group-hover:text-blue-800">
                  Use this prompt →
                </span>
              </button>
            ))}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="relative">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={9}
            placeholder={
              'Describe your construction project in plain language.\n\n' +
              'Include: building type, number of floors, city, primary material, ' +
              'intended use, site conditions, special requirements...\n\n' +
              'Supports Russian (Русский), Kazakh (Қазақша), and English.'
            }
            className="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm text-slate-800 placeholder-slate-400 resize-y focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent leading-relaxed"
          />
          <span className={`absolute bottom-2 right-3 text-xs ${charCount > 3800 ? 'text-red-500' : 'text-slate-400'}`}>
            {charCount}/4000
          </span>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={!isValid || isPending}
            className="flex-1 rounded-xl bg-blue-700 hover:bg-blue-800 disabled:bg-slate-300 text-white text-sm font-semibold py-2.5 px-4 transition-colors flex items-center justify-center gap-2"
          >
            {isPending ? (
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
          {prompt && !isPending && (
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
