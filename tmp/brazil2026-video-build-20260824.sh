#!/usr/bin/env bash
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive
export npm_config_loglevel=warn
export PIP_DISABLE_PIP_VERSION_CHECK=1
WORK=/work/brazil2026
rm -rf "$WORK"
mkdir -p "$WORK"/{raw,processed,audio,hf-project,remotion/public/assets,remotion/src,out}

echo "=== INSTALL SYSTEM ==="
apt-get update -qq
apt-get install -y -qq curl ca-certificates gnupg ffmpeg python3 python3-pip python3-venv espeak-ng zip unzip \
  fonts-dejavu-core libnss3 libxss1 libasound2 libatk-bridge2.0-0 libgtk-3-0 libgbm1 libxshmfence1 \
  libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libxfixes3 >/dev/null
curl -fsSL https://deb.nodesource.com/setup_22.x | bash - >/dev/null
apt-get install -y -qq nodejs >/dev/null
node -v
npm -v
ffmpeg -version | head -1

echo "=== INSTALL PYTHON DEPS ==="
python3 -m pip install --break-system-packages -q "yt-dlp[default,curl-cffi]" kokoro soundfile numpy requests

echo "=== DOWNLOAD STOCK FOOTAGE ==="
python3 - <<'PY'
import subprocess, pathlib
raw=pathlib.Path('/work/brazil2026/raw')
assets={
 'city':'https://pixabay.com/videos/city-of-brazil-brazil-city-336095/',
 'woman':'https://pixabay.com/videos/woman-phone-street-urban-person-129410/',
 'phone':'https://pixabay.com/videos/smartphone-social-media-whatsapp-356885/',
 'datacenter':'https://pixabay.com/videos/data-center-server-information-262726/',
}
for name,url in assets.items():
    tmpl=str(raw/f'{name}.%(ext)s')
    cmd=['yt-dlp','--impersonate','chrome','--no-playlist','-f','best','--merge-output-format','mp4','-o',tmpl,url]
    print('DOWNLOAD',name,url,flush=True)
    subprocess.run(cmd,check=True)
    files=[p for p in raw.glob(f'{name}.*') if p.suffix.lower() in {'.mp4','.mov','.webm','.mkv'}]
    if not files:
        raise RuntimeError(f'No media for {name}')
    src=max(files,key=lambda p:p.stat().st_size)
    dst=raw/f'{name}.mp4'
    if src!=dst:
        src.rename(dst)
    print(name,dst.stat().st_size,flush=True)
PY

echo "=== PREPROCESS FOOTAGE ==="
ffmpeg -y -stream_loop -1 -i "$WORK/raw/city.mp4" -t 60 \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,eq=contrast=1.07:saturation=0.82:brightness=-0.05,format=yuv420p" \
  -an -c:v libx264 -preset fast -crf 19 -movflags +faststart "$WORK/processed/city.mp4" >/dev/null 2>&1
ffmpeg -y -stream_loop -1 -i "$WORK/raw/woman.mp4" -t 18 \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,eq=contrast=1.06:saturation=0.78:brightness=-0.035,format=yuv420p" \
  -an -c:v libx264 -preset fast -crf 18 -movflags +faststart "$WORK/processed/woman.mp4" >/dev/null 2>&1
ffmpeg -y -stream_loop -1 -i "$WORK/raw/phone.mp4" -t 12 \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,eq=contrast=1.08:saturation=0.74:brightness=-0.05,format=yuv420p" \
  -an -c:v libx264 -preset fast -crf 18 -movflags +faststart "$WORK/processed/phone.mp4" >/dev/null 2>&1
ffmpeg -y -stream_loop -1 -i "$WORK/raw/datacenter.mp4" -t 25 \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,eq=contrast=1.14:saturation=0.58:brightness=-0.12,format=yuv420p" \
  -an -c:v libx264 -preset fast -crf 19 -movflags +faststart "$WORK/processed/datacenter.mp4" >/dev/null 2>&1

