(function(){
    const $ = (q, s = document) => s.querySelector(q);
    const fmt = (n) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(Number(n||0));

    function getEnv(key, fallback){ return fallback; }

    async function fetchMarket(symbol){
        try {
            const res = await fetch(`http://localhost:8080/api/quote?symbol=${encodeURIComponent(symbol)}`, { cache:'no-store' });
            if (!res.ok) throw new Error('Fetch error');
            return await res.json();
        } catch (e) {
            console.error('Market fetch error:', e);
            return { last:0, delta:0, close:[] };
        }
    }

    function renderMarket(symbol, data){
        const container = $('#market-cards');
        const card = document.createElement('div');
        card.className = 'card-mini';
        const dir = data.delta>=0 ? 'up':'down';
        card.innerHTML = `
            <h4>${symbol.toUpperCase()}</h4>
            <div class="price">${fmt(data.last)}</div>
            <div class="delta ${dir}">${data.delta>=0?'+':''}${data.delta.toFixed(2)}</div>
        `;
        container.appendChild(card);
    }

    function clearMarket(){ $('#market-cards').innerHTML=''; }

    function bindMarket(){
        $('#load-quote').addEventListener('click', async ()=>{
            const symbols = ($('#symbol').value||'MSFT').split(',').map(s=>s.trim()).slice(0,3);
            clearMarket();
            const results = await Promise.all(symbols.map(s=>fetchMarket(s).then(d=>({s,d}))));
            results.forEach(r=> renderMarket(r.s,r.d));

            // Chart.js rendering
            const ctx = document.getElementById('chartjs');
            const datasets = results.map((r,idx)=>({
                label: r.s.toUpperCase(),
                data: r.d.close.map((y,i)=>({x:i,y})),
                borderColor: ['#22d3ee','#10b981','#f59e0b'][idx%3],
                backgroundColor: 'transparent',
                tension:0.25
            }));
            if(window.__chart) window.__chart.destroy();
            window.__chart = new Chart(ctx,{type:'line',data:{datasets},options:{responsive:true,maintainAspectRatio:false,scales:{x:{display:false}}}});
        });
    }

    // Initialize all binds
    document.addEventListener('DOMContentLoaded', ()=>{
        const y = new Date().getFullYear();
        const yearNode = document.getElementById('year');
        if(yearNode) yearNode.textContent = y;

        bindMarket();
        // other binds like forms, chat, etc. remain untouched
    });

})(); 