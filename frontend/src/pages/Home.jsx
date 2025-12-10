import React, { useState, useEffect } from "react";
import ProductCard from "../components/ProductCard";
import Loading from "../components/Loading";
import SearchBar from "../components/SearchBar";
import { searchApi } from "../api/searchApi";

export default function Home() {
  const [text, setText] = useState("");
  const [imageFile, setImageFile] = useState(null);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const [min, setMin] = useState("");
  const [max, setMax] = useState("");

  const [mode, setMode] = useState("keyword");
  const [k, setK] = useState(40);
  const [alpha, setAlpha] = useState(0.5);
  const [reranker, setReranker] = useState(true);
  const [rerankerScore, setRerankerScore] = useState(0.0);

  const [store, setStore] = useState("");

  const [page, setPage] = useState(1);
  const pageSize = 12;

  const onSearch = async () => {
    setLoading(true);

    const data = await searchApi({
      text,
      imageFile,
      mode,
      k,
      alpha,
      reranker,
      rerankerScore,
      store
    });

    setResults(data.results || []);
    setLoading(false);
    setPage(1);
  };

  const filteredResults = results.filter((r) => {
    const val = r.price || 0;
    const minOk = !min || val >= parseFloat(min);
    const maxOk = !max || val <= parseFloat(max);
    return minOk && maxOk;
  });

  const paginatedResults = filteredResults.slice(
    (page - 1) * pageSize,
    page * pageSize
  );

  const totalPages = Math.ceil(filteredResults.length / pageSize) || 1;

  useEffect(() => {
    setPage(1);
  }, [min, max]);

  const shouldShowResults = results.length > 0 || loading;

  return (
    <div className="page-root">
      <div className="hero-wrapper fade-in">
        <div className="hero-card">
          <h1 className="hero-title" style={{ fontSize: "45px" }}>
            بحث دلالي
          </h1>
        </div>
      </div>

      <SearchBar
        text={text}
        setText={setText}
        onSearch={onSearch}
        onImageUpload={setImageFile}
        mode={mode}
        setMode={setMode}
        k={k}
        setK={setK}
        alpha={alpha}
        setAlpha={setAlpha}
        reranker={reranker}
        setReranker={setReranker}
        rerankerScore={rerankerScore}
        setRerankerScore={setRerankerScore}
        imageFile={imageFile}
        setImageFile={setImageFile}
        min={min}
        max={max}
        setMin={setMin}
        setMax={setMax}
        store={store}
        setStore={setStore}
      />

      {shouldShowResults && (
        <div className="results-container fade-in">

          <div className="results-grid">
            {loading ? (
              <Loading />
            ) : filteredResults.length === 0 ? (
              <div style={{ gridColumn: "1 / -1", textAlign: "center", padding: "20px 0" }}>
                No products found.
              </div>
            ) : (
              paginatedResults.map((item) => (
                <ProductCard key={item.id} item={item} />
              ))
            )}
          </div>

          {!loading && filteredResults.length > 0 && (
            <div className="pagination">
              <button className="pg-btn" disabled={page === 1} onClick={() => setPage(page - 1)}>
                Prev
              </button>

              <span className="pg-label">
                Page {page} / {totalPages}
              </span>

              <button className="pg-btn" disabled={page === totalPages} onClick={() => setPage(page + 1)}>
                Next
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
