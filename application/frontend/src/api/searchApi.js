import axios from "axios";
import { API_URL } from "../config";

export const searchApi = async ({
  text,
  imageFile,
  mode,
  k,
  alpha,
  reranker,
  rerankerScore,
  store
}) => {
  const formData = new FormData();

  if (text) formData.append("text", text);
  if (imageFile) formData.append("image", imageFile);

  formData.append("mode", mode);         
  formData.append("k", String(k));               
  formData.append("alpha", String(alpha));       
  formData.append("reranker", String(reranker)); 
  formData.append("reranker_score", String(rerankerScore));

  if (store) formData.append("store", store);

  const res = await axios.post(API_URL, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
      "X-Pinggy-No-Screen": "true"
    }
  });

  return res.data;
};
