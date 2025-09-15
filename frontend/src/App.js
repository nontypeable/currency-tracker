import "./App.css";
import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";

function App() {
    const [rates, setRates] = useState({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [lastUpdated, setLastUpdated] = useState(null);
    const [baseCurrency, setBaseCurrency] = useState("USD");

    const fetchRates = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await axios.get(
                `http://localhost:8000/api/currency/rates/${baseCurrency}`,
                { timeout: 10000 },
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

    useEffect(() => {
        fetchRates();
        const interval = setInterval(fetchRates, 5 * 60 * 1000); // update data every 5 minutes
        return () => clearInterval(interval);
    }, [fetchRates]);

    return;
}

export default App;
