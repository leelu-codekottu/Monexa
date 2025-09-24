const express = require('express');
const cors = require('cors');
const axios = require('axios');
const dotenv = require('dotenv');

dotenv.config();

const app = express();
app.use(cors()); // enable CORS for all origins
app.use(express.json());

// Import routes
const healthRoute = require('./routes/health');
const financeRoute = require('./routes/finance');
const chatbotRoute = require('./routes/chatbot');

app.use('/health', healthRoute);
app.use('/finance', financeRoute);
app.use('/chatbot', chatbotRoute);

// /api/quote route using Alpha Vantage with Yahoo Finance fallback
app.get('/api/quote', async (req, res) => {
	const symbolParam = req.query.symbol;
	if (!symbolParam || !String(symbolParam).trim()) {
		return res.status(400).json({ error: 'Symbol required' });
	}

	const alphaVantageKey = process.env.ALPHA_VANTAGE_KEY;

	async function fetchFromAlphaVantage(symbol) {
		if (!alphaVantageKey) throw new Error('ALPHA_VANTAGE_KEY not provided');
		const url = `https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=${encodeURIComponent(symbol)}&interval=5min&apikey=${alphaVantageKey}`;
		const response = await axios.get(url, { timeout: 15000 });
		const data = response.data;
		const series = data && data['Time Series (5min)'];
		if (!series) throw new Error('Alpha Vantage response missing series');
		const timesAsc = Object.keys(series).sort();
		const closePrices = timesAsc.map((t) => parseFloat(series[t]['4. close'])).filter((n) => Number.isFinite(n));
		if (!closePrices.length) throw new Error('Alpha Vantage no prices');
		const last = closePrices[closePrices.length - 1] || 0;
		const delta = last - (closePrices[0] || 0);
		return { symbol: symbol.toUpperCase(), last, delta, close: closePrices };
	}

	async function fetchFromYahoo(symbol) {
		const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?interval=5m&range=1d`;
		const response = await axios.get(url, { timeout: 15000 });
		const root = response.data && response.data.chart && response.data.chart.result && response.data.chart.result[0];
		if (!root) throw new Error('Yahoo Finance response missing result');
		let closePrices = (root.indicators && root.indicators.quote && root.indicators.quote[0] && root.indicators.quote[0].close) || [];
		closePrices = (closePrices || []).filter((n) => Number.isFinite(n));
		if (!closePrices.length) throw new Error('Yahoo Finance no prices');
		const last = closePrices[closePrices.length - 1] || 0;
		const delta = last - (closePrices[0] || 0);
		return { symbol: symbol.toUpperCase(), last, delta, close: closePrices };
	}

	async function fetchForSymbol(symbol) {
		try {
			return await fetchFromAlphaVantage(symbol);
		} catch (e) {
			try {
				return await fetchFromYahoo(symbol);
			} catch (e2) {
				return { symbol: symbol.toUpperCase(), last: 0, delta: 0, close: [] };
			}
		}
	}

	try {
		const symbols = String(symbolParam)
			.split(',')
			.map((s) => s.trim())
			.filter((s) => s.length > 0);

		if (symbols.length === 0) {
			return res.status(400).json({ error: 'Symbol required' });
		}

		// Fetch all symbols in parallel
		const results = await Promise.all(symbols.map((s) => fetchForSymbol(s)));

		// Backward compatibility: if a single symbol was requested, return a single object
		if (symbols.length === 1) {
			return res.json(results[0]);
		}

		return res.json(results);
	} catch (err) {
		console.error('Stock fetch error:', err && err.message ? err.message : err);
		return res.status(500).json({ error: 'Internal Server Error' });
	}
});

// Start server
const PORT = process.env.PORT || 8080;
app.listen(PORT, () => console.log(`Monexa backend listening on http://localhost:${PORT}`));
