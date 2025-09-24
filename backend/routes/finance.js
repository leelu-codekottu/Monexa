const express = require('express');
const axios = require('axios');
require('dotenv').config();

const router = express.Router();

// Utility function to check if symbol is Indian (e.g., ends with .NS)
function isIndianStock(symbol) {
  return symbol.toUpperCase().endsWith('.NS');
}

// GET /finance/summary?symbol=XXX
router.get('/summary', async (req, res) => {
  const symbol = req.query.symbol;
  if (!symbol) return res.status(400).json({ error: 'symbol query param required' });

  try {
    if (isIndianStock(symbol)) {
      // Yahoo Finance for Indian stocks
      const response = await axios.get(
        `https://${process.env.YAHOO_FINANCE_HOST}/stock/v2/get-summary`,
        {
          params: { symbol },
          headers: {
            'X-RapidAPI-Key': process.env.YAHOO_FINANCE_KEY,
            'X-RapidAPI-Host': process.env.YAHOO_FINANCE_HOST
          }
        }
      );

      const data = response.data;
      const summary = {
        source: 'Yahoo Finance (India)',
        symbol,
        price: data.price?.regularMarketPrice?.raw || 0,
        previousClose: data.summaryDetail?.previousClose?.raw || 0,
        dayHigh: data.summaryDetail?.dayHigh?.raw || 0,
        dayLow: data.summaryDetail?.dayLow?.raw || 0
      };
      return res.json(summary);

    } else {
      // Alpha Vantage for international stocks
      const response = await axios.get(
        'https://www.alphavantage.co/query',
        {
          params: {
            function: 'GLOBAL_QUOTE',
            symbol,
            apikey: process.env.ALPHA_VANTAGE_KEY
          }
        }
      );

      const data = response.data['Global Quote'] || {};
      const summary = {
        source: 'Alpha Vantage (International)',
        symbol,
        price: parseFloat(data['05. price']) || 0,
        previousClose: parseFloat(data['08. previous close']) || 0,
        dayHigh: parseFloat(data['03. high']) || 0,
        dayLow: parseFloat(data['04. low']) || 0
      };
      return res.json(summary);
    }

  } catch (err) {
    console.error('Finance API error:', err.response?.data || err.message);
    return res.status(500).json({ error: 'Failed to fetch finance data' });
  }
});

module.exports = router;
