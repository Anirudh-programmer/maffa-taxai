import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(amount: number): string {
  if (amount >= 10000000) return `₹${(amount / 10000000).toFixed(2)}Cr`
  if (amount >= 100000) return `₹${(amount / 100000).toFixed(2)}L`
  if (amount >= 1000) return `₹${(amount / 1000).toFixed(1)}K`
  return `₹${amount.toLocaleString('en-IN')}`
}

export function formatCurrencyFull(amount: number): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount)
}

export function formatPercentage(value: number): string {
  return `${value.toFixed(1)}%`
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric',
  })
}

export function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)
  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return formatDate(dateStr)
}

export function getDocumentTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    form_16: 'Form 16',
    salary_slip: 'Salary Slip',
    itr: 'ITR',
    investment_proof: 'Investment Proof',
    other: 'Document',
  }
  return labels[type] || 'Document'
}

export function getDocumentTypeColor(type: string): string {
  const colors: Record<string, string> = {
    form_16: 'text-blue-400 bg-blue-400/10',
    salary_slip: 'text-green-400 bg-green-400/10',
    itr: 'text-purple-400 bg-purple-400/10',
    investment_proof: 'text-yellow-400 bg-yellow-400/10',
    other: 'text-gray-400 bg-gray-400/10',
  }
  return colors[type] || colors.other
}

export function truncate(str: string, length: number): string {
  return str.length > length ? `${str.slice(0, length)}...` : str
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1048576).toFixed(1)} MB`
}

export const SUGGESTED_PROMPTS = [
  'Which tax regime saves me more money?',
  'How to maximize Section 80C deductions?',
  'Explain HRA exemption calculation',
  'Should I invest in NPS for tax saving?',
  'What changed in Budget 2024 for salaried employees?',
  'How is capital gains tax calculated on mutual funds?',
  'Help me understand my Form 16',
  'What documents do I need to file ITR?',
]
