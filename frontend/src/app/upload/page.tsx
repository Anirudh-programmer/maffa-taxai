'use client'
import { useCallback, useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import {
  Upload, FileText, CheckCircle, XCircle, Loader2, Trash2,
  Eye, AlertCircle, File, Clock
} from 'lucide-react'
import toast from 'react-hot-toast'
import { AppShell } from '@/components/layout/AppShell'
import { documentsApi } from '@/lib/api'
import { useAuthStore, useUIStore } from '@/store'
import { formatFileSize, formatDate, getDocumentTypeLabel, getDocumentTypeColor, cn } from '@/lib/utils'
import type { UploadedDocument } from '@/types'

const DOC_TYPES = [
  { value: 'form_16', label: 'Form 16' },
  { value: 'salary_slip', label: 'Salary Slip' },
  { value: 'itr', label: 'ITR PDF' },
  { value: 'investment_proof', label: 'Investment Proof' },
  { value: 'other', label: 'Other' },
]

function DocumentCard({ doc, onDelete }: { doc: UploadedDocument; onDelete: (id: string) => void }) {
  const [analysis, setAnalysis] = useState<Record<string, unknown> | null>(null)
  const [showAnalysis, setShowAnalysis] = useState(false)

  const loadAnalysis = async () => {
    if (analysis) { setShowAnalysis(!showAnalysis); return }
    try {
      const data = await documentsApi.getAnalysis(doc.id)
      setAnalysis(data)
      setShowAnalysis(true)
    } catch {
      toast.error('Could not load analysis')
    }
  }

  const statusIcon = {
    uploaded: <Clock className="w-4 h-4 text-yellow-400" />,
    processing: <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />,
    processed: <CheckCircle className="w-4 h-4 text-green-400" />,
    failed: <XCircle className="w-4 h-4 text-red-400" />,
  }[doc.status]

  const statusLabel = {
    uploaded: 'Queued', processing: 'Processing...', processed: 'Analyzed', failed: 'Failed',
  }[doc.status]

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass rounded-xl overflow-hidden"
    >
      <div className="p-5 flex items-start gap-4">
        <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center flex-shrink-0">
          <FileText className="w-5 h-5 text-muted-foreground" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-medium text-sm truncate">{doc.original_filename}</span>
            <span className={cn('text-xs px-2 py-0.5 rounded-full flex-shrink-0', getDocumentTypeColor(doc.document_type))}>
              {getDocumentTypeLabel(doc.document_type)}
            </span>
          </div>
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <span>{formatFileSize(doc.file_size)}</span>
            <span>{formatDate(doc.created_at)}</span>
            {doc.financial_year && <span>FY {doc.financial_year}</span>}
          </div>
        </div>
        <div className="flex items-center gap-3 flex-shrink-0">
          <div className="flex items-center gap-1.5 text-xs">
            {statusIcon}
            <span className="text-muted-foreground">{statusLabel}</span>
          </div>
          {doc.status === 'processed' && (
            <button onClick={loadAnalysis} className="p-1.5 rounded-lg hover:bg-white/10 text-muted-foreground hover:text-brand-400 transition-all">
              <Eye className="w-4 h-4" />
            </button>
          )}
          <button onClick={() => onDelete(doc.id)} className="p-1.5 rounded-lg hover:bg-red-500/10 text-muted-foreground hover:text-red-400 transition-all">
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      <AnimatePresence>
        {showAnalysis && analysis && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="border-t border-white/5 p-5 bg-white/[0.02]"
          >
            <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-brand-400" />
              AI Analysis
            </h4>
            {(analysis as any).extracted_data?.summary && (
              <p className="text-sm text-muted-foreground mb-3 leading-relaxed">
                {(analysis as any).extracted_data.summary}
              </p>
            )}
            {(analysis as any).extracted_data?.key_observations?.length > 0 && (
              <div className="mb-3">
                <p className="text-xs font-medium text-brand-400 mb-1.5">Key Observations</p>
                <div className="space-y-1">
                  {(analysis as any).extracted_data.key_observations.map((obs: string, i: number) => (
                    <div key={i} className="flex items-start gap-2 text-sm">
                      <div className="w-1 h-1 rounded-full bg-brand-400 mt-2 flex-shrink-0" />
                      <span className="text-muted-foreground">{obs}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {(analysis as any).extracted_data?.tax_saving_opportunities?.length > 0 && (
              <div>
                <p className="text-xs font-medium text-green-400 mb-1.5">Tax Saving Opportunities</p>
                <div className="space-y-1">
                  {(analysis as any).extracted_data.tax_saving_opportunities.map((opp: string, i: number) => (
                    <div key={i} className="flex items-start gap-2 text-sm">
                      <div className="w-1 h-1 rounded-full bg-green-400 mt-2 flex-shrink-0" />
                      <span className="text-muted-foreground">{opp}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {(analysis as any).extracted_text && (
              <div className="mt-4 pt-4 border-t border-white/5">
                <p className="text-xs font-medium text-brand-400 mb-2">Raw Extracted Text</p>
                <div className="bg-black/20 border border-white/5 rounded-xl p-3.5 max-h-48 overflow-y-auto font-mono text-xs text-muted-foreground/80 leading-relaxed whitespace-pre-wrap selection:bg-brand-500/20 scrollbar-thin">
                  {(analysis as any).extracted_text}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default function UploadPage() {
  const { documents, setDocuments } = useUIStore()
  const [uploading, setUploading] = useState<Array<{ name: string; progress: number }>>([])
  const [selectedType, setSelectedType] = useState('other')
  const [loadingDocs, setLoadingDocs] = useState(documents.length === 0)
  const { user } = useAuthStore()

  useEffect(() => {
    if (!user) return
    documentsApi.list()
      .then(setDocuments)
      .catch(console.error)
      .finally(() => setLoadingDocs(false))
  }, [user, setDocuments])

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    for (const file of acceptedFiles) {
      const upload = { name: file.name, progress: 0 }
      setUploading(prev => [...prev, upload])
      try {
        const doc = await documentsApi.upload(file, selectedType)
        setDocuments(prev => [doc, ...prev])
        toast.success(`${file.name} uploaded and analyzing!`)
      } catch (e: any) {
        toast.error(e?.response?.data?.detail || `Failed to upload ${file.name}`)
      } finally {
        setUploading(prev => prev.filter(u => u.name !== file.name))
      }
    }
  }, [selectedType])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'image/jpeg': ['.jpg', '.jpeg'], 'image/png': ['.png'] },
    maxSize: 10 * 1024 * 1024,
  })

  const handleDelete = async (id: string) => {
    try {
      await documentsApi.delete(id)
      setDocuments(prev => prev.filter(d => d.id !== id))
      toast.success('Document deleted')
    } catch {
      toast.error('Failed to delete')
    }
  }

  return (
    <AppShell>
      <div className="p-6 md:p-8 max-w-4xl mx-auto">
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <h1 className="font-display font-bold text-3xl mb-1 flex items-center gap-3">
            <Upload className="w-7 h-7 text-brand-400" />
            Tax Documents
          </h1>
          <p className="text-muted-foreground">Upload Form 16, salary slips, ITR PDFs for AI-powered analysis</p>
        </motion.div>

        {/* Document type selector */}
        <div className="glass rounded-2xl p-5 mb-5">
          <p className="text-sm text-muted-foreground mb-3">Document type</p>
          <div className="flex flex-wrap gap-2">
            {DOC_TYPES.map((type) => (
              <button
                key={type.value}
                onClick={() => setSelectedType(type.value)}
                className={cn(
                  'px-3 py-1.5 rounded-lg text-sm transition-all',
                  selectedType === type.value
                    ? 'bg-brand-500/20 text-brand-400 border border-brand-500/30'
                    : 'bg-white/5 text-muted-foreground hover:text-foreground border border-transparent hover:border-white/10'
                )}
              >
                {type.label}
              </button>
            ))}
          </div>
        </div>

        {/* Dropzone */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <div
            {...getRootProps()}
            className={cn(
              'border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all mb-6',
              isDragActive
                ? 'border-brand-500/60 bg-brand-500/5'
                : 'border-white/10 hover:border-brand-500/30 hover:bg-white/[0.02]'
            )}
          >
            <input {...getInputProps()} />
            <motion.div animate={isDragActive ? { scale: 1.05 } : { scale: 1 }}>
              <div className="w-14 h-14 rounded-2xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center mx-auto mb-4">
                <Upload className="w-6 h-6 text-brand-400" />
              </div>
              <p className="font-semibold text-lg mb-1">
                {isDragActive ? 'Drop files here' : 'Drop your tax documents here'}
              </p>
              <p className="text-muted-foreground text-sm mb-4">
                or click to browse · PDF, JPG, PNG · Max 10MB
              </p>
              <div className="flex items-center justify-center gap-4 text-xs text-muted-foreground">
                {['Form 16', 'Salary Slip', 'ITR PDF', 'Investment Proof'].map((t) => (
                  <span key={t} className="flex items-center gap-1">
                    <File className="w-3 h-3" /> {t}
                  </span>
                ))}
              </div>
            </motion.div>
          </div>
        </motion.div>

        {/* Upload progress */}
        {uploading.length > 0 && (
          <div className="space-y-2 mb-5">
            {uploading.map((u) => (
              <div key={u.name} className="glass rounded-xl p-4 flex items-center gap-3">
                <Loader2 className="w-4 h-4 text-brand-400 animate-spin flex-shrink-0" />
                <span className="text-sm flex-1 truncate">{u.name}</span>
                <span className="text-xs text-muted-foreground">Uploading...</span>
              </div>
            ))}
          </div>
        )}

        {/* Documents list */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold">
              {loadingDocs ? 'Documents' : `${documents.length} Document${documents.length !== 1 ? 's' : ''}`}
            </h2>
            {documents.length > 0 && (
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <AlertCircle className="w-3.5 h-3.5" />
                Indexed for AI chat context
              </div>
            )}
          </div>

          {loadingDocs ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="skeleton h-20 rounded-xl" />
              ))}
            </div>
          ) : documents.length === 0 ? (
            <div className="glass rounded-2xl p-12 text-center">
              <FileText className="w-10 h-10 text-muted-foreground/30 mx-auto mb-3" />
              <p className="text-muted-foreground text-sm">No documents uploaded yet</p>
              <p className="text-muted-foreground/60 text-xs mt-1">Upload your Form 16 or salary slips to get started</p>
            </div>
          ) : (
            <div className="space-y-3">
              {documents.map((doc) => (
                <DocumentCard key={doc.id} doc={doc} onDelete={handleDelete} />
              ))}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  )
}
