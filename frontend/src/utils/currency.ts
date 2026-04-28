const SYMBOLS: Record<string, string> = {
  USD: '$',
  JPY: '¥',
  EUR: '€',
  GBP: '£',
  HKD: 'HK$',
  CNY: '¥',
  KRW: '₩',
  TWD: 'NT$',
  AUD: 'A$',
  CAD: 'C$',
  SGD: 'S$',
}

export function currencySymbol(currency: string | null | undefined): string {
  if (!currency) return ''
  return SYMBOLS[currency.toUpperCase()] ?? currency + ' '
}

export function formatPrice(price: number, currency: string | null | undefined): string {
  const sym = currencySymbol(currency)
  // JPY and KRW don't use decimals
  const noDecimals = currency === 'JPY' || currency === 'KRW'
  return `${sym}${noDecimals ? price.toLocaleString() : price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}
