import { useEffect, useState } from 'react'
import { Save } from 'lucide-react'
import client from '@/api/client'

interface SettingsData {
  openrouter_api_key_set: boolean
  openrouter_model: string
  analysis_score_threshold: number
  price_cache_ttl_minutes: number
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<SettingsData | null>(null)
  const [apiKey, setApiKey] = useState('')
  const [model, setModel] = useState('')
  const [threshold, setThreshold] = useState(40)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    client.get('/settings').then((r) => {
      const data: SettingsData = r.data
      setSettings(data)
      setThreshold(data.analysis_score_threshold)
      setModel(data.openrouter_model)
    })
  }, [])

  const handleSave = async () => {
    setSaving(true)
    try {
      const body: {
        openrouter_api_key?: string
        openrouter_model?: string
        analysis_score_threshold?: number
      } = { analysis_score_threshold: threshold }
      if (apiKey) body.openrouter_api_key = apiKey
      if (model) body.openrouter_model = model

      const r = await client.put('/settings', body)
      setSettings(r.data)
      setApiKey('')
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="p-6 max-w-lg mx-auto">
      <h1 className="text-xl font-bold text-white mb-6">Settings</h1>

      <div className="space-y-5">
        {/* OpenRouter API Key */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <label className="block text-sm font-medium text-gray-300 mb-1">OpenRouter API Key</label>
          <p className="text-xs text-gray-600 mb-3">
            Required for AI-powered analysis. Get yours at openrouter.ai/keys.
          </p>
          <div className="flex items-center gap-2 mb-2">
            <span className={`w-2 h-2 rounded-full ${settings?.openrouter_api_key_set ? 'bg-emerald-500' : 'bg-red-500'}`} />
            <span className="text-xs text-gray-500">
              {settings?.openrouter_api_key_set ? 'API key configured' : 'API key not set'}
            </span>
          </div>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="sk-or-..."
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white font-mono placeholder-gray-600 focus:outline-none focus:border-indigo-500"
          />
          <p className="text-xs text-gray-600 mt-1">Leave blank to keep existing key.</p>
        </div>

        {/* Model */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <label className="block text-sm font-medium text-gray-300 mb-1">OpenRouter Model</label>
          <p className="text-xs text-gray-600 mb-3">
            Any model ID from openrouter.ai/models (e.g. openai/gpt-4o).
          </p>
          <input
            type="text"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder="openai/gpt-4o"
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white font-mono placeholder-gray-600 focus:outline-none focus:border-indigo-500"
          />
        </div>

        {/* Score threshold */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <label className="block text-sm font-medium text-gray-300 mb-1">
            AI Analysis Threshold
          </label>
          <p className="text-xs text-gray-600 mb-3">
            Stocks scoring above this value will be sent to the AI for analysis. Range: 0–150.
          </p>
          <div className="flex items-center gap-3">
            <input
              type="range"
              min={0}
              max={150}
              step={5}
              value={threshold}
              onChange={(e) => setThreshold(Number(e.target.value))}
              className="flex-1 accent-indigo-500"
            />
            <span className="text-sm font-bold text-white w-12 text-right tabular-nums">{threshold}</span>
          </div>
        </div>

        {/* Cache TTL info */}
        {settings && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <p className="text-sm font-medium text-gray-400 mb-1">Price Cache TTL</p>
            <p className="text-sm text-gray-300">{settings.price_cache_ttl_minutes} minutes</p>
            <p className="text-xs text-gray-600 mt-1">Configurable via .env file (PRICE_CACHE_TTL_MINUTES).</p>
          </div>
        )}

        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg text-sm font-medium text-white transition-colors"
        >
          <Save size={14} />
          {saving ? 'Saving...' : saved ? 'Saved!' : 'Save Settings'}
        </button>
      </div>
    </div>
  )
}
