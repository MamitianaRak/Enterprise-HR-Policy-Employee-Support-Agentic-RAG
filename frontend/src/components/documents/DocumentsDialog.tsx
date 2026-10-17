import { FileText, FolderOpen, Loader2, Trash2, Upload } from 'lucide-react'
import { useRef, useState, type DragEvent } from 'react'
import type { DomainConfig } from '@/api/schemas'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { useDeleteDocument, useDocuments, useUploadDocument } from '@/hooks/queries'
import { formatDate } from '@/lib/ids'
import { cn } from '@/lib/utils'
import { useAppStore } from '@/stores/app-store'

const ACCEPT = '.pdf,.txt,.md,.docx'

export function DocumentsDialog({ domain }: { domain: DomainConfig }) {
  const [open, setOpen] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const adminKey = useAppStore((s) => s.adminKey)
  const setAdminKey = useAppStore((s) => s.setAdminKey)

  const documents = useDocuments(domain.name, open)
  const upload = useUploadDocument(domain.name)
  const remove = useDeleteDocument(domain.name)

  const onDrop = (e: DragEvent) => {
    e.preventDefault()
    setDragging(false)
    if (e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0])
  }

  const submit = () => {
    if (!file) return
    upload.mutate({ file, adminKey }, { onSuccess: () => setFile(null) })
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={<Button variant="outline" className="w-full justify-start" />}>
        <FolderOpen data-icon="inline-start" /> {domain.documents_label}
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{domain.documents_label}</DialogTitle>
          <DialogDescription>
            PDF, TXT, Markdown or DOCX. Files are chunked, embedded and indexed into the knowledge base. Uploading a file
            with the same name replaces it.
          </DialogDescription>
        </DialogHeader>

        <label className="grid gap-1.5 text-sm">
          <span className="font-medium">Admin API key</span>
          <Input type="password" autoComplete="off" value={adminKey} onChange={(e) => setAdminKey(e.target.value)} />
        </label>

        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          className={cn(
            'flex flex-col items-center gap-1 rounded-xl border-2 border-dashed px-4 py-6 text-sm transition-colors',
            dragging ? 'border-[var(--domain)] bg-[var(--domain)]/5' : 'hover:bg-muted/50',
          )}
        >
          <Upload className="size-5 text-muted-foreground" aria-hidden />
          <span className="font-medium">{file ? file.name : 'Drop a file here or click to browse'}</span>
          <span className="text-xs text-muted-foreground">{ACCEPT.replaceAll(',', ' ')}</span>
        </button>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          hidden
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />

        <Button onClick={submit} disabled={!file || !adminKey || upload.isPending}>
          {upload.isPending ? <Loader2 className="animate-spin" data-icon="inline-start" /> : <Upload data-icon="inline-start" />}
          {upload.isPending ? 'Indexing…' : 'Index document'}
        </Button>

        <div className="space-y-2">
          <h3 className="text-sm font-medium">Indexed documents</h3>
          {documents.isLoading ? (
            <Skeleton className="h-12 w-full rounded-xl" />
          ) : !documents.data?.length ? (
            <p className="text-sm text-muted-foreground">No document indexed from this app yet.</p>
          ) : (
            <ul className="max-h-56 space-y-1.5 overflow-y-auto">
              {documents.data.map((d) => (
                <li key={d.filename} className="flex items-center gap-2.5 rounded-xl border px-3 py-2">
                  <FileText className="size-4 shrink-0 text-muted-foreground" aria-hidden />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-medium" title={d.filename}>
                      {d.filename}
                    </span>
                    <span className="block text-xs text-muted-foreground">
                      {d.chunks} chunks · {formatDate(d.indexed_at)}
                    </span>
                  </span>
                  <Button
                    variant="ghost"
                    size="icon-xs"
                    disabled={!adminKey || remove.isPending}
                    onClick={() => remove.mutate({ filename: d.filename, adminKey })}
                    aria-label={`Remove ${d.filename}`}
                    title={adminKey ? 'Remove from knowledge base' : 'Enter the admin key first'}
                    className="hover:text-destructive"
                  >
                    <Trash2 />
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
