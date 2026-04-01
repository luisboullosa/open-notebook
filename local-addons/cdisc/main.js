function $(id){return document.getElementById(id)}

const langR = $('langR')
const langPy = $('langPy')
const generateBtn = $('generateBtn')
const statusBox = $('statusBox')
const resultBox = $('resultBox')

function setActiveLang(isR){
  if(isR){langR.classList.add('active'); langPy.classList.remove('active')} else {langPy.classList.add('active'); langR.classList.remove('active')}
}

langR.addEventListener('click',()=>setActiveLang(true))
langPy.addEventListener('click',()=>setActiveLang(false))

// Determine API base: prefer the Caddy host (no port 3005). If served directly
// from the frontend container (port 3005), route requests to the LAN API URL
// so the request goes through the reverse proxy which injects Authorization.
// API base: when served under /cdisc use that origin; when served on port 3005 (dev), route to Caddy host
const API_BASE = (location.pathname.startsWith('/cdisc')) ? location.origin + '/cdisc' : ((location.port === '3005') ? 'https://192.168.2.129/cdisc' : location.origin)

async function postJSON(url,body){
  const fullUrl = url.startsWith('http') ? url : `${API_BASE}${url.startsWith('/') ? '' : '/'}${url}`
  const res = await fetch(fullUrl,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
  if(!res.ok) throw new Error(await res.text())
  return res.json()
}

async function getJSON(url){
  const fullUrl = url.startsWith('http') ? url : `${API_BASE}${url.startsWith('/') ? '' : '/'}${url}`
  const res = await fetch(fullUrl)
  if(!res.ok) throw new Error(await res.text())
  return res.json()
}

generateBtn.addEventListener('click', async ()=>{
  try{
    generateBtn.disabled = true
    statusBox.style.display='block'
    statusBox.textContent = 'Submitting job…'

    const cfg = {
      projectName: $('projectName').value || 'STUDY001',
      description: $('description').value || '',
      language: langR.classList.contains('active') ? 'R' : 'py',
      nSubjects: Number($('nSubjects').value||50)
    }

    const resp = await postJSON('/api/ollama/generate', cfg)
    const jobId = resp.job_id
    statusBox.textContent = 'Job submitted: ' + jobId + '. Polling status...'

    // Poll
    let done=false
    while(!done){
      await new Promise(r=>setTimeout(r,2000))
      const st = await getJSON('/api/ollama/status/'+jobId)
      statusBox.textContent = 'Status: ' + (st.status || JSON.stringify(st))
      if(st.status === 'completed' || st.status === 'success' || st.status === 'finished'){
        done=true
        const dl = '/api/ollama/exports/'+jobId+'/download'
        resultBox.style.display='block'
        resultBox.innerHTML = `<a href="${dl}" style="color:#34d399;">↓ Download ZIP</a>`
        statusBox.textContent = 'Completed'
        break
      }
      if(st.status === 'failed' || st.status === 'error'){
        done=true
        statusBox.textContent = 'Job failed: ' + (st.error_message || JSON.stringify(st))
        break
      }
    }

  }catch(err){
    statusBox.style.display='block'
    statusBox.textContent = 'Error: '+String(err)
  }finally{generateBtn.disabled=false}
})
