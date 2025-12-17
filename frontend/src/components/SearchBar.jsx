import React, { useState } from "react";

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
  setImageFile,
  store,
  setStore
}) {

  const [open, setOpen] = useState(false);

  const updateMode = (newMode) => {
    setMode(newMode);

    if (newMode === "keyword") setAlpha(0.0);
    if (newMode === "vector") setAlpha(1.0);
    if (newMode === "hybrid") setAlpha(0.5);
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
    if (isNaN(val)) val = 0.5;
    if (val < 0) val = 0;
    if (val > 1) val = 1;
    val = parseFloat(val.toFixed(2));
    setAlpha(val);
  };

  const normalizeScore = (v) => {
    let val = parseFloat(String(v).replace(",", "."));
    if (isNaN(val)) val = 0.0;
    if (val < 0) val = 0;
    if (val > 1) val = 1;
    val = parseFloat(val.toFixed(2));
    setRerankerScore(val);
  };

  return (
    <div className="search-card fade-in">

      {imageFile && (
        <div className="image-preview-box">
          <img
            src={URL.createObjectURL(imageFile)}
            alt="preview"
            className="image-preview-thumb"
          />
          <button
            className="remove-image-btn"
            onClick={() => setImageFile(null)}
          >
            Remove
          </button>
        </div>
      )}

      {/* SEARCH BAR */}
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
        <button
          type="button"
          className="search-btn"
          onClick={onSearch}
          onTouchStart={onSearch}
        >
          Search
        </button>
      </div>

      {/* ADVANCED BUTTON - NEW STYLE */}
      <button
        onClick={() => setOpen(!open)}
        className="advanced-filters-btn"
        style={{
          background: open ? "#e55d2e" : "#FC6736"
        }}
      >
        {open ? "Hide Filters" : "Advanced Filters"}
      </button>

      {open && (
        <div className="params-bar">

          {/* Store Filter */}
          <div className="param-group">
            <span>Store</span>
            <input
              type="text"
              placeholder="jarir | noon | almanea"
              value={store}
              onChange={(e) => setStore(e.target.value)}
            />
          </div>

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
              style={mode==="keyword" || mode==="vector" ? { opacity: 0.4, cursor:"not-allowed" } : {}}
            />
          </div>

          <div className="param-group" style={{ display:"flex", alignItems:"center", gap:"14px" }}>
            <div style={{ display:"flex", flexDirection:"column", alignItems:"center" }}>
              <span style={{ fontSize:"13px", marginBottom:"4px", fontWeight:"600" }}>Reranker</span>
              <label className="switch">
                <input
                  type="checkbox"
                  checked={reranker}
                  onChange={() => setReranker(!reranker)}
                />
                <span className="slider"></span>
              </label>
            </div>

            <div>
              <span style={{ display:"block", marginBottom:"4px", fontSize:"13px", fontWeight:"600" }}>
                Reranker Score ≥
              </span>
              <input
                type="text"
                value={rerankerScore}
                disabled={!reranker}
                onChange={(e) => setRerankerScore(e.target.value)}
                onBlur={(e) => normalizeScore(e.target.value)}
                style={!reranker ? { opacity:0.4, cursor:"not-allowed" } : {}}
              />
            </div>
          </div>

        </div>
      )}
    </div>
  );
}
