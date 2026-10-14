import axios from 'axios';

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
});

export const getMatches = (competition = 'PL') =>
  API.get(`/matches?competition=${competition}`).then(r => r.data);

export const getPredictions = (competition = 'PL') =>
  API.get(`/predictions?competition=${competition}`).then(r => r.data);

export const getValueBets = (competition = 'PL', minEv = 0.05) =>
  API.get(`/value-bets?competition=${competition}&min_ev=${minEv}`).then(r => r.data);

export const trainModel = (competition = 'PL') =>
  API.post(`/model/train?competition=${competition}`).then(r => r.data);

export const getBetBetterPicks = (league = 'soccer/epl') =>
  API.get(`/betbetter/picks?league=${league}`).then(r => r.data);