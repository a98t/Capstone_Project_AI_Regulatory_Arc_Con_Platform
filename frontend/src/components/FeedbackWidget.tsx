import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { submitFeedback } from '../api/client'
import { useAppStore } from '../store/appStore'

export default function FeedbackWidget() {
  const { result } = useAppStore()
  const [rating, setRating] = useState(0)
  const [comment, setComment] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const mutation = useMutation({
    mutationFn: () =>
      submitFeedback(result!.session_id, rating, comment),
    onSuccess: () => setSubmitted(true),
  })

  if (!result) return null
  if (submitted) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-xl px-4 py-3 text-sm text-green-800">
        ✓ Thank you for your feedback!
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5">
      <h3 className="text-sm font-semibold text-slate-600 mb-3">Rate this analysis</h3>

      <div className="flex gap-1 mb-3">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            onClick={() => setRating(star)}
            className={`text-2xl transition-transform hover:scale-110 ${
              star <= rating ? 'text-amber-400' : 'text-slate-200'
            }`}
          >
            ★
          </button>
        ))}
      </div>

      <textarea
        rows={2}
        placeholder="Optional comment..."
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none mb-3"
      />

      <button
        disabled={rating === 0 || mutation.isPending}
        onClick={() => mutation.mutate()}
        className="bg-blue-700 hover:bg-blue-800 disabled:opacity-40 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
      >
        Submit
      </button>
    </div>
  )
}
