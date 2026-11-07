// Round avatar: a head image, or an emoji when there is no image.
export default function Avatar({ src, emoji = '🎫', className = 'h-10 w-10' }) {
  return (
    <div className={`flex shrink-0 items-center justify-center overflow-hidden rounded-full border-2 border-[#e2c39a] bg-[#ece0fb] ${className}`}>
      {src
        ? <img src={src} alt="" className="h-full w-full object-contain p-0.5" />
        : <span className="text-lg leading-none">{emoji}</span>}
    </div>
  )
}
