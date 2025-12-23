import React, { useState, useEffect } from "react";
import { API_BASE } from "../config";

export default function ProductCard({ item }) {
  const { title_en, brand, price, currency, url, image_paths } = item;

  const images = image_paths || [];
  const [index, setIndex] = useState(0);

  useEffect(() => {
    setIndex(0);
  }, [images]);

  const next = () => setIndex((prev) => (prev + 1) % images.length);
  const prev = () => setIndex((prev) => (prev - 1 + images.length) % images.length);
  const goTo = (i) => setIndex(i);

  return (
    <div style={styles.card} className="fade-in scale-hover">
      {/* IMAGE SLIDER */}
      <div style={styles.slider}>
        {images.length > 0 ? (
        <img
          src={`${API_BASE}${images[index]}`}
          style={styles.image}
          alt="product"
        />
        ) : (
          <div style={styles.noImg}>No Image</div>
        )}

        {images.length > 1 && (
          <>
            <button style={{ ...styles.navBtn, left: "10px" }} onClick={prev}>
              ❮
            </button>
            <button style={{ ...styles.navBtn, right: "10px" }} onClick={next}>
              ❯
            </button>
          </>
        )}

        {images.length > 1 && (
          <div style={styles.indicators}>
            {images.map((_, i) => (
              <span
                key={i}
                style={{ ...styles.dot, opacity: index === i ? 1 : 0.35 }}
                onClick={() => goTo(i)}
              />
            ))}
          </div>
        )}
      </div>

      {/* INFO */}
      <div style={styles.info}>
        <div>
          <h3 style={styles.brand}>{brand}</h3>
          <p style={styles.title}>{title_en}</p>
        </div>

        <div>
          <p style={styles.price}>
            {price ? `${price} ${currency || ""}` : "-"}
          </p>

          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            style={styles.link}
          >
            View Product →
          </a>
        </div>
      </div>
    </div>
  );
}
const styles = {
  card: {
    margin: "12px",
    padding: "16px",
    width: "100%",
    height: "460px",
    borderRadius: "18px",
    background: "#FFFFFF",
    border: "1px solid rgba(0,0,0,0.08)",
    boxShadow: "0 10px 28px rgba(0,0,0,0.14)",
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
    transition: "0.25s ease",
  },

  slider: {
    position: "relative",
    width: "100%",
    height: "200px",
    overflow: "hidden",
    borderRadius: "12px",
    background: "#F0F1F3",
  },

  image: {
    width: "100%",
    height: "200px",
    objectFit: "contain",
  },

  noImg: {
    width: "100%",
    height: "200px",
    background: "#E2E3E6",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "#555",
  },

  navBtn: {
    position: "absolute",
    top: "50%",
    transform: "translateY(-50%)",
    background: "rgba(0,0,0,0.45)",
    border: "none",
    color: "#fff",
    padding: "6px 10px",
    fontSize: "18px",
    borderRadius: "50%",
    cursor: "pointer",
  },

  indicators: {
    position: "absolute",
    bottom: "10px",
    left: "50%",
    transform: "translateX(-50%)",
    display: "flex",
    gap: "12px",
  },

  dot: {
    width: "8px",
    height: "8px",
    borderRadius: "50%",
    background: "#fff",
    cursor: "pointer",
  },

  info: {
    height: "200px",
    marginTop: "14px",
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
  },

  brand: {
    fontWeight: "700",
    fontSize: "16px",
    marginBottom: "4px",
    color: "#0D1117",
  },

  title: {
    fontSize: "14px",
    color: "#20232a",
    lineHeight: "1.4",
    opacity: 0.85,
    display: "-webkit-box",
    WebkitLineClamp: 2,
    WebkitBoxOrient: "vertical",
    overflow: "hidden",
  },

  price: {
    fontWeight: "700",
    marginTop: "10px",
    fontSize: "17px",
    color: "#111",
  },

  link: {
    marginTop: "12px",
    display: "block",
    textDecoration: "none",
    color: "#FC6736",
    fontWeight: "bold",
  },
};
