const form = document.getElementById('uploadForm');
const progress = document.getElementById('progress');
const results = document.getElementById('results');
const summaryDiv = document.getElementById('summary');
const linksDiv = document.getElementById('links');
const procVideo = document.getElementById('procVideo');
const submitBtn = document.getElementById('submitBtn');

form.addEventListener('submit', (e) => {
  e.preventDefault();
  const fileInput = document.getElementById('fileInput');
  if (!fileInput.files || fileInput.files.length === 0) {
    alert("Selecione um arquivo primeiro.");
    return;
  }
  submitBtn.disabled = true;
  progress.classList.remove('hidden');
  results.classList.add('hidden');
  summaryDiv.innerHTML = '';
  linksDiv.innerHTML = '';
  procVideo.src = '';

  const fd = new FormData();
  fd.append('file', fileInput.files[0]);
  fd.append('microns_per_pixel', document.getElementById('microns').value);
  fd.append('fps', document.getElementById('fps').value);
  fd.append('drop_volume_ul', document.getElementById('volume').value);
  fd.append('conf', document.getElementById('conf').value);

  const xhr = new XMLHttpRequest();
  xhr.open('POST', '/analyze', true);

  xhr.onreadystatechange = function(){
    if (xhr.readyState === 4) {
      progress.classList.add('hidden');
      submitBtn.disabled = false;
      if (xhr.status === 200) {
        const resp = JSON.parse(xhr.responseText);
        if (resp.status === 'done') {
          results.classList.remove('hidden');
          summaryDiv.innerHTML = `<pre>${JSON.stringify(resp.summary, null, 2)}</pre>`;
          if (resp.processed_video) {
            procVideo.src = resp.processed_video;
          }
          linksDiv.innerHTML = '';
          if (resp.report_json) linksDiv.innerHTML += `<a href="${resp.report_json}" target="_blank">JSON do Relatório</a>`;
          if (resp.report_md) linksDiv.innerHTML += `<a href="${resp.report_md}" target="_blank">Relatório (Markdown)</a>`;
          if (resp.histogram) linksDiv.innerHTML += `<a href="${resp.histogram}" target="_blank">Histograma</a>`;
        } else {
          alert("Resposta inesperada: " + JSON.stringify(resp));
        }
      } else {
        let msg = "Erro no servidor.";
        try { msg = JSON.parse(xhr.responseText).error || xhr.responseText } catch(e){}
        alert("Erro: " + msg);
      }
    }
  };

  xhr.send(fd);
});