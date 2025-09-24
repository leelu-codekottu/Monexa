const express = require('express');
const axios = require('axios');
require('dotenv').config();

const router = express.Router();

// Utility to determine if Indian or International stock
function isIndianStock(symbol) {
  return symbol.toUpperCase().endsWith('.NS');
}

// Fetch live stock data from finance APIs
async function getStockData(symbol) {
  try {
    if (isIndianStock(symbol)) {
      // Yahoo Finance
      const res = await axios.get(
        `https://${process.env.YAHOO_FINANCE_HOST}/stock/v2/get-summary`,
        {
          params: { symbol },
          headers: {
            'X-RapidAPI-Key': process.env.YAHOO_FINANCE_KEY,
            'X-RapidAPI-Host': process.env.YAHOO_FINANCE_HOST
          }
        }
      );
      const data = res.data;
      return {
        symbol,
        price: data.price?.regularMarketPrice?.raw || 0,
        previousClose: data.summaryDetail?.previousClose?.raw || 0
      };
    } else {
      // Alpha Vantage
      const res = await axios.get('https://www.alphavantage.co/query', {
        params: {
          function: 'GLOBAL_QUOTE',
          symbol,
          apikey: process.env.ALPHA_VANTAGE_KEY
        }
      });
      const data = res.data['Global Quote'] || {};
      return {
        symbol,
        price: parseFloat(data['05. price']) || 0,
        previousClose: parseFloat(data['08. previous close']) || 0
      };
    }
  } catch (err) {
    console.error('Finance API error:', err.message);
    return { symbol, price: 0, previousClose: 0 };
  }
}

// POST /chatbot/chat
router.post('/chat', async (req, res) => {
  const { query, symbols } = req.body || {};
  if (!query) return res.status(400).json({ error: 'query required' });

  try {
    // 1️⃣ Fetch stock data for context
    let context = '';
    if (Array.isArray(symbols) && symbols.length > 0) {
      const rows = [];
      for (const s of symbols) {
        const stock = await getStockData(s);
        rows.push(`${s.toUpperCase()}: price=${stock.price}, previousClose=${stock.previousClose}`);
      }
      context = rows.join('\n');
    }

    // 2️⃣ Call OpenAI
    const aiResp = await axios.post(
      'https://api.openai.com/v1/chat/completions',
      {
        model: 'gpt-3.5-turbo',
        messages: [
          { role: 'system', content: 'You are Monexa, a friendly and clear financial assistant. Include relevant stock data in your answers concisely.' },
          ...(context ? [{ role: 'assistant', content: `Stock Data:\n${context}` }] : []),
          { role: 'user', content: query }
        ],
        max_tokens: 600
      },
      {
        headers: { Authorization: `Bearer ${process.env.OPENAI_API_KEY}` }
      }
    );

    const answer = aiResp.data.choices?.[0]?.message?.content || 'No answer from model';
    res.json({ answer, context });

  } catch (err) {
    console.error('Chat error', err.response?.data || err.message);
    res.status(500).json({ error: 'Chat failed', detail: err.response?.data || err.message });
  }
});

module.exports = router;
