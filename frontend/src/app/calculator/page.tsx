'use client'
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Calculator, TrendingUp, TrendingDown, CheckCircle, Save, Download, ChevronDown, ChevronUp } from 'lucide-react'
import toast from 'react-hot-toast'
import { AppShell } from '@/components/layout/AppShell'
import { taxApi } from '@/lib/api'
import { formatCurrencyFull, formatPercentage, cn } from '@/lib/utils'
import type { TaxInput, TaxCalculationResult, RegimeResult } from '@/types'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

const defaultInput: TaxInput = {
  basic_salary: 600000, hra_received: 120000, other_allowances: 60000,
  business_income: 0, rental_income: 0, interest_income: 0,
  capital_gains_short: 0, capital_gains_long: 0, other_income: 0,
  rent_paid: 120000, city_type: 'metro',
  section_80c: 150000, section_80ccd_nps: 50000, section_80d: 25000,
  section_80e: 0, section_80g: 0, section_80tta: 10000, section_80ttb: 0,
  home_loan_interest: 0, home_loan_principal: 0,
  lta_exemption: 0, professional_tax: 2400,
  age: 30, is_senior_citizen: false, is_super_senior_citizen: false,
  financial_year: '2026-27',
}

function InputField({ label, name, value, onChange, max, hint }: {
  label: string; name: string; value: number; onChange: (name: string, val: number) => void; max?: number; hint?: string
}) {
  return (
    <div>
      <label className="block text-xs text-muted-foreground mb-1.5">{label}</label>
      <div className="relative">
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm">₹</span>
        <input
          type="number"
          value={value || ''}
          onChange={(e) => onChange(name, Math.min(parseFloat(e.target.value) || 0, max || 999999999))}
          className="w-full bg-white/5 border border-white/10 rounded-lg pl-7 pr-3 py-2.5 text-sm focus:outline-none focus:border-brand-500/50 transition-colors"
          min={0}
          max={max}
          step={1000}
        />
      </div>
      {hint && <p className="text-[11px] text-muted-foreground mt-1">{hint}</p>}
    </div>
  )
}

