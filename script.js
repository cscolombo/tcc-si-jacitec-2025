(function(){
  const $ = (sel, el=document) => el.querySelector(sel);

  const state = { date: null, q: '' };

  function normalize(str){ return (str || '').toLowerCase().normalize('NFD').replace(/\p{Diacritic}/gu,''); }

  function renderStats(list){
    $('#totalCount').textContent = list.length.toString();
    if(list.length){
      const times = list.map(x=>x.hora).filter(Boolean).sort();
      $('#timeSpan').textContent = `${times[0]} – ${times[times.length-1]}`;
      const advisors = new Set(list.map(x=>x.orientador).filter(Boolean));
      $('#advisorCount').textContent = advisors.size.toString();
    }else{
      $('#timeSpan').textContent = '—';
      $('#advisorCount').textContent = '0';
    }
    $('#generatedAt').textContent = (window.TCC_DATA?.gerado_em || '—');
  }

  function renderCards(list){
    const cont = $('#scheduleContainer');
    cont.innerHTML = '';
    if(!list.length){
      $('#emptyState').classList.remove('hide');
      return;
    }
    $('#emptyState').classList.add('hide');
    const frag = document.createDocumentFragment();
    list.forEach(item => {
      const card = document.createElement('article');
      card.className = 'session';
      card.innerHTML = `
        <div class="time">
          <div>${item.hora || '—:—'}</div>
          <div class="badge">${state.date}</div>
        </div>
        <div class="details">
          <h3 class="title">${item.titulo || 'Título não informado'}</h3>
          <div class="meta">
            <span><strong>Aluno(a):</strong> ${item.aluno || '—'}</span>
            <span><strong>Orientador(a):</strong> ${item.orientador || '—'}</span>
            <span><strong>Banca:</strong> ${[item.revisor1,item.revisor2].filter(Boolean).join(' &middot; ') || '—'}</span>
          </div>
          ${ (item.media_total ?? item.nota_orientador ?? item.nota_revisor1 ?? item.nota_revisor2) !== undefined ? `
          <div class="meta" style="margin-top:.35rem">
            <span><strong>Média:</strong> ${item.media_total ?? '—'}</span>
            <span><strong>Notas:</strong> O ${item.nota_orientador ?? '—'} · R1 ${item.nota_revisor1 ?? '—'} · R2 ${item.nota_revisor2 ?? '—'}</span>
          </div>` : ''}
        </div>
      `;
      frag.appendChild(card);
    });
    cont.appendChild(frag);
  }

  function currentList(){
    const raw = window.TCC_DATA?.datas?.[state.date] || [];
    const q = normalize(state.q);
    if(!q) return raw;
    return raw.filter(it => {
      const hay = [it.aluno, it.titulo, it.orientador, it.revisor1, it.revisor2].map(normalize).join(' ');
      return hay.includes(q);
    });
  }

  function update(){
    // hydrate date options
    const sel = $('#dateFilter');
    if(!state.date){
      const dates = Object.keys(window.TCC_DATA?.datas || {}).sort((a,b)=>{
        const [da,ma,ya] = a.split('/').map(Number);
        const [db,mb,yb] = b.split('/').map(Number);
        return new Date(ya,ma-1,da) - new Date(yb,mb-1,db);
      });
      sel.innerHTML = dates.map(d => `<option value="${d}">${d}</option>`).join('');
      state.date = dates[0] || null;
      sel.value = state.date;
    }
    const list = currentList();
    renderStats(list);
    renderCards(list);
  }

  function initControls(){
    $('#dateFilter').addEventListener('change', () => {
      state.date = $('#dateFilter').value;
      update();
    });
    $('#searchBox').addEventListener('input', (e) => {
      state.q = e.target.value;
      update();
    });
    $('#exportPdfBtn').addEventListener('click', async () => {
      const { jsPDF } = window.jspdf;
      const container = document.querySelector('main');
      const canvas = await html2canvas(container, { scale: 2, useCORS: true, backgroundColor: '#ffffff' });
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'pt', 'a4');
      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();
      const imgWidth = pageWidth - 40;
      const imgHeight = canvas.height * imgWidth / canvas.width;

      if (imgHeight <= pageHeight - 40) {
        pdf.addImage(imgData, 'PNG', 20, 20, imgWidth, imgHeight);
      } else {
        let position = 0;
        while (position < canvas.height) {
          const pageCanvas = document.createElement('canvas');
          const pageCtx = pageCanvas.getContext('2d');
          const ratio = imgWidth / canvas.width;
          pageCanvas.width = imgWidth;
          pageCanvas.height = pageHeight - 40;
          const sliceHeight = pageCanvas.height / ratio;
          pageCtx.drawImage(canvas, 0, position, canvas.width, sliceHeight, 0, 0, pageCanvas.width, pageCanvas.height);
          const pageImg = pageCanvas.toDataURL('image/png');
          pdf.addImage(pageImg, 'PNG', 20, 20, imgWidth, pageCanvas.height);
          position += sliceHeight;
          if (position < canvas.height) pdf.addPage();
        }
      }
      const dateSlug = (state.date || 'tcc').replace(/\//g,'-');
      pdf.save(`programacao_tcc_${dateSlug}.pdf`);
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    initControls();
    update();
  });
})();