echo "=== GENERATE NEURAL PORTUGUESE NARRATION ==="
cat > "$WORK/audio/tts.py" <<'PY'
import subprocess, pathlib, numpy as np, soundfile as sf
from kokoro import KPipeline
work=pathlib.Path('/work/brazil2026/audio')
scene_durations=[4.8,8.2,7.0,8.0,9.0,6.0,9.0,7.4]
texts=[
"Faltam vinte e quatro horas para a votação.",
"Ana, quarenta e dois anos, auxiliar de enfermagem no Recife, abre o grupo de WhatsApp das mães do bairro.",
"Chega um áudio. Parece a voz de um candidato do PT. Mas é falso.",
"Foi feito para ela: conhece seus medos, sua rotina e o que poderia fazê-la desistir. Ana decide não votar.",
"Agora repita isso cem mil vezes: cada mensagem adaptada, cada pessoa escolhida por uma inteligência artificial agêntica, na véspera da eleição.",
"Não é preciso hackear a urna. Basta deslocar vontades suficientes para influenciar uma disputa apertada.",
"Nossa pesquisa separa três perguntas: o que a inteligência artificial consegue fazer; como isso chega a escala; e que efeito real produz no voto.",
"É o C D E gap. Entendê-lo cedo ajuda a detectar, limitar e mitigar. A urna pode ficar intacta. A vontade, não."
]
pipe=KPipeline(lang_code='p')
out_segments=[]
for i,(text,target) in enumerate(zip(texts,scene_durations)):
    chunks=[]
    for _,_,audio in pipe(text,voice='pf_dora',speed=1.02):
        chunks.append(audio)
    if not chunks:
        raise RuntimeError(f'No TTS audio scene {i}')
    wav=np.concatenate(chunks).astype(np.float32)
    raw=work/f'raw_{i}.wav'
    sf.write(raw,wav,24000)
    probe=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nk=1:nw=1',str(raw)],text=True).strip())
    desired=max(0.5,target-0.28)
    tempo=probe/desired
    filters=[]
    while tempo>2.0:
        filters.append('atempo=2.0'); tempo/=2.0
    while tempo<0.5:
        filters.append('atempo=0.5'); tempo/=0.5
    filters.append(f'atempo={tempo:.8f}')
    filters += ['highpass=f=85','lowpass=f=9000','acompressor=threshold=-18dB:ratio=2.2:attack=10:release=170','afade=t=in:st=0:d=0.08',f'apad=pad_dur={target}',f'atrim=duration={target}']
    fitted=work/f'scene_{i}.wav'
    subprocess.run(['ffmpeg','-y','-i',str(raw),'-af',','.join(filters),'-ar','48000','-ac','2',str(fitted)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    out_segments.append(fitted)
lst=work/'concat.txt'
lst.write_text(''.join(f"file '{p}'\n" for p in out_segments))
subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i',str(lst),'-c','copy',str(work/'narration.wav')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
print('NARRATION_DURATION',subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nk=1:nw=1',str(work/'narration.wav')],text=True).strip())
PY
python3 "$WORK/audio/tts.py"

echo "=== SYNTHESIZE SOUND DESIGN ==="
cat > "$WORK/audio/bed.py" <<'PY'
import numpy as np, soundfile as sf
sr=48000; dur=59.4; n=int(sr*dur); t=np.arange(n)/sr
rng=np.random.default_rng(20260824)
env=0.55+0.18*np.sin(2*np.pi*0.055*t)+0.12*np.sin(2*np.pi*0.021*t+1.3)
drone=(0.055*np.sin(2*np.pi*43*t)+0.025*np.sin(2*np.pi*64.5*t)+0.014*np.sin(2*np.pi*86*t))*env
noise=rng.normal(0,1,n); kernel=np.ones(1200)/1200; smooth=np.convolve(noise,kernel,mode='same')*0.15
bed=drone+smooth
for when,amp,freq in [(4.8,.10,78),(13.0,.08,102),(20.0,.13,62),(28.0,.15,54),(37.0,.17,48),(43.0,.16,58),(52.0,.17,52)]:
    start=int(when*sr); L=int(1.05*sr); x=np.arange(L)/sr; pulse=amp*np.sin(2*np.pi*freq*x)*np.exp(-4.2*x); end=min(n,start+L); bed[start:end]+=pulse[:end-start]
for when,freq in [(13.22,880),(13.38,1175)]:
    start=int(when*sr); L=int(.22*sr); x=np.arange(L)/sr; bed[start:start+L]+=.09*np.sin(2*np.pi*freq*x)*np.exp(-12*x)
start=int(52.0*sr); L=int(2.2*sr); x=np.arange(L)/sr; bed[start:start+L]+=.12*np.sin(2*np.pi*38*x)*np.exp(-2.2*x)
fade=int(.7*sr); bed[:fade]*=np.linspace(0,1,fade); bed[-fade:]*=np.linspace(1,0,fade)
sf.write('/work/brazil2026/audio/bed.wav',np.stack([bed,bed],axis=1).astype(np.float32),sr)
PY
python3 "$WORK/audio/bed.py"
ffmpeg -y -i "$WORK/audio/narration.wav" -i "$WORK/audio/bed.wav" \
  -filter_complex "[1:a]volume=0.52[bed];[0:a]volume=1.0[vox];[bed][vox]amix=inputs=2:duration=first:weights='0.58 1.0',loudnorm=I=-16:TP=-1.5:LRA=8[a]" \
  -map "[a]" -ar 48000 -ac 2 "$WORK/audio/master.wav" >/dev/null 2>&1

echo "=== BUILD HYPERFRAMES PROJECT ==="
cd "$WORK"
npx --yes hyperframes@0.8.12 init hf-project --non-interactive --example blank >/dev/null
cp "$WORK/processed/datacenter.mp4" "$WORK/hf-project/data-center.mp4"
cat > "$WORK/hf-project/DESIGN.md" <<'EOF'
# Visual identity

## Style Prompt
A dark, cinematic public-interest warning with documentary restraint: real infrastructure under precise editorial motion graphics. Urgent and credible, not cyberpunk, partisan, or sensationalist.

## Colors
- #070B0B — near-black canvas
- #F4F1E8 — warm paper white
- #00A859 — restrained Brazil green
- #7AE582 — signal lime
- #C4383E — warning red
- #9CA7A3 — neutral grey

## Motion
Weighted entrances, vertical wipes, deliberate stagger, no playful motion.

## What NOT to Do
No real candidate faces or party logos. No reusable fake-news screenshots. No hacker hoodies. No dense academic diagrams.
EOF
cat > "$WORK/hf-project/index.html" <<'EOF'
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"/><meta name="viewport" content="width=1080, height=1920"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}html,body{width:1080px;height:1920px;overflow:hidden;background:#070B0B}body{font-family:Inter,Arial,sans-serif;color:#F4F1E8}#root{position:relative;width:100%;height:100%;overflow:hidden;background:#070B0B}#bg-video{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;filter:saturate(.55) contrast(1.14) brightness(.56);z-index:0}.scrim{position:absolute;inset:0;background:radial-gradient(circle at 50% 35%,rgba(0,168,89,.08),rgba(7,11,11,.58) 44%,rgba(7,11,11,.94) 100%);z-index:1}.grain{position:absolute;inset:0;opacity:.12;z-index:2;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.78' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.34'/%3E%3C/svg%3E");mix-blend-mode:soft-light}.scene{position:absolute;inset:0;z-index:5;width:100%;height:100%;padding:116px 76px 120px;display:flex;flex-direction:column;gap:34px;overflow:hidden}.eyebrow{font-size:24px;letter-spacing:.17em;text-transform:uppercase;font-weight:800;color:#7AE582}.headline{font-size:96px;line-height:.92;letter-spacing:-.055em;font-weight:900;max-width:930px}.sub{font-size:36px;line-height:1.3;color:#D8DEDA;max-width:900px}.audio-card{margin-top:auto;width:100%;padding:34px 34px 30px;border:1px solid rgba(122,229,130,.28);border-radius:28px;background:rgba(4,10,8,.78);box-shadow:0 30px 80px rgba(0,0,0,.38)}.audio-top{display:flex;align-items:center;justify-content:space-between;font-size:25px;color:#B8C2BD}.pill{padding:10px 16px;border-radius:999px;background:rgba(196,56,62,.18);color:#FF8C91;font-weight:800;letter-spacing:.08em}.wave{height:142px;margin-top:30px;display:flex;align-items:center;gap:9px}.bar{width:18px;border-radius:12px;background:linear-gradient(180deg,#7AE582,#00A859);transform-origin:center;height:var(--h)}.target-row{display:flex;gap:14px;flex-wrap:wrap;margin-top:24px}.target{font-size:26px;padding:14px 18px;border-radius:999px;background:rgba(244,241,232,.08);border:1px solid rgba(244,241,232,.16)}.label-big{font-size:154px;line-height:.82;letter-spacing:-.07em;font-weight:950;color:#7AE582;font-variant-numeric:tabular-nums}.map-wrap{position:relative;flex:1;min-height:720px;display:flex;align-items:center;justify-content:center}.brazil{position:absolute;width:620px;height:710px;clip-path:polygon(43% 1%,61% 7%,72% 18%,91% 24%,84% 39%,93% 49%,77% 59%,70% 72%,58% 79%,51% 96%,40% 83%,26% 76%,21% 61%,7% 54%,15% 38%,9% 25%,25% 18%,31% 7%);background:linear-gradient(150deg,rgba(0,168,89,.33),rgba(122,229,130,.06));filter:drop-shadow(0 30px 70px rgba(0,168,89,.18))}.node{position:absolute;width:15px;height:15px;border-radius:50%;background:#F4F1E8;box-shadow:0 0 0 6px rgba(122,229,130,.09),0 0 22px rgba(122,229,130,.9)}.beam{position:absolute;height:2px;background:linear-gradient(90deg,rgba(122,229,130,0),rgba(122,229,130,.7),rgba(122,229,130,0));transform-origin:left center}.scale-card{margin-top:auto;padding:30px;border-left:8px solid #C4383E;background:rgba(7,11,11,.76);font-size:34px;line-height:1.28}.stack{display:flex;flex-direction:column;gap:22px;margin-top:26px}.stage{display:grid;grid-template-columns:148px 1fr;gap:24px;align-items:center;padding:28px;border:1px solid rgba(244,241,232,.14);border-radius:24px;background:rgba(7,11,11,.78)}.stage-num{width:116px;height:116px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:43px;font-weight:900;background:rgba(122,229,130,.12);border:2px solid rgba(122,229,130,.5)}.stage h3{font-size:43px}.stage p{font-size:29px;line-height:1.25;color:#C7D0CC;margin-top:7px}.gap{height:112px;border-left:4px dashed #C4383E;margin-left:58px;padding-left:52px;display:flex;align-items:center;font-size:30px;color:#FF8C91;font-weight:800;letter-spacing:.08em}.mitigate{margin-top:auto;font-size:42px;line-height:1.15;font-weight:900}.mitigate span{display:inline-block;margin-right:18px}.wipe{position:absolute;inset:-4%;z-index:50;background:#C4383E;transform-origin:bottom}.wipe.second{background:#00A859}.footer{position:absolute;left:76px;right:76px;bottom:50px;z-index:40;display:flex;justify-content:space-between;font-size:20px;letter-spacing:.08em;color:#9CA7A3}
</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="25" data-width="1080" data-height="1920">
<video id="bg-video" data-start="0" data-duration="25" data-track-index="0" src="data-center.mp4" muted playsinline></video><div class="scrim" data-start="0" data-duration="25" data-track-index="1"></div><div class="grain" data-start="0" data-duration="25" data-track-index="2" data-layout-ignore></div>
<section class="scene" data-start="0" data-duration="7.2" data-track-index="3"><div class="eyebrow s1-e">ÁUDIO ENCAMINHADO · CENÁRIO FICTÍCIO</div><h1 class="headline s1-h">PARECE A VOZ DE UM CANDIDATO.</h1><p class="sub s1-s">Mas a voz foi fabricada e a mensagem foi desenhada para atingir uma pessoa específica.</p><div class="audio-card s1-card"><div class="audio-top"><span>Mensagem de voz · 0:19</span><span class="pill">VOZ CLONADA</span></div><div class="wave"><i class="bar" style="--h:42px"></i><i class="bar" style="--h:92px"></i><i class="bar" style="--h:65px"></i><i class="bar" style="--h:128px"></i><i class="bar" style="--h:74px"></i><i class="bar" style="--h:112px"></i><i class="bar" style="--h:56px"></i><i class="bar" style="--h:138px"></i><i class="bar" style="--h:86px"></i><i class="bar" style="--h:118px"></i><i class="bar" style="--h:48px"></i><i class="bar" style="--h:101px"></i><i class="bar" style="--h:72px"></i><i class="bar" style="--h:132px"></i><i class="bar" style="--h:59px"></i><i class="bar" style="--h:104px"></i><i class="bar" style="--h:80px"></i><i class="bar" style="--h:122px"></i><i class="bar" style="--h:51px"></i><i class="bar" style="--h:96px"></i><i class="bar" style="--h:68px"></i><i class="bar" style="--h:127px"></i><i class="bar" style="--h:62px"></i><i class="bar" style="--h:109px"></i><i class="bar" style="--h:75px"></i><i class="bar" style="--h:134px"></i><i class="bar" style="--h:55px"></i><i class="bar" style="--h:88px"></i></div><div class="target-row"><span class="target">violência contra mulheres</span><span class="target">proteção da família</span><span class="target">medo</span><span class="target">desmobilização</span></div></div></section>
<div id="wipe1" class="wipe" data-start="6.45" data-duration="1.05" data-track-index="6"></div>
<section class="scene" data-start="6.8" data-duration="9.4" data-track-index="4"><div class="eyebrow s2-e">IA AGÊNTICA · OPERAÇÃO EM ESCALA</div><div class="label-big s2-num">100.000</div><h2 class="headline s2-h">TENTATIVAS PERSONALIZADAS.</h2><p class="sub s2-s">Não são cem mil votos garantidos. São cem mil intervenções adaptadas, baratas e difíceis de observar.</p><div class="map-wrap"><div class="brazil s2-map"></div><span class="node" style="left:33%;top:22%"></span><span class="node" style="left:54%;top:16%"></span><span class="node" style="left:68%;top:28%"></span><span class="node" style="left:75%;top:41%"></span><span class="node" style="left:62%;top:53%"></span><span class="node" style="left:51%;top:68%"></span><span class="node" style="left:43%;top:81%"></span><span class="node" style="left:29%;top:65%"></span><span class="node" style="left:22%;top:48%"></span><span class="node" style="left:39%;top:39%"></span><span class="node" style="left:58%;top:36%"></span><span class="node" style="left:46%;top:55%"></span><span class="beam" style="left:22%;top:48%;width:460px;rotate:-18deg"></span><span class="beam" style="left:29%;top:65%;width:390px;rotate:-42deg"></span><span class="beam" style="left:39%;top:39%;width:370px;rotate:22deg"></span><span class="beam" style="left:33%;top:22%;width:410px;rotate:13deg"></span></div><div class="scale-card s2-card">Um grupo pequeno pode transferir decisões de campanha para sistemas que selecionam alvos, adaptam mensagens e distribuem conteúdo em massa.</div></section>
<div id="wipe2" class="wipe second" data-start="15.45" data-duration="1.05" data-track-index="7"></div>
<section class="scene" data-start="15.8" data-duration="9.2" data-track-index="5"><div class="eyebrow s3-e">CAPABILITY · DEPLOYMENT · EFFECT GAP</div><h2 class="headline s3-h">TRÊS PERGUNTAS. UM RISCO.</h2><div class="stack"><div class="stage cde-card"><div class="stage-num">1</div><div><h3>CAPACIDADE</h3><p>O que a inteligência artificial consegue produzir e executar.</p></div></div><div class="stage cde-card"><div class="stage-num">2</div><div><h3>DEPLOYMENT</h3><p>Como a operação chega a escala, com custo baixo e pouca supervisão.</p></div></div><div class="gap s3-gap">O GAP: MEDIR O EFEITO REAL</div><div class="stage cde-card"><div class="stage-num" style="border-color:#C4383E;background:rgba(196,56,62,.14)">3</div><div><h3>EFEITO</h3><p>O que realmente muda no comportamento, na participação e no voto.</p></div></div></div><div class="mitigate s3-m"><span>DETECTAR.</span><span>LIMITAR.</span><span>MITIGAR.</span></div></section>
<div class="footer" data-start="0" data-duration="25" data-track-index="8"><span>NENHUMA VOZ OU CANDIDATO REAL É REPRODUZIDO</span><span>BRASIL · 2026</span></div></div>
<script>window.__timelines=window.__timelines||{};const tl=gsap.timeline({paused:true});tl.from('.s1-e',{opacity:0,y:24,duration:.45,ease:'power2.out'},.18);tl.from('.s1-h',{opacity:0,y:70,duration:.72,ease:'expo.out'},.34);tl.from('.s1-s',{opacity:0,x:-42,duration:.62,ease:'power3.out'},.68);tl.from('.s1-card',{opacity:0,scale:.94,y:48,duration:.7,ease:'back.out(1.35)'},1.02);tl.from('.bar',{scaleY:.08,duration:.34,stagger:.025,ease:'power2.out'},1.36);tl.from('.target',{opacity:0,y:18,duration:.35,stagger:.09,ease:'sine.out'},1.92);tl.fromTo('#wipe1',{scaleY:0,transformOrigin:'bottom'},{scaleY:1,duration:.48,ease:'power4.in'},6.45);tl.to('#wipe1',{scaleY:0,transformOrigin:'top',duration:.52,ease:'power4.out'},6.93);tl.from('.s2-e',{opacity:0,x:-60,duration:.5,ease:'power3.out'},7.12);tl.from('.s2-num',{opacity:0,scale:.72,y:50,duration:.74,ease:'expo.out'},7.25);tl.from('.s2-h',{opacity:0,y:64,duration:.68,ease:'power4.out'},7.58);tl.from('.s2-s',{opacity:0,x:38,duration:.58,ease:'sine.out'},7.95);tl.from('.s2-map',{opacity:0,scale:.82,rotation:-5,duration:.9,ease:'power3.out'},8.22);tl.from('.node',{opacity:0,scale:0,duration:.32,stagger:.13,ease:'back.out(1.8)'},8.56);tl.from('.beam',{opacity:0,scaleX:0,duration:.55,stagger:.18,ease:'power2.out'},9.1);tl.from('.s2-card',{opacity:0,y:44,duration:.62,ease:'expo.out'},10.3);tl.fromTo('#wipe2',{scaleY:0,transformOrigin:'bottom'},{scaleY:1,duration:.48,ease:'power4.in'},15.45);tl.to('#wipe2',{scaleY:0,transformOrigin:'top',duration:.52,ease:'power4.out'},15.93);tl.from('.s3-e',{opacity:0,y:24,duration:.45,ease:'power2.out'},16.12);tl.from('.s3-h',{opacity:0,y:64,duration:.7,ease:'expo.out'},16.28);tl.from('.cde-card',{opacity:0,x:-72,scale:.97,duration:.62,stagger:.52,ease:'power3.out'},16.72);tl.from('.s3-gap',{opacity:0,scaleY:.45,duration:.55,ease:'back.out(1.5)'},18.05);tl.from('.s3-m span',{opacity:0,y:28,duration:.42,stagger:.18,ease:'power2.out'},20.2);tl.to('#root',{opacity:0,duration:.8,ease:'power2.in'},24.15);window.__timelines.main=tl;</script></body></html>
EOF
cd "$WORK/hf-project"
echo "=== HYPERFRAMES CHECK ==="
npx --yes hyperframes@0.8.12 check
echo "HYPERFRAMES_CHECK_OK"
npx --yes hyperframes@0.8.12 render --output "$WORK/out/hyperframes-graphics.mp4" --fps 30 --quality high --workers 4
echo "HYPERFRAMES_RENDER_OK"
ffmpeg -y -ss 0 -i "$WORK/out/hyperframes-graphics.mp4" -t 7.0 -an -c:v libx264 -preset fast -crf 17 -pix_fmt yuv420p "$WORK/processed/hf-deepfake.mp4" >/dev/null 2>&1
ffmpeg -y -ss 7.0 -i "$WORK/out/hyperframes-graphics.mp4" -t 9.0 -an -c:v libx264 -preset fast -crf 17 -pix_fmt yuv420p "$WORK/processed/hf-scale.mp4" >/dev/null 2>&1
ffmpeg -y -ss 16.0 -i "$WORK/out/hyperframes-graphics.mp4" -t 9.0 -an -c:v libx264 -preset fast -crf 17 -pix_fmt yuv420p "$WORK/processed/hf-cde.mp4" >/dev/null 2>&1

echo "=== BUILD REMOTION PROJECT ==="
cd "$WORK/remotion"
cat > package.json <<'EOF'
{"name":"brazil-2026-remotion","private":true,"type":"module","dependencies":{"@remotion/cli":"4.0.506","@remotion/media":"4.0.506","remotion":"4.0.506","react":"19.1.1","react-dom":"19.1.1"},"devDependencies":{"typescript":"5.9.2"}}
EOF
npm install --no-audit --no-fund
cp "$WORK/processed/city.mp4" public/assets/city.mp4; cp "$WORK/processed/woman.mp4" public/assets/woman.mp4; cp "$WORK/processed/phone.mp4" public/assets/phone.mp4; cp "$WORK/processed/hf-deepfake.mp4" public/assets/hf-deepfake.mp4; cp "$WORK/processed/hf-scale.mp4" public/assets/hf-scale.mp4; cp "$WORK/processed/hf-cde.mp4" public/assets/hf-cde.mp4; cp "$WORK/audio/master.wav" public/assets/master.wav
cat > src/index.ts <<'EOF'
import {registerRoot} from "remotion"; import {RemotionRoot} from "./Root"; registerRoot(RemotionRoot);
EOF
cat > src/Root.tsx <<'EOF'
import React from "react"; import {Composition} from "remotion"; import {Brazil2026} from "./Brazil2026"; export const RemotionRoot:React.FC=()=> <Composition id="Brazil2026" component={Brazil2026} durationInFrames={1782} fps={30} width={1080} height={1920}/>;
EOF
cat > src/Brazil2026.tsx <<'EOF'
import React from "react"; import {AbsoluteFill,Easing,Sequence,staticFile,interpolate,useCurrentFrame,useVideoConfig} from "remotion"; import {Audio,Video} from "@remotion/media";
const C={black:"#070B0B",paper:"#F4F1E8",green:"#00A859",lime:"#7AE582",red:"#C4383E",grey:"#9CA7A3"}; const clamp={extrapolateLeft:"clamp" as const,extrapolateRight:"clamp" as const}; const scenes=[{start:0,dur:144},{start:144,dur:246},{start:390,dur:210},{start:600,dur:240},{start:840,dur:270},{start:1110,dur:180},{start:1290,dur:270},{start:1560,dur:222}];
const FilmGrain=()=> <AbsoluteFill style={{pointerEvents:"none",opacity:.13,mixBlendMode:"soft-light",backgroundImage:"url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.82' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.38'/%3E%3C/svg%3E\")"}}/>;
const Scrim=({strength=.72}:{strength?:number})=> <AbsoluteFill style={{background:`radial-gradient(circle at 50% 35%,rgba(0,168,89,.08),rgba(7,11,11,${strength*.62}) 48%,rgba(7,11,11,${strength}) 100%)`}}/>;
const Labels=()=> <><div style={{position:"absolute",top:52,left:58,zIndex:90,padding:"12px 18px",borderRadius:999,border:"1px solid rgba(244,241,232,.28)",background:"rgba(7,11,11,.68)",fontFamily:"Arial",fontSize:20,fontWeight:800,letterSpacing:2.8,color:C.paper}}>CENÁRIO FICTÍCIO</div><div style={{position:"absolute",bottom:34,left:58,right:58,zIndex:90,display:"flex",justifyContent:"space-between",fontFamily:"Arial",fontSize:17,letterSpacing:1.6,color:"rgba(244,241,232,.58)"}}><span>NENHUMA VOZ OU CANDIDATO REAL É REPRODUZIDO</span><span>BRASIL · 2026</span></div></>;
const Caption=({children,accent=C.lime}:{children:React.ReactNode,accent?:string})=>{const f=useCurrentFrame();return <div style={{position:"absolute",left:58,right:58,bottom:94,zIndex:70,translate:`0 ${interpolate(f,[2,16],[32,0],{...clamp,easing:Easing.bezier(.16,1,.3,1)})}px`,opacity:interpolate(f,[2,13],[0,1],clamp),padding:"24px 28px",borderLeft:`6px solid ${accent}`,background:"rgba(7,11,11,.80)",fontFamily:"Arial",fontSize:34,lineHeight:1.24,fontWeight:700,color:C.paper,boxShadow:"0 20px 60px rgba(0,0,0,.28)"}}>{children}</div>};
const Kicker=({children,color=C.lime}:{children:React.ReactNode,color?:string})=>{const f=useCurrentFrame();return <div style={{opacity:interpolate(f,[4,16],[0,1],clamp),translate:`${interpolate(f,[4,18],[-45,0],{...clamp,easing:Easing.bezier(.16,1,.3,1)})}px 0`,fontFamily:"Arial",fontSize:24,fontWeight:900,letterSpacing:4.2,color,textTransform:"uppercase"}}>{children}</div>};
const Title=({children,size=94}:{children:React.ReactNode,size?:number})=>{const f=useCurrentFrame();return <div style={{opacity:interpolate(f,[6,23],[0,1],clamp),translate:`0 ${interpolate(f,[5,25],[76,0],{...clamp,easing:Easing.bezier(.16,1,.3,1)})}px`,fontFamily:"Arial",fontSize:size,lineHeight:.94,letterSpacing:-4.8,fontWeight:950,color:C.paper,maxWidth:930}}>{children}</div>};
const VBg=({src,scaleTo=1.06,position="50% 50%"}:{src:string,scaleTo?:number,position?:string})=>{const f=useCurrentFrame();const {durationInFrames}=useVideoConfig();return <AbsoluteFill style={{overflow:"hidden",background:C.black}}><Video src={staticFile(src)} muted style={{width:"100%",height:"100%",objectFit:"cover",objectPosition:position,scale:interpolate(f,[0,durationInFrames],[1,scaleTo],clamp)}}/></AbsoluteFill>};
const S0=()=>{const f=useCurrentFrame();return <AbsoluteFill><VBg src="assets/city.mp4" scaleTo={1.08}/><Scrim strength={.78}/><div style={{position:"absolute",inset:0,display:"flex",flexDirection:"column",justifyContent:"center",padding:"90px 70px 260px",gap:30}}><Kicker>ELEIÇÕES GERAIS · OUTUBRO DE 2026</Kicker><div style={{opacity:interpolate(f,[5,18],[0,1],clamp),scale:interpolate(f,[0,28],[1.2,1],{...clamp,easing:Easing.bezier(.16,1,.3,1)}),fontFamily:"Arial",fontWeight:950,fontSize:194,lineHeight:.79,letterSpacing:-12,color:C.paper}}>24<br/>HORAS</div><div style={{opacity:interpolate(f,[18,34],[0,1],clamp),fontFamily:"Arial",fontSize:42,fontWeight:800,color:C.lime}}>PARA A VOTAÇÃO.</div></div><Caption>O risco começa antes de qualquer ataque à urna.</Caption></AbsoluteFill>};
const S1=()=>{const f=useCurrentFrame();return <AbsoluteFill><VBg src="assets/woman.mp4" scaleTo={1.08} position="53% 50%"/><Scrim strength={.76}/><div style={{position:"absolute",inset:0,padding:"160px 64px 280px",display:"flex",flexDirection:"column",gap:24}}><Kicker>RECIFE · PERSONAGEM FICTÍCIA</Kicker><Title size={116}>ANA,<br/><span style={{color:C.lime}}>42 ANOS.</span></Title><div style={{marginTop:"auto",translate:`0 ${interpolate(f,[28,48],[70,0],clamp)}px`,opacity:interpolate(f,[25,48],[0,1],clamp),padding:28,borderRadius:26,border:"1px solid rgba(244,241,232,.22)",background:"rgba(7,11,11,.76)",fontFamily:"Arial"}}><div style={{fontSize:31,fontWeight:900}}>AUXILIAR DE ENFERMAGEM</div><div style={{fontSize:26,color:"#C8D0CC",marginTop:8}}>Abre o grupo de WhatsApp das mães do bairro.</div></div></div><Caption>Uma pessoa comum. Um grupo comum. Uma intervenção feita para ela.</Caption></AbsoluteFill>};
const HF=({src,caption}:{src:string,caption:string})=> <AbsoluteFill style={{background:C.black}}><Video src={staticFile(src)} muted style={{width:"100%",height:"100%",objectFit:"cover"}}/><Caption>{caption}</Caption></AbsoluteFill>;
const S3=()=>{const f=useCurrentFrame();return <AbsoluteFill><VBg src="assets/phone.mp4" scaleTo={1.1}/><Scrim strength={.84}/><div style={{position:"absolute",inset:0,padding:"160px 66px 280px",display:"flex",flexDirection:"column",gap:30}}><Kicker color="#FF8C91">O EFEITO BUSCADO</Kicker><div style={{marginTop:100,translate:`0 ${interpolate(f,[18,38],[70,0],clamp)}px`,opacity:interpolate(f,[14,38],[0,1],clamp),alignSelf:"flex-end",maxWidth:760,padding:"28px 32px",borderRadius:"28px 28px 8px 28px",background:"#0B6B47",fontFamily:"Arial",fontSize:52,fontWeight:800}}>Eu não vou votar.</div><div style={{marginTop:"auto",opacity:interpolate(f,[48,70],[0,1],clamp),fontFamily:"Arial",fontSize:72,lineHeight:.96,fontWeight:950}}>ELA NÃO MUDA<br/>DE CANDIDATO.</div><div style={{opacity:interpolate(f,[86,112],[0,1],clamp),fontFamily:"Arial",fontSize:105,lineHeight:.88,fontWeight:950,color:"#FF767B"}}>ELA DESISTE.</div></div><Caption accent={C.red}>A agência da eleitora é deslocada sem tocar na infraestrutura eleitoral.</Caption></AbsoluteFill>};
const S5=()=>{const f=useCurrentFrame();return <AbsoluteFill><VBg src="assets/city.mp4" scaleTo={1.03} position="50% 66%"/><Scrim strength={.9}/><div style={{position:"absolute",inset:0,padding:"160px 65px 280px",display:"flex",flexDirection:"column",alignItems:"center",gap:34}}><Kicker color="#FF8C91">SEGURANÇA ELEITORAL</Kicker><div style={{marginTop:80,translate:`0 ${interpolate(f,[6,30],[120,0],clamp)}px`,opacity:interpolate(f,[4,28],[0,1],clamp),width:540,height:610,borderRadius:34,background:"#D9DDD9",border:"10px solid #F4F1E8",position:"relative"}}><div style={{position:"absolute",top:58,left:70,right:70,height:245,background:"#111A18",borderRadius:14,border:"8px solid #7D8781",display:"flex",alignItems:"center",justifyContent:"center",fontFamily:"Arial",fontSize:54,fontWeight:950,color:C.lime}}>VOTO</div><div style={{position:"absolute",left:70,right:70,bottom:70,display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:16}}>{[1,2,3,4,5,6,7,8,9].map(n=><div key={n} style={{height:68,borderRadius:12,background:"#606A65",display:"flex",alignItems:"center",justifyContent:"center",fontFamily:"Arial",fontWeight:900,fontSize:30}}>{n}</div>)}</div><div style={{position:"absolute",inset:-55,opacity:interpolate(f,[76,104],[0,1],clamp),rotate:"-38deg",borderTop:"22px solid #C4383E",top:330}}/></div><div style={{fontFamily:"Arial",fontSize:72,lineHeight:.96,fontWeight:950,textAlign:"center"}}>A URNA NÃO<br/><span style={{color:"#FF767B"}}>FOI HACKEADA.</span></div></div><Caption accent={C.red}>O ataque pode mirar a vontade, não a máquina.</Caption></AbsoluteFill>};
const S7=()=>{const f=useCurrentFrame();return <AbsoluteFill><VBg src="assets/city.mp4" scaleTo={1.04} position="50% 62%"/><Scrim strength={.92}/><div style={{position:"absolute",inset:0,padding:"175px 64px 260px",display:"flex",flexDirection:"column",justifyContent:"center",gap:42,opacity:interpolate(f,[10,42,176,215],[0,1,1,0],clamp)}}><Kicker>DETECTAR · LIMITAR · MITIGAR</Kicker><div style={{fontFamily:"Arial",fontSize:102,lineHeight:.91,fontWeight:950}}>A URNA PODE<br/>FICAR INTACTA.</div><div style={{fontFamily:"Arial",fontSize:124,lineHeight:.86,fontWeight:950,color:"#FF767B",opacity:interpolate(f,[30,65],[0,1],clamp)}}>A VONTADE,<br/>NÃO.</div><div style={{fontFamily:"Arial",fontSize:28,lineHeight:1.3,color:"#C5CDC9",maxWidth:840}}>Compreender o capability–deployment–effect gap ajuda a agir antes que o efeito seja irreversível.</div></div></AbsoluteFill>};
const Wipe=({color}:{color:string})=>{const f=useCurrentFrame();return <AbsoluteFill style={{zIndex:100,translate:`${interpolate(f,[0,9,14,24],[-1120,0,0,1120],clamp)}px 0`,background:color}}/>};
export const Brazil2026:React.FC=()=>{const comps=[S0,S1,()=> <HF src="assets/hf-deepfake.mp4" caption="Parece real. É personalizado. E a voz é falsa."/>,S3,()=> <HF src="assets/hf-scale.mp4" caption="Escala não significa cem mil votos mudados. Significa cem mil tentativas adaptadas."/>,S5,()=> <HF src="assets/hf-cde.mp4" caption="Capacidade. Implantação em escala. Efeito real no comportamento e no voto."/>,S7];return <AbsoluteFill style={{background:C.black,color:C.paper}}><Audio src={staticFile("assets/master.wav")}/>{scenes.map((s,i)=>{const Comp=comps[i];return <Sequence key={i} from={s.start} durationInFrames={s.dur} layout="absolute-fill"><Comp/></Sequence>})}{scenes.slice(1).map((s,i)=><Sequence key={i} from={s.start-12} durationInFrames={26} layout="absolute-fill"><Wipe color={i%2===0?C.red:C.green}/></Sequence>)}<Labels/><FilmGrain/></AbsoluteFill>};
EOF
mkdir -p "$WORK/remotion/out"
echo "=== REMOTION FRAME CHECKS ==="
npx remotion still src/index.ts Brazil2026 "$WORK/out/frame-300.png" --frame=300 --scale=0.5
npx remotion still src/index.ts Brazil2026 "$WORK/out/frame-930.png" --frame=930 --scale=0.5
npx remotion still src/index.ts Brazil2026 "$WORK/out/frame-1400.png" --frame=1400 --scale=0.5
echo "REMOTION_STILLS_OK"
echo "=== REMOTION FINAL RENDER ==="
npx remotion render src/index.ts Brazil2026 "$WORK/out/Brasil_2026_Harmful_Manipulation_FINAL.mp4" --codec=h264 --crf=17 --pixel-format=yuv420p --concurrency=6
echo "REMOTION_RENDER_OK"
ffmpeg -y -i "$WORK/out/Brasil_2026_Harmful_Manipulation_FINAL.mp4" -vf "scale=540:960" -c:v libx264 -preset fast -crf 24 -c:a aac -b:a 128k "$WORK/out/Brasil_2026_Harmful_Manipulation_PREVIEW.mp4" >/dev/null 2>&1
ffmpeg -y -i "$WORK/out/Brasil_2026_Harmful_Manipulation_FINAL.mp4" -vf "fps=1/8,scale=270:480,tile=4x2:padding=8:margin=8" -frames:v 1 "$WORK/out/contact-sheet.jpg" >/dev/null 2>&1
cat > "$WORK/README.md" <<'EOF'
# Brazil 2026 — Harmful Manipulation
Fictional public-interest explainer rendered with HyperFrames 0.8.12 and Remotion 4.0.506, with Kokoro Brazilian Portuguese narration and Pixabay stock under the source-page license. No real candidate likeness or voice is reproduced.
EOF
rm -rf "$WORK/remotion/node_modules"
cp "$WORK/hf-project/DESIGN.md" "$WORK/DESIGN.md"
cd "$WORK"; zip -qr "$WORK/out/Brasil_2026_HyperFrames_Remotion_SOURCES.zip" hf-project remotion/src remotion/public remotion/package.json README.md DESIGN.md
for f in "$WORK/out/Brasil_2026_Harmful_Manipulation_FINAL.mp4" "$WORK/out/Brasil_2026_Harmful_Manipulation_PREVIEW.mp4" "$WORK/out/Brasil_2026_HyperFrames_Remotion_SOURCES.zip" "$WORK/out/contact-sheet.jpg"; do ls -lh "$f"; done
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate:format=duration,size -of default=nw=1 "$WORK/out/Brasil_2026_Harmful_Manipulation_FINAL.mp4"
echo "=== UPLOAD ARTIFACTS ==="
python3 - <<'PY'
import requests, pathlib, time
files=[pathlib.Path('/work/brazil2026/out/Brasil_2026_Harmful_Manipulation_FINAL.mp4'),pathlib.Path('/work/brazil2026/out/Brasil_2026_Harmful_Manipulation_PREVIEW.mp4'),pathlib.Path('/work/brazil2026/out/Brasil_2026_HyperFrames_Remotion_SOURCES.zip'),pathlib.Path('/work/brazil2026/out/contact-sheet.jpg')]
for p in files:
    for attempt in range(4):
        try:
            with p.open('rb') as fh:r=requests.post('https://tmpfiles.org/api/v1/upload',files={'file':(p.name,fh)},timeout=900)
            r.raise_for_status(); url=r.json()['data']['url']; direct=url.replace('https://tmpfiles.org/','https://tmpfiles.org/dl/'); print(f'ARTIFACT|{p.name}|{url}|{direct}',flush=True); break
        except Exception as e:
            print('UPLOAD_RETRY',p.name,attempt+1,type(e).__name__,str(e)[:240],flush=True)
            if attempt==3:raise
            time.sleep(3*(attempt+1))
print('ALL_DONE',flush=True)
PY
