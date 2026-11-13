/* Snibble web — Pyodide bridge + Canvas2D renderer.
 * Simulation runs unmodified Python (snibble/world.py, snibble/bot.py)
 * inside the browser via WASM; JS only ticks, draws and feeds input. */

const COLORS = [
  [0.20,0.78,0.35],[0.00,0.74,0.83],[0.94,0.21,0.48],[1.00,0.72,0.05],
  [0.42,0.36,0.90],[0.95,0.34,0.27],[0.55,0.76,0.29]];
const PORTAL_COLS = [[0.2,0.9,0.9],[0.95,0.3,0.9],[1.0,0.6,0.15]];
const css = (c,a=1)=>`rgba(${c.map(v=>v*255|0).join()},${a})`;
const dark = c=>c.map(v=>v*0.45);

const cv = document.getElementById('cv'), ctx = cv.getContext('2d');
const $ = id => document.getElementById(id);
let py, world=null, stepFn=null, dumpFn=null, decideFn=null;
let cam = {x:150,y:150,z:28};           // z = cells per screen height
let ptr = {x:0,y:0,down:false,useKeys:false};
let keys = {}, lastT=0, st=null, deadShown=false, camInit=false;

function resize(){ cv.width=innerWidth*devicePixelRatio;
  cv.height=innerHeight*devicePixelRatio; }
addEventListener('resize', resize); resize();

// ---------- boot ----------
(async()=>{
  $('loadmsg').textContent='pyodide';
  py = await loadPyodide();
  $('loadmsg').textContent='game code';
  py.FS.mkdir('/snibble_pkg');
  for (const f of ['__init__','world','bot']) {
    const r = await fetch(`../snibble/${f}.py`);
    py.FS.writeFile(`/snibble_pkg/${f}.py`, await r.text());
  }
  py.runPython(`
import sys, os
sys.path.insert(0, '/')
os.rename('/snibble_pkg', '/snibble')
from snibble import world as W
from snibble import bot as B
world = None
def init(name, castles, cannons, frogs, portals):
    global world
    world = W.World(player_name=name, castles=castles,
                    cannons=cannons, frogs=frogs, portals=portals)
    return static_dump()
def static_dump():
    import json
    return json.dumps({'obstacles': world.obstacles,
                       'portals': world.portals,
                       'cannons': world.cannons})
def step(dt):
    world.tick(dt, B.decide)
    return dump()
def dump():
    import json
    pl = world.player
    return json.dumps({
      'time': world.time,
      'player': {'alive': pl.alive, 'len': pl.length,
                 'x': pl.head[0], 'y': pl.head[1]},
      'snakes': [{'c': s.color, 'n': s.name, 'a': s.alive,
                  'sh': s.shield > 0, 'len': s.length,
                  'bot': s.is_bot,
                  'sp': [list(p) for p in s.spine]}
                 for s in world.snakes],
      'crystals': [[k[0], k[1], v] for k, v in world.crystals.items()],
      'frogs': world.frogs,
      'bullets': world.bullets,
    })
def steer(angle): world.player.target_angle = angle
def boost(on): world.player.boost = bool(on)
def respawn(): world.respawn_player()
`);
  stepFn = py.globals.get('step');
  decideFn = py.globals.get('decide');
  $('load').classList.add('hidden');
  frame(0);
  if (location.hash === '#autoplay') startGame();
})().catch(e => { $('loadmsg').textContent = 'ERROR: ' + e; });

// ---------- game control ----------
let obstacles=[], portals=[], cannons=[];
function startGame(){
  const mods = id=>$(id).checked;
  const init = py.globals.get('init');
  const sd = JSON.parse(init($('name').value||'You',
    mods('m-castles'), mods('m-cannons'),
    mods('m-frogs'), mods('m-portals')));
  obstacles = sd.obstacles; portals = sd.portals; cannons = sd.cannons;
  world = true; deadShown = false; camInit = false;
  $('menu').style.display='none'; $('dead').style.display='none';
  $('rank').classList.remove('hidden');
  $('boost').classList.remove('hidden');
  $('zoom').classList.remove('hidden');
}
$('play').onclick = startGame;
$('retry').onclick = ()=>{ py.globals.get('respawn')();
  deadShown=false; $('dead').style.display='none'; };
