interface Props {
  name: string | null
  icon: string | null
  color: string | null
  onClick?: () => void
}

export default function CategoryBadge({ name, icon, color, onClick }: Props) {
  if (!name) {
    return (
      <button
        onClick={onClick}
        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-500 hover:bg-gray-200 transition-colors"
      >
        Sin categoría
      </button>
    )
  }
  return (
    <button
      onClick={onClick}
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium transition-colors hover:opacity-80"
      style={{ backgroundColor: color ? `${color}20` : '#f3f4f6', color: color || '#374151' }}
    >
      {icon && <span>{icon}</span>}
      <span>{name}</span>
    </button>
  )
}
