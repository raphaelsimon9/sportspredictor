import React, { useState, useEffect } from 'react';
import { getValueBets, getPredictions, trainModel, getBetBetterPicks } from './api';
import './index.css';

function App() {
  const [competition, setCompetition] = useState('PL');
  const [valueBets, setValueBets] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [activeTab, setActiveTab] = useState('bets');

  const loadData = async () => {
    setLoading(true);
    setMessage('');
    try {
      const bets = await getValueBets(competition);
      setValueBets(bets);
      const preds = await getPredictions(competition);
      setPredictions(preds);
    } catch (e) {
      setMessage('Error loading data. Model may need training first.');
    }
    setLoading(false);
  };

  const handleTrain = async () => {
    setLoading(true);
    setMessage('Training model on historical data...');
    try {
      const res = await trainModel(competition);
      setMessage(`Model trained on ${res.matches_used} matches. ${res.teams_learned} teams learned.`);
    } catch (e) {
      setMessage('Training failed. Check API keys and try again.');
    }
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, [competition]);

  return (
    <div className="app">
      <header>
        <h1>BetEdge</h1>
        <p className="subtitle">Statistical value bet finder</p>
      </header>

      <div className="controls">
        <select value={competition} onChange={e => setCompetition(e.target.value)}>
          <option value="PL">Premier League</option>
          <option value="BL1">Bundesliga</option>
          <option value="SA">Serie A</option>
          <option value="PD">La Liga</option>
          <option value="FL1">Ligue 1</option>
        </select>
        <button onClick={handleTrain} disabled={loading}>
          {loading ? 'Working...' : 'Train Model'}
        </button>
        <button onClick={loadData} disabled={loading}>Refresh</button>
      </div>

      {message && <div className="message">{message}</div>}

      <nav className="tabs">
        <button className={activeTab === 'bets' ? 'active' : ''}
                onClick={() => setActiveTab('bets')}>
          Value Bets ({valueBets.length})
        </button>
        <button className={activeTab === 'predictions' ? 'active' : ''}
                onClick={() => setActiveTab('predictions')}>
          Predictions ({predictions.length})
        </button>
      </nav>

      {activeTab === 'bets' && (
        <div className="bet-list">
          {valueBets.length === 0 && !loading && (
            <p className="empty">No value bets found. Try training the model first, or lower the EV threshold.</p>
          )}
          {valueBets.map((bet, i) => (
            <div key={i} className="bet-card">
              <div className="bet-header">
                <span className="match">{bet.match_label}</span>
                <span className={`confidence ${bet.confidence.toLowerCase()}`}>
                  {bet.confidence}
                </span>
              </div>
              <div className="bet-details">
                <div className="selection">
                  <strong>{bet.selection}</strong> @ {bet.bookmaker}
                </div>
                <div className="odds">{bet.bookmaker_odds.toFixed(2)}</div>
              </div>
              <div className="bet-stats">
                <span>Model: {(bet.model_probability * 100).toFixed(1)}%</span>
                <span>Implied: {(bet.implied_probability * 100).toFixed(1)}%</span>
                <span className="ev">EV: +{(bet.expected_value * 100).toFixed(1)}%</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'predictions' && (
        <div className="prediction-list">
          {predictions.map((p, i) => (
            <div key={i} className="pred-card">
              <div className="pred-teams">{p.match_id}</div>
              <div className="pred-bars">
                <div className="bar-row">
                  <span>Home</span>
                  <div className="bar"><div className="fill" style={{width: `${p.home_win_prob*100}%`}} /></div>
                  <span>{(p.home_win_prob*100).toFixed(0)}%</span>
                </div>
                <div className="bar-row">
                  <span>Draw</span>
                  <div className="bar"><div className="fill draw" style={{width: `${p.draw_prob*100}%`}} /></div>
                  <span>{(p.draw_prob*100).toFixed(0)}%</span>
                </div>
                <div className="bar-row">
                  <span>Away</span>
                  <div className="bar"><div className="fill away" style={{width: `${p.away_win_prob*100}%`}} /></div>
                  <span>{(p.away_win_prob*100).toFixed(0)}%</span>
                </div>
              </div>
              <div className="pred-xg">
                xG: {p.predicted_home_goals} - {p.predicted_away_goals}
              </div>
            </div>
          ))}
        </div>
      )}

      <footer>
        <p>For research only. Not betting advice. Gamble responsibly.</p>
      </footer>
    </div>
  );
}

export default App;