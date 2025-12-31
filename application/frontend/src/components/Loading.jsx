export default function Loading() {
  return (
    <div style={{
      display: "flex",
      justifyContent: "center",
      marginTop: "40px"
    }}>
      <div className="spinner"></div>

      <style>{`
        .spinner {
          width: 44px;
          height: 44px;
          border: 4px solid rgba(255,255,255,0.2);
          border-top-color: #09f;
          border-radius: 50%;
          animation: spin 0.7s linear infinite;
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
