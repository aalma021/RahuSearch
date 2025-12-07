import React from "react";

export default function SearchBar({
  text,
  setText,
  onSearch,
  onImageUpload,
  mode,
  setMode,
  k,
  setK,
  alpha,
  setAlpha,
  reranker,
  setReranker,
  rerankerScore,
  setRerankerScore,
  imageFile,
  setImageFile
}) {

  const updateMode = (newMode) => {
    setMode(newMode);

    if (newMode === "keyword") setAlpha(0.00);
    if (newMode === "vector") setAlpha(1.00);
    if (newMode === "hybrid") setAlpha(0.50);
  };

  const normalizeTopK = (v) => {
    let val = parseInt(v);
    if (isNaN(val)) val = 40;
    if (val < 10) val = 10;
    if (val > 200) val = 200;
    setK(val);
  };

  const normalizeAlpha = (v) => {
    let val = parseFloat(String(v).replace(",", "."));
    if (isNaN(val)) val = 0.50;
    if (val < 0) val = 0;
    if (val > 1) val = 1;
    val = parseFloat(val.toFixed(2));
    setAlpha(val);
  };

  const normalizeScore = (v) => {
    let val = parseFloat(String(v).replace(",", "."));
    if (isNaN(val)) val = 0.00;
    if (val < 0) val = 0;
    if (val > 1) val = 1;
    val = parseFloat(val.toFixed(2));
    setRerankerScore(val);
  };

  return (
    <div className="search-card fade-in">

      {/* IMAGE PREVIEW — ONLY CHANGE ADDED! */}
      {imageFile && (
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: "12px",
          background: "#f4f5f7",
          borderRadius: "10px",
          padding: "10px",
          border: "1px solid #ddd",
          marginBottom: "10px"
        }}>

          <img
            src={URL.createObjectURL(imageFile)}
            alt="preview"
            style={{
              width: "55px",
              height: "55px",
              borderRadius: "8px",
              objectFit: "cover",
              border: "1px solid #aaa"
            }}
          />

          <button
            style={{
              background: "#ff5555",
              border: "none",
              padding: "6px 12px",
              color: "white",
              borderRadius: "6px",
              cursor: "pointer",
              fontSize: "13px"
            }}
            onClick={() => setImageFile(null)}
          >
            Remove
          </button>
        </div>
      )}
      {/* END OF IMAGE UI */}


      {/* TOP SEARCH INPUT LINE */}
      <div className="search-top">
        <input
          placeholder="Search..."
          value={text}
          onChange={(e) => setText(e.target.value)}
        />

        <label className="camera-btn">
          📷
          <input
            type="file"
            accept="image/*"
            onChange={(e) => onImageUpload(e.target.files[0])}
          />
        </label>

        <button className="search-btn" onClick={onSearch}>
          Search
        </button>
      </div>

      {/* PARAMETER BAR */}
      <div className="params-bar">

        <div className="param-group">
          <span>Mode</span>
          <div className="param-buttons">
            <button className={mode==="keyword"?"active":""} onClick={() => updateMode("keyword")}>KW</button>
            <button className={mode==="vector"?"active":""} onClick={() => updateMode("vector")}>VS</button>
            <button className={mode==="hybrid"?"active":""} onClick={() => updateMode("hybrid")}>H</button>
          </div>
        </div>

        <div className="param-group">
          <span>Top K</span>
          <input
            type="text"
            value={k}
            onChange={(e) => setK(e.target.value)}
            onBlur={(e) => normalizeTopK(e.target.value)}
          />
        </div>

        <div className="param-group">
          <span>α</span>
          <input
            type="text"
            value={alpha}
            disabled={mode === "keyword" || mode === "vector"}
            onChange={(e) => setAlpha(e.target.value)}
            onBlur={(e) => normalizeAlpha(e.target.value)}
            style={ mode==="keyword" || mode==="vector" ? { opacity: 0.4, cursor:"not-allowed" } : {} }
          />
        </div>

        <div className="param-group" style={{ display:"flex", alignItems:"center", gap:"10px" }}>

          <label className="switch">
            <input
              type="checkbox"
              checked={reranker}
              onChange={() => setReranker(!reranker)}
            />
            <span className="slider"></span>
          </label>

          <div>
            <span style={{ display:"block", marginBottom:"4px" }}>Score ≥</span>
            <input
              type="text"
              value={rerankerScore}
              onChange={(e) => setRerankerScore(e.target.value)}
              onBlur={(e) => normalizeScore(e.target.value)}
            />
          </div>

        </div>

      </div>

    </div>
  );
}