$('tomenu').onclick = ()=>{ $('dead').style.display='none';
  $('menu').style.display='flex'; world=null;
  ['rank','boost','zoom'].forEach(i=>$(i).classList.add('hidden')); };
$('zin').onclick = ()=> cam.z = Math.max(14, cam.z/1.25);
$('zout').onclick = ()=> cam.z = Math.min(60, cam.z*1.25);

// ---------- input ----------
cv.addEventListener('pointermove', e=>{
  ptr.x=e.clientX; ptr.y=e.clientY; ptr.useKeys=false; });
cv.addEventListener('pointerdown', e=>{
  ptr.x=e.clientX; ptr.y=e.clientY; ptr.down=true; ptr.useKeys=false; });
addEventListener('pointerup', ()=>ptr.down=false);
$('boost').addEventListener('pointerdown', e=>{
  e.preventDefault(); $('boost').classList.add('on');
  if(world) py.globals.get('boost')(1); });
$('boost').addEventListener('pointerup', ()=>{
  $('boost').classList.remove('on');
  if(world) py.globals.get('boost')(0); });
addEventListener('keydown', e=>{
  keys[e.key]=true; ptr.useKeys=true;
  if(e.key===' '){ e.preventDefault();
    if(world) py.globals.get('boost')(1); }});
addEventListener('keyup', e=>{
  keys[e.key]=false;
  if(e.key===' '&&world) py.globals.get('boost')(0); });

const KD = {ArrowUp:[0,-1],ArrowDown:[0,1],ArrowLeft:[-1,0],
  ArrowRight:[1,0],w:[0,-1],s:[0,1],a:[-1,0],d:[1,0]};

// ---------- render ----------
function frame(t){
  requestAnimationFrame(frame);
  const dt = Math.min((t-lastT)/1000||0.016, 0.05); lastT=t;
  if(world){
    st = JSON.parse(stepFn(dt));
    const pl = st.player;
    if(!camInit){ camInit=true; cam.x=pl.x; cam.y=pl.y; }
    cam.x += (pl.x-cam.x)*Math.min(1,dt*5);
    cam.y += (pl.y-cam.y)*Math.min(1,dt*5);
    // death screen (once)
    if(!pl.alive && !deadShown){
      deadShown = true;
      $('deadscore').textContent = 'len ' + (pl.len|0);
      $('dead').style.display='flex';
    }
    const steer = py.globals.get('steer');
    if(pl.alive && !ptr.useKeys){
      const s = cam.z/cv.height*devicePixelRatio;
      const wx = cam.x + (ptr.x*devicePixelRatio-cv.width/2)*s;
      const wy = cam.y + (ptr.y*devicePixelRatio-cv.height/2)*s;
      steer(Math.atan2(wy-pl.y, wx-pl.x));
    } else if(pl.alive){
      let dx=0,dy=0;
      for(const k in KD) if(keys[k]){dx+=KD[k][0];dy+=KD[k][1];}
      if(dx||dy) steer(Math.atan2(dy,dx));
    }
    // ranking
    $('rank').textContent = st.snakes
      .filter(s=>s.a).sort((a,b)=>b.len-a.len).slice(0,8)
      .map((s,i)=>`${i+1}. ${s.n} ${s.len|0}`).join('\n');
  }
  try { draw(); } catch(e) {
    if(!window._e){window._e=1;console.log('DRAWERR', e.message, e.stack);}
  }
}