function RegimeCard({ label, result, isRecommended, regime }: {
  label: string; result: RegimeResult; isRecommended: boolean; regime: string
}) {
  return (
    <div className={cn(
      'rounded-2xl p-6 border transition-all',
      isRecommended
        ? 'bg-brand-500/10 border-brand-500/30 glow-teal'
        : 'glass border-white/10'
    )}>
      {isRecommended && (
        <div className="flex items-center gap-1.5 mb-3">
          <CheckCircle className="w-4 h-4 text-brand-400" />
          <span className="text-xs font-medium text-brand-400">Recommended</span>
        </div>
      )}
      <h3 className="font-display font-bold text-xl mb-4">{label}</h3>
      <div className="space-y-3">
        {[
          { label: 'Gross Income', value: result.gross_income },
          { label: 'Total Deductions', value: result.total_deductions },
          { label: 'Taxable Income', value: result.taxable_income },
          { label: 'Basic Tax', value: result.basic_tax },
          { label: 'Cess (4%)', value: result.cess },
        ].map((row) => (
          <div key={row.label} className="flex justify-between text-sm">
            <span className="text-muted-foreground">{row.label}</span>
            <span className="font-medium">{formatCurrencyFull(row.value)}</span>
          </div>
        ))}
        <div className="border-t border-white/10 pt-3">
          <div className="flex justify-between">
            <span className="font-semibold">Total Tax Payable</span>
            <span className={cn('font-bold text-lg', isRecommended ? 'text-brand-400' : '')}>
              {formatCurrencyFull(result.total_tax)}
            </span>
          </div>
          <div className="flex justify-between text-sm mt-1">
            <span className="text-muted-foreground">Effective Rate</span>
            <span className="text-muted-foreground">{formatPercentage(result.effective_rate)}</span>
          </div>
          <div className="flex justify-between text-sm mt-1">
            <span className="text-muted-foreground">Monthly Take-home</span>
            <span className="text-green-400 font-medium">{formatCurrencyFull(result.take_home_monthly)}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function CalculatorPage() {
  const [input, setInput] = useState<TaxInput>(defaultInput)
  const [result, setResult] = useState<TaxCalculationResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [showDeductions, setShowDeductions] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)

  const updateField = (name: string, value: number) => {
    setInput(prev => ({ ...prev, [name]: value }))
  }

  const updateSelect = (name: string, value: string) => {
    setInput(prev => ({ ...prev, [name]: value }))
  }

  const calculate = async () => {
    setLoading(true)
    try {
      const res = await taxApi.calculate(input)
      setResult(res)
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Calculation failed')
    } finally {
      setLoading(false)
    }
  }

  const saveCalculation = async () => {
    if (!result) return
    try {
      await taxApi.saveCalculation({
        title: `Tax Calculation ${new Date().toLocaleDateString('en-IN')}`,
        input_data: input as unknown as Record<string, unknown>,
        old_regime_result: result.old_regime as unknown as Record<string, unknown>,
        new_regime_result: result.new_regime as unknown as Record<string, unknown>,
        recommended_regime: result.recommended_regime,
        tax_saved: result.tax_saved,
        financial_year: input.financial_year,
      })
      toast.success('Calculation saved!')
    } catch {
      toast.error('Failed to save')
    }
  }

  const chartData = result ? [
    { name: 'Old Regime', tax: result.old_regime.total_tax, fill: '#6366f1' },
    { name: 'New Regime', tax: result.new_regime.total_tax, fill: '#14b8a6' },
  ] : []

  return (
    <AppShell>
      <div className="p-6 md:p-8 max-w-6xl mx-auto">
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <h1 className="font-display font-bold text-3xl mb-1 flex items-center gap-3">
            <Calculator className="w-7 h-7 text-brand-400" />
            Tax Calculator
          </h1>
          <p className="text-muted-foreground">FY 2026-27 · Old vs New Regime comparison</p>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Input form */}
          <div className="space-y-5">
            {/* Income */}
            <div className="glass rounded-2xl p-6">
              <h2 className="font-semibold mb-4 flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-brand-500/20 text-brand-400 text-xs flex items-center justify-center font-bold">1</span>
                Income Details
              </h2>
              <div className="grid grid-cols-2 gap-4">
                <InputField label="Basic Salary" name="basic_salary" value={input.basic_salary} onChange={updateField} />
                <InputField label="HRA Received" name="hra_received" value={input.hra_received} onChange={updateField} />
                <InputField label="Other Allowances" name="other_allowances" value={input.other_allowances} onChange={updateField} />
                <InputField label="Rent Paid / Month × 12" name="rent_paid" value={input.rent_paid} onChange={updateField} />
                <div>
                  <label className="block text-xs text-muted-foreground mb-1.5">City Type</label>
                  <select
                    value={input.city_type}
                    onChange={(e) => updateSelect('city_type', e.target.value)}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-brand-500/50"
                  >
                    <option value="metro">Metro (Delhi/Mumbai/Kolkata/Chennai)</option>
                    <option value="non_metro">Non-Metro</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-muted-foreground mb-1.5">Age</label>
                  <input
                    type="number"
                    value={input.age || ''}
                    onChange={(e) => {
                      const val = parseInt(e.target.value);
                      setInput(p => ({ ...p, age: isNaN(val) ? 0 : val }));
                    }}
                    onBlur={() => {
                      if (!input.age || input.age < 1) {
                        setInput(p => ({ ...p, age: 30 }));
                      } else if (input.age < 18) {
                        setInput(p => ({ ...p, age: 18 }));
                      }
                    }}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-brand-500/50"
                    min={18} max={100}
                  />
                </div>
              </div>

              {/* Other income toggle */}
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="mt-4 flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                Other Income (Business, Rental, Capital Gains)
              </button>
              {showAdvanced && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="grid grid-cols-2 gap-4 mt-4">
                  <InputField label="Business Income" name="business_income" value={input.business_income} onChange={updateField} />
                  <InputField label="Rental Income" name="rental_income" value={input.rental_income} onChange={updateField} />
                  <InputField label="Interest Income" name="interest_income" value={input.interest_income} onChange={updateField} />
                  <InputField label="Short-term Capital Gains" name="capital_gains_short" value={input.capital_gains_short} onChange={updateField} />
                  <InputField label="Long-term Capital Gains" name="capital_gains_long" value={input.capital_gains_long} onChange={updateField} />
                </motion.div>
              )}
            </div>

            {/* Deductions */}
            <div className="glass rounded-2xl p-6">
              <button
                onClick={() => setShowDeductions(!showDeductions)}
                className="w-full flex items-center justify-between"
              >
                <h2 className="font-semibold flex items-center gap-2">
                  <span className="w-6 h-6 rounded-full bg-brand-500/20 text-brand-400 text-xs flex items-center justify-center font-bold">2</span>
                  Deductions (Old Regime)
                </h2>
                {showDeductions ? <ChevronUp className="w-4 h-4 text-muted-foreground" /> : <ChevronDown className="w-4 h-4 text-muted-foreground" />}
              </button>

              <AnimatePresence>
                {showDeductions && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="grid grid-cols-2 gap-4 mt-4"
                  >
                    <InputField label="Section 80C" name="section_80c" value={input.section_80c} onChange={updateField} max={150000} hint="Max ₹1,50,000" />
                    <InputField label="NPS 80CCD(1B)" name="section_80ccd_nps" value={input.section_80ccd_nps} onChange={updateField} max={50000} hint="Max ₹50,000" />
                    <InputField label="Health Insurance 80D" name="section_80d" value={input.section_80d} onChange={updateField} max={100000} hint="Max ₹1,00,000" />
                    <InputField label="Home Loan Interest 24b" name="home_loan_interest" value={input.home_loan_interest} onChange={updateField} max={200000} hint="Max ₹2,00,000" />
                    <InputField label="Education Loan 80E" name="section_80e" value={input.section_80e} onChange={updateField} />
                    <InputField label="Donations 80G" name="section_80g" value={input.section_80g} onChange={updateField} />
                    <InputField label="Savings Interest 80TTA" name="section_80tta" value={input.section_80tta} onChange={updateField} max={10000} hint="Max ₹10,000" />
                    <InputField label="Professional Tax" name="professional_tax" value={input.professional_tax} onChange={updateField} max={2500} hint="Max ₹2,500" />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <button
              onClick={calculate}
              disabled={loading}
              className="w-full py-4 rounded-xl bg-brand-500 hover:bg-brand-400 disabled:opacity-50 font-semibold text-white transition-all glow-teal hover:glow-teal-strong flex items-center justify-center gap-2"
            >
              {loading ? (
                <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Calculating...</>
              ) : (
                <><Calculator className="w-4 h-4" />Calculate Tax</>
              )}
            </button>
          </div>

          {/* Results */}
          <div>
            {!result ? (
              <div className="glass rounded-2xl p-12 text-center h-full flex flex-col items-center justify-center">
                <Calculator className="w-12 h-12 text-muted-foreground/30 mx-auto mb-4" />
                <p className="text-muted-foreground text-sm">Fill in your income details and click Calculate to see your tax analysis</p>
              </div>
            ) : (
              <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="space-y-5">
                {/* Summary banner */}
                <div className="glass-strong rounded-2xl p-5 border border-brand-500/20 glow-teal">
                  <div className="flex items-center gap-3 mb-3">
                    <CheckCircle className="w-5 h-5 text-brand-400" />
                    <span className="font-semibold">
                      {result.recommended_regime === 'old' ? 'Old' : 'New'} Regime saves you more
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-3xl font-display font-bold text-brand-400">
                        {formatCurrencyFull(result.tax_saved)}
                      </div>
                      <div className="text-sm text-muted-foreground">annual savings · {formatPercentage(result.savings_percentage)} less tax</div>
                    </div>
                    <div className="flex gap-2">
                      <button onClick={saveCalculation} className="flex items-center gap-1.5 bg-white/10 hover:bg-white/15 px-3 py-2 rounded-lg text-sm transition-all">
                        <Save className="w-3.5 h-3.5" /> Save
                      </button>
                    </div>
                  </div>
                </div>

                {/* Chart */}
                <div className="glass rounded-2xl p-5">
                  <h3 className="font-semibold mb-4">Tax Comparison</h3>
                  <ResponsiveContainer width="100%" height={160}>
                    <BarChart data={chartData} barSize={48}>
                      <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#888' }} />
                      <YAxis hide />
                      <Tooltip
                        contentStyle={{ background: 'hsl(222 47% 9%)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }}
                        formatter={(v: number) => [formatCurrencyFull(v), 'Total Tax']}
                      />
                      <Bar dataKey="tax" radius={[6, 6, 0, 0]}>
                        {chartData.map((entry, i) => (
                          <Cell key={i} fill={entry.fill} fillOpacity={result.recommended_regime === (i === 0 ? 'old' : 'new') ? 1 : 0.5} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Regime cards */}
                <div className="grid gap-4">
                  <RegimeCard
                    label="Old Tax Regime"
                    result={result.old_regime}
                    isRecommended={result.recommended_regime === 'old'}
                    regime="old"
                  />
                  <RegimeCard
                    label="New Tax Regime"
                    result={result.new_regime}
                    isRecommended={result.recommended_regime === 'new'}
                    regime="new"
                  />
                </div>

                {/* Recommendations */}
                <div className="glass rounded-2xl p-5">
                  <h3 className="font-semibold mb-3 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-brand-400" />
                    AI Recommendations
                  </h3>
                  <div className="space-y-2">
                    {result.key_recommendations.map((rec, i) => (
                      <div key={i} className="flex items-start gap-2 text-sm">
                        <div className="w-1.5 h-1.5 rounded-full bg-brand-400 mt-2 flex-shrink-0" />
                        <span className="text-muted-foreground leading-relaxed">{rec}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  )
}
