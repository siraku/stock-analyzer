import { useEffect, useRef } from 'react'
import { createChart, ColorType } from 'lightweight-charts'
import type { IChartApi } from 'lightweight-charts'
import { PriceBar } from '@/types/stock'
import { SignalSnapshot } from '@/types/analysis'

interface Props {
  bars: PriceBar[]
  snapshot?: SignalSnapshot | null
}

export default function PriceChart({ bars, snapshot }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)

  useEffect(() => {
    if (!containerRef.current) return

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#0f172a' },
        textColor: '#9ca3af',
      },
      grid: {
        vertLines: { color: '#1e293b' },
        horzLines: { color: '#1e293b' },
      },
      width: containerRef.current.clientWidth,
      height: 300,
      timeScale: { borderColor: '#1e293b' },
      rightPriceScale: { borderColor: '#1e293b' },
    })
    chartRef.current = chart

    // Candlestick series (v4 API)
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#10b981',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    })

    const candleData = bars
      .filter((b) => b.open && b.high && b.low && b.close)
      .map((b) => ({
        time: b.date as `${number}-${number}-${number}`,
        open: b.open!,
        high: b.high!,
        low: b.low!,
        close: b.close!,
      }))
    candleSeries.setData(candleData)

    // EMA20 overlay
    if (snapshot?.ema20 && bars.length > 0) {
      const ema20Series = chart.addLineSeries({
        color: '#6366f1',
        lineWidth: 1,
        title: 'EMA20',
        lastValueVisible: true,
        priceLineVisible: false,
      })
      const lastBar = bars[bars.length - 1]
      ema20Series.setData([
        { time: lastBar.date as `${number}-${number}-${number}`, value: snapshot.ema20 },
      ])
    }

    // EMA50 overlay
    if (snapshot?.ema50 && bars.length > 0) {
      const ema50Series = chart.addLineSeries({
        color: '#f59e0b',
        lineWidth: 1,
        title: 'EMA50',
        lastValueVisible: true,
        priceLineVisible: false,
      })
      const lastBar = bars[bars.length - 1]
      ema50Series.setData([
        { time: lastBar.date as `${number}-${number}-${number}`, value: snapshot.ema50 },
      ])
    }

    chart.timeScale().fitContent()

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth })
      }
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [bars, snapshot])

  return <div ref={containerRef} className="w-full rounded-lg overflow-hidden" />
}
