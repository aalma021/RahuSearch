import React from "react";
import "./../styles/theme.css";

export default function Filters({ min, max, setMin, setMax }) {
  return (
    <div
      className="glass fade-in"
      style={{
        padding: "20px",
        width: "240px",
        height: "fit-content"
      }}
    >
      <h3>Filters</h3>

      <label>Min Price</label>
      <input
        value={min}
        onChange={(e) => setMin(e.target.value)}
        type="number"
        style={inputStyle}
      />

      <label>Max Price</label>
      <input
        value={max}
        onChange={(e) => setMax(e.target.value)}
        type="number"
        style={inputStyle}
      />
    </div>
  );
}

const inputStyle = {
  width: "100%",
  padding: "10px 14px",
  marginBottom: "12px",
  borderRadius: "10px",
  border: "none",
  outline: "none",
  background: "rgba(255,255,255,0.12)",
  color: "#fff",
  fontSize: "15px"
};