function draw(){
  const s = cv.height/cam.z;
  ctx.setTransform(1,0,0,1,0,0);
  ctx.fillStyle='#6db34a'; ctx.fillRect(0,0,cv.width,cv.height);
  ctx.setTransform(s,0,0,s, cv.width/2-cam.x*s, cv.height/2-cam.y*s);
  const W=300;
  // brick wall border
  ctx.strokeStyle='#8a5a3a'; ctx.lineWidth=2.4;
  ctx.strokeRect(0,0,W,W);
  ctx.strokeStyle='#5a3a22'; ctx.lineWidth=0.25;
  ctx.strokeRect(0,0,W,W);
  if(!world) return;
  // castle/cannon obstacles
  ctx.fillStyle='#8a6a4a'; ctx.strokeStyle='#4a3320'; ctx.lineWidth=0.2;
  for(const[x1,y1,x2,y2]of obstacles){
    ctx.fillRect(x1,y1,x2-x1,y2-y1); ctx.strokeRect(x1,y1,x2-x1,y2-y1);}
  // portals
  for(const p of portals){
    const c=PORTAL_COLS[p.pair%3];
    ctx.beginPath(); ctx.arc(p.x,p.y,1.0,0,7);
    ctx.strokeStyle=css(c); ctx.lineWidth=0.45; ctx.stroke();
    ctx.beginPath(); ctx.arc(p.x,p.y,0.6,0,7);
    ctx.fillStyle='rgba(20,20,40,.9)'; ctx.fill();}
  // crystals
  for(const[cx,cy,v]of st.crystals){
    const x=cx+.5,y=cy+.5,r=v>=30?0.9:v>=5?0.55:v>=2?0.45:0.35;
    ctx.fillStyle=v>=30?'#fff':v>=2?'#ff598c':'#ffd640';
    ctx.strokeStyle=v>=30?'#ffd640':v>=2?'#a02050':'#a08010';
    ctx.lineWidth=0.1;
    ctx.beginPath();
    ctx.moveTo(x,y-r);ctx.lineTo(x+r*.7,y);ctx.lineTo(x,y+r);ctx.lineTo(x-r*.7,y);
    ctx.closePath(); ctx.fill(); ctx.stroke();}
  // frogs
  for(const f of st.frogs){
    ctx.fillStyle='#4caf50'; ctx.strokeStyle='#1b5e20'; ctx.lineWidth=0.12;
    ctx.beginPath(); ctx.ellipse(f.x,f.y,0.55,0.42,0,0,7); ctx.fill(); ctx.stroke();
    for(const s of[-1,1]){
      ctx.fillStyle='#fff';
      ctx.beginPath(); ctx.arc(f.x+s*0.22,f.y-0.32,0.17,0,7); ctx.fill();
      ctx.fillStyle='#111';
      ctx.beginPath(); ctx.arc(f.x+s*0.22,f.y-0.32,0.08,0,7); ctx.fill();}}
  // bullets
  ctx.fillStyle='#222';
  for(const b of st.bullets){
    ctx.beginPath(); ctx.arc(b.x,b.y,0.35,0,7); ctx.fill();}
  // snakes (outline pass then fill pass, split at gaps)
  for(const pass of[0,1]) for(const sn of st.snakes){
    if(!sn.a) continue;
    const col = COLORS[sn.c%COLORS.length];
    ctx.strokeStyle = pass?css(col,sn.sh?0.55:1):css(dark(col),sn.sh?0.4:1);
    ctx.lineWidth = pass?1.3:1.9; ctx.lineCap='round'; ctx.lineJoin='round';
    ctx.beginPath();
    let pen=false, px=0, py=0;
    for(const[x,y]of sn.sp){
      if(!pen||Math.hypot(x-px,y-py)>2){ctx.moveTo(x,y);pen=true;}
      else ctx.lineTo(x,y);
      px=x; py=y;}
    ctx.stroke();}
  // heads + eyes
  for(const sn of st.snakes){
    if(!sn.a) continue;
    const[x,y]=sn.sp[0], col=COLORS[sn.c%COLORS.length];
    const ang = sn.sp.length>1?
      Math.atan2(y-sn.sp[1][1],x-sn.sp[1][0]):0;
    ctx.beginPath(); ctx.arc(x,y,0.95,0,7);
    ctx.fillStyle=css(col,sn.sh?0.55:1); ctx.fill();
    ctx.strokeStyle=css(dark(col)); ctx.lineWidth=0.2; ctx.stroke();
    for(const off of[-0.85,0.85]){
      const a=ang+off;
      const ex=x+Math.cos(a)*0.55, ey=y+Math.sin(a)*0.55;
      ctx.beginPath(); ctx.arc(ex,ey,0.34,0,7);
      ctx.fillStyle='#fff'; ctx.fill();
      ctx.beginPath();
      ctx.arc(ex+Math.cos(ang)*0.12,ey+Math.sin(ang)*0.12,0.17,0,7);
      ctx.fillStyle='#111'; ctx.fill();}}
}
