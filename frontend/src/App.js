import "./App.css";
import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import CurrencyChart from "./CurrencyChart";

function App() {
  const [rates, setRates] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [baseCurrency, setBaseCurrency] = useState("USD");
  const [selectedCurrency, setSelectedCurrency] = useState(null);

  const handleRateClick = (currency) => {
    setSelectedCurrency(currency);
  };

  const closeChart = () => {
    setSelectedCurrency(null);
  };

  const fetchRates = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(
        `http://localhost:8000/api/currency/rates/${baseCurrency}`,
        { timeout: 10000 }
      );
      setRates(response.data.rates);
      setLastUpdated(new Date());
    } catch (error) {
      console.error("Error fetching rates:", error);
      setError("Failed to fetch exchange rates. Please try again later.");
    } finally {
      setLoading(false);
    }
  }, [baseCurrency]);

  const formatRate = (rate) => {
    if (rate >= 1000) {
      return rate.toFixed(2);
    } else if (rate >= 1) {
      return rate.toFixed(4);
    } else {
      return rate.toFixed(6);
    }
  };

  useEffect(() => {
    fetchRates();
    const interval = setInterval(fetchRates, 5 * 60 * 1000); // update data every 5 minutes
    return () => clearInterval(interval);
  }, [fetchRates]);

  return (
    <div className="App">
      <div className="section">
        <div className="header">
          <h1>💱 Currency Tracker</h1>
          <p>Real-time exchange rates</p>
        </div>

        <div className="currency-selector">
          <label htmlFor="base-currency">Base Currency:</label>
          <select
            id="base-currency"
            value={baseCurrency}
            onChange={(e) => setBaseCurrency(e.target.value)}
            disabled={loading}
          >
            <option value="USD">USD 🇺🇸</option>
            <option value="EUR">EUR 🇪🇺</option>
            <option value="RUB">RUB 🇷🇺</option>
          </select>
        </div>

        {error && (
          <div className="error">
            <p>{error}</p>
            <button onClick={fetchRates} style={{ marginTop: "10px" }}>
              Retry
            </button>
          </div>
        )}

        {loading ? (
          <div className="loading">
            <div className="spinner"></div>
            <p>Loading exchange rates...</p>
          </div>
        ) : (
          <>
            <div className="rates-grid">
              {Object.entries(rates)
                .sort(([a], [b]) => a.localeCompare(b))
                .map(([currency, rate]) => (
                  <div
                    key={currency}
                    className="rate-item"
                    onClick={() => handleRateClick(currency)}
                  >
                    <span className="currency-code">{currency}</span>
                    <span className="currency-rate">{formatRate(rate)}</span>
                  </div>
                ))}
            </div>

            {lastUpdated && (
              <div className="last-updated">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </div>
            )}
          </>
        )}
      </div>
      {selectedCurrency && (
        <CurrencyChart
          currency={selectedCurrency}
          baseCurrency={baseCurrency}
          onClose={closeChart}
        />
      )}
    </div>
  );
}

export default App;
