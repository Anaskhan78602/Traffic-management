import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:8000",
});

export const getMetrics = () => API.get("/metrics");

export const startSimulation = (mode) =>
  API.post("/start-simulation", { mode });