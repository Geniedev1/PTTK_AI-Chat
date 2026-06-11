import type { ReactNode } from "react"

type ButtonProps = {
  children: ReactNode
  className?: string
  disabled?: boolean
  type?: "button" | "submit"
  variant?: "primary" | "secondary" | "danger" | "ghost"
  onClick?: () => void
}

export function Button({
  children,
  className = "",
  disabled = false,
  type = "button",
  variant = "secondary",
  onClick,
}: ButtonProps) {
  return (
    <button
      className={`btn btn-${variant} ${className}`.trim()}
      disabled={disabled}
      type={type}
      onClick={onClick}
    >
      {children}
    </button>
  )
}

type PageHeaderProps = {
  title: string
  eyebrow?: string
  description?: string
  actions?: ReactNode
}

export function PageHeader({ title, eyebrow, description, actions }: PageHeaderProps) {
  return (
    <div className="page-header">
      <div>
        {eyebrow ? <span className="eyebrow">{eyebrow}</span> : null}
        <h1>{title}</h1>
        {description ? <p>{description}</p> : null}
      </div>
      {actions ? <div className="page-actions">{actions}</div> : null}
    </div>
  )
}

type StatusBadgeProps = {
  children: ReactNode
  tone?: "neutral" | "success" | "warning" | "danger" | "info"
}

export function StatusBadge({ children, tone = "neutral" }: StatusBadgeProps) {
  return <span className={`status-badge status-${tone}`}>{children}</span>
}

export function statusTone(status?: string): StatusBadgeProps["tone"] {
  switch ((status || "").toUpperCase()) {
    case "PAID":
    case "COMPLETED":
    case "DELIVERED":
    case "ACTIVE":
      return "success"
    case "PENDING":
    case "CONFIRMED":
    case "READY_TO_SHIP":
    case "PROCESSING":
      return "warning"
    case "CANCELLED":
    case "FAILED":
    case "OUT_OF_STOCK":
      return "danger"
    case "SHIPPED":
      return "info"
    default:
      return "neutral"
  }
}

type EmptyStateProps = {
  title: string
  description?: string
  action?: ReactNode
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <h2>{title}</h2>
      {description ? <p>{description}</p> : null}
      {action ? <div className="empty-action">{action}</div> : null}
    </div>
  )
}

export function LoadingState({ label = "Loading..." }: { label?: string }) {
  return <div className="state-line">{label}</div>
}

export function ErrorBanner({ message }: { message: string }) {
  return <div className="error-banner">{message}</div>
}

type MetricCardProps = {
  label: string
  value: ReactNode
  hint?: string
}

export function MetricCard({ label, value, hint }: MetricCardProps) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
      {hint ? <small>{hint}</small> : null}
    </div>
  )
}

type PaginationProps = {
  page: number
  pageCount: number
  total: number
  pageSize: number
  onPageChange: (page: number) => void
}

export function Pagination({ page, pageCount, total, pageSize, onPageChange }: PaginationProps) {
  const safePageCount = Math.max(1, pageCount)
  const start = total === 0 ? 0 : (page - 1) * pageSize + 1
  const end = Math.min(total, page * pageSize)

  return (
    <div className="pagination">
      <span>
        {start}-{end} of {total}
      </span>
      <div className="pagination-controls">
        <Button disabled={page <= 1} variant="ghost" onClick={() => onPageChange(page - 1)}>
          Previous
        </Button>
        <strong>
          {page} / {safePageCount}
        </strong>
        <Button disabled={page >= safePageCount} variant="ghost" onClick={() => onPageChange(page + 1)}>
          Next
        </Button>
      </div>
    </div>
  )
}

export function formatCurrency(value: string | number | null | undefined) {
  const amount = Number(value ?? 0)
  if (!Number.isFinite(amount)) {
    return "$0.00"
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(amount)
}

export function formatDateTime(value?: string | null) {
  if (!value) {
    return "-"
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return "-"
  }
  return date.toLocaleString()
}
