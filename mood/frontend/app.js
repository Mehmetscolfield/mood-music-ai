const API_BASE = "http://127.0.0.1:5050";
let selectedFile = null;

document.getElementById("file").addEventListener("change", e=>{
  selectedFile = e.target.files[0] || null;
  const preview = document.getElementById("preview");
  preview.innerHTML = "";
  if(selectedFile){
    const img = document.createElement("img");
    img.src = URL.createObjectURL(selectedFile);
    preview.appendChild(img);
  }
});

document.getElementById("go").addEventListener("click", async ()=>{
  if(!selectedFile){ alert("Please select an image first."); return; }
  const fd = new FormData();
  fd.append("image", selectedFile);
  fd.append("language", document.getElementById("lang").value);

  document.getElementById("result").innerHTML = "Analyzing…";
  try{
    const r = await fetch(API_BASE + "/api/analyze",{ method:"POST", body: fd });
    const data = await r.json();
    if(!r.ok) throw new Error(data.error || "Server error");

    const { mood, language, tracks, embeds } = data;

    let html = `<h2 style="text-align:center;">Your mood: <b>${mood}</b> <span style="opacity:.7;">(${language})</span></h2>`;

    if (embeds && embeds.length){
      html += `<h3 style="margin-top:18px;">🎵 Popular Matches</h3>
               <div class="widgets">
                 ${embeds.slice(0,8).map(id => `
                   <iframe src="https://open.spotify.com/embed/track/${id}"
                           allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
                           loading="lazy"></iframe>
                 `).join("")}
               </div>`;
    } else {
      html += `<p style="opacity:.7;text-align:center;margin-top:12px;">No widgets available for this region right now.</p>`;
    }

    document.getElementById("result").innerHTML = html;

    // --- player logic ---
    const audio = document.getElementById("audio");
    if (audio && tracks && tracks.length){
      let current = -1;

      function fmt(s){ s = Math.floor(s||0); return `${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`; }

      function updateProgress(){
        if (current < 0) return;
        const dur = audio.duration || 30;
        const cur = audio.currentTime || 0;
        const pct = Math.min(100, Math.max(0, (cur / dur) * 100));
        const bar = document.getElementById(`seekbar-${current}`);
        const tcur = document.getElementById(`tcur-${current}`);
        const tmax = document.getElementById(`tmax-${current}`);
        if (bar) bar.style.width = pct + "%";
        if (tcur) tcur.textContent = fmt(cur);
        if (tmax) tmax.textContent = fmt(dur || 30);
      }

      function resetBars(){
        document.querySelectorAll(".seek__bar").forEach(b=> b.style.width = "0%");
        document.querySelectorAll("[id^='tcur-']").forEach(el=> el.textContent = "0:00");
      }

      function playIndex(i){
        if (!tracks[i] || !tracks[i].preview_url) return;
        current = i;
        audio.src = tracks[i].preview_url;
        resetBars();
        audio.play();
        updateButtons();
      }

      function updateButtons(){
        document.querySelectorAll(".play-btn").forEach(btn=>{
          const i = parseInt(btn.dataset.idx,10);
          if (!Number.isInteger(i)) return;
          if (i === current && !audio.paused) btn.textContent = "⏸";
          else btn.textContent = (tracks[i] && tracks[i].preview_url) ? "▶" : "⋯";
        });
      }

      document.getElementById("cards").addEventListener("click", (e)=>{
        const btn = e.target.closest(".play-btn");
        if(btn){
          const i = parseInt(btn.dataset.idx,10);
          if (i === current){ if (audio.paused) audio.play(); else audio.pause(); }
          else playIndex(i);
          updateButtons();
        }
        const seek = e.target.closest(".seek");
        if(seek){
          const i = parseInt(seek.dataset.idx,10);
          if (i === current){
            const rect = seek.getBoundingClientRect();
            const ratio = (e.clientX - rect.left) / rect.width;
            const dur = audio.duration || 30;
            audio.currentTime = Math.max(0, Math.min(dur, dur * ratio));
            updateProgress();
          }
        }
      });

      audio.addEventListener("timeupdate", updateProgress);
      audio.addEventListener("loadedmetadata", updateProgress);
      audio.addEventListener("seeked", updateProgress);
      audio.addEventListener("ended", ()=>{ if (current >= 0 && tracks.length) playIndex((current + 1) % tracks.length); });
      audio.addEventListener("play",  updateButtons);
      audio.addEventListener("pause", updateButtons);
    }
  }catch(err){
    document.getElementById("result").innerHTML = `<p style="color:#f77;">Error: ${err.message}</p>`;
    console.error(err);
  }
});
