import React, { useState } from "react";

export default function ProductCard({ item }) {
  const { title_en, brand, price, currency, url, image_paths } = item;

  const images = image_paths || [];
  const [index, setIndex] = useState(0);

  const next = () => setIndex(prev => (prev + 1) % images.length);
  const prev = () => setIndex(prev => (prev - 1 + images.length) % images.length);
  const goTo = i => setIndex(i);

  return (
    <div style={styles.outerBox} className="fade-in scale-hover">
      <div style={styles.innerCard}>

        {/* IMAGE SLIDER */}
        <div style={styles.slider}>
          {images.length > 0 ? (
            <img src={images[index]} style={styles.image} alt="product" />
          ) : (
            <div style={styles.noImg}>No Image</div>
          )}

          {images.length > 1 && (
            <button style={{ ...styles.navBtn, left: "10px" }} onClick={prev}>❮</button>
          )}
          {images.length > 1 && (
            <button style={{ ...styles.navBtn, right: "10px" }} onClick={next}>❯</button>
          )}

          {/* Dot indicators */}
          <div style={styles.indicators}>
            {images.map((_, i) => (
              <span
                key={i}
                style={{ ...styles.dot, opacity: index === i ? 1 : 0.35 }}
                onClick={() => goTo(i)}
              />
            ))}
          </div>
        </div>

        {/* INFO */}
        <div style={styles.info}>
          <h3 style={styles.brand}>{brand}</h3>
          <p style={styles.title}>{title_en}</p>

          <p style={styles.price}>
            {price ? `${price} ${currency || ""}` : "-"}
          </p>

          <a href={url} target="_blank" rel="noopener noreferrer" style={styles.link}>
            View Product →
          </a>
        </div>

      </div>
    </div>
  );
}


const styles = {
  /** OUTER DARK PANEL BOX */
  outerBox: {
    padding: "12px",
    borderRadius: "24px",
    width: "100%",
    background: "linear-gradient(to bottom right, #0c090d, #272931)",
    border: "1px solid rgba(255,255,255,0.12)",
    boxShadow: "0 16px 42px rgba(0,0,0,0.32)",
    transition: "0.3s ease",
  },

  /** INNER LIGHT CARD */
  innerCard: {
    width: "100%",
    background: "#F4F5F7",
    borderRadius: "18px",
    padding: "16px",
    border: "1px solid rgba(0,0,0,0.1)",
    boxShadow: "0 8px 18px rgba(0,0,0,0.12)",
  },

  slider: {
    position: "relative",
    width: "100%",
    height: "200px",
    overflow: "hidden",
    borderRadius: "12px",
  },

  image: {
    width: "100%",
    height: "200px",
    objectFit: "cover",
    borderRadius: "12px",
  },

  noImg: {
    width: "100%",
    height: "200px",
    background: "#444",
    borderRadius: "12px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "white",
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
    transition: "0.2s",
  },

  indicators: {
    position: "absolute",
    bottom: "10px",
    left: "50%",
    transform: "translateX(-50%)",
    display: "flex",
    gap: "6px",
  },

  dot: {
    width: "9px",
    height: "9px",
    borderRadius: "50%",
    background: "#fff",
    cursor: "pointer",
    transition: "0.22s",
  },

  info: {
    marginTop: "14px",
  },

  brand: {
    fontWeight: "700",
    fontSize: "17px",
    marginBottom: "4px",
    color: "#0D1117",
  },

  title: {
    fontSize: "14px",
    opacity: 0.85,
    color: "#20232a",
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
