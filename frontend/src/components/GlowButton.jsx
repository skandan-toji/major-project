export default function GlowButton({ children, onClick, disabled, danger, className = '', ...props }) {
  return (
    <button
      className={`btn-glow ${danger ? 'btn-danger' : ''} ${className}`}
      onClick={onClick}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
}
