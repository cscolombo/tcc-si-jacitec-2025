// Patch: pretty-print date labels if they look like filenames (e.g., 22_10_2025.csv)
(function(){
  const pretty = (label) => {
    const m = String(label||'').match(/^(\d{1,2})_(\d{1,2})_(\d{4})(?:\.csv)?$/i);
    if(m){ return `${m[1].padStart(2,'0')}/${m[2].padStart(2,'0')}/${m[3]}`; }
    return label;
  };
  const sel = document.querySelector('#dateFilter');
  if(!sel) return;
  const options = Array.from(sel.querySelectorAll('option'));
  options.forEach(opt => { opt.textContent = pretty(opt.textContent); });
})();