import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import axios from 'axios';

function CurrencyChart({ currency, baseCurrency, onClose }) {
    const [historicalData, setHistoricalData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        console.log("CurrencyChart mounted with", currency, baseCurrency);
        const fetchHistoricalData = async () => {
            console.log("Fetching historical data for", currency, baseCurrency);
            setLoading(true);
            setError(null);
            try {
                console.log("fetching data...");
                const response = await axios.get(
                    `http://localhost:8000/api/currency/historical/${currency}/${baseCurrency}/180`,
                    { timeout: 10000000 }
                );
                console.log("Data fetched:", response.data);
                setHistoricalData(response.data);
            } catch (err) {
                console.error("Error fetching historical data:", err);
                setError('Failed to load historical data');
            } finally {
                setLoading(false);
            }
        };
        fetchHistoricalData();
    }, [currency, baseCurrency]);

    if (loading) return <div>Loading chart...</div>;
    if (error) return <div>{error}</div>;

    return (
        <div style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', background: 'rgba(0,0,0,0.5)', zIndex: 1000 }}>
            <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', background: 'white', padding: '20px', borderRadius: '10px', width: '80%', maxWidth: '800px' }}>
                <button onClick={onClose} style={{ float: 'right' }}>Close</button>
                <h2>Historical Rates for {currency} (Base: {baseCurrency})</h2>
                <ResponsiveContainer width="100%" height={400}>
                    <LineChart data={historicalData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <Tooltip />
                        <Line type="monotone" dataKey="rate" stroke="#8884d8" />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}

export default CurrencyChart;
