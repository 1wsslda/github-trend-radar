#!/usr/bin/env python3
from __future__ import annotations

CSS = r""":root{
  --font-sans:"HarmonyOS Sans SC","MiSans","Source Han Sans SC","PingFang SC","Microsoft YaHei",sans-serif;
  --font-mono:"JetBrains Mono","Maple Mono","Fira Code",monospace;
  --ease-smooth:cubic-bezier(0.16, 1, 0.3, 1);
  --bg:#12100d;
  --bg-soft:#171410;
  --surface:#1b1813;
  --surface-2:#221e18;
  --surface-3:#2b261f;
  --border:rgba(232,214,184,.12);
  --border-strong:rgba(246,222,174,.24);
  --text:#f2ebdf;
  --text-soft:#d8cdbd;
  --muted:#9d907b;
  --muted-soft:#7e725f;
  --accent:#e3c691;
  --accent-strong:#f1d8aa;
  --accent-ink:#23180a;
  --green:#7fd0a0;
  --amber:#d7b171;
  --danger:#f1a498;
  --shadow:0 16px 36px rgba(0,0,0,.22);
  --shadow-soft:0 10px 26px rgba(0,0,0,.18);
}
*{box-sizing:border-box}
html,body{height:100%}
body{
  margin:0;
  color:var(--text);
  background:
    radial-gradient(circle at top left, rgba(227,198,145,.08), transparent 0 34%),
    linear-gradient(180deg,#100f0c 0%,#14120f 50%,#15130f 100%);
  font-family:var(--font-sans);
  font-size:15px;
  line-height:1.7;
  text-rendering:optimizeLegibility;
  font-kerning:normal;
  -webkit-font-smoothing:antialiased;
  -moz-osx-font-smoothing:grayscale;
}
button,input,select,textarea{font:inherit}
a{color:inherit;text-decoration:none}
:focus-visible{
  outline:none;
  box-shadow:0 0 0 3px rgba(227,198,145,.16);
}
::selection{background:rgba(227,198,145,.22);color:var(--text)}

::-webkit-scrollbar{width:10px;height:10px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{
  background:rgba(232,214,184,.14);
  border-radius:999px;
  border:2px solid var(--bg);
}
::-webkit-scrollbar-thumb:hover{background:rgba(232,214,184,.24)}
::-webkit-scrollbar-corner{background:transparent}

.page{
  position:relative;
  max-width:1720px;
  margin:0 auto;
  padding:clamp(18px,2.6vw,30px) clamp(16px,2vw,28px) 148px;
}
body.overlay-open{
  overflow:hidden;
}
.masthead{
  display:grid;
  grid-template-columns:minmax(0,1.45fr) minmax(320px,.9fr);
  gap:18px;
  margin-bottom:20px;
}
.masthead-copy,
.masthead-side{
  position:relative;
  overflow:visible;
  padding:24px clamp(20px,2vw,28px);
  border:1px solid var(--border);
  border-radius:28px;
  background:linear-gradient(180deg, rgba(28,24,19,.94), rgba(16,14,11,.98));
  box-shadow:var(--shadow);
}
.masthead-copy::before,
.masthead-side::before{
  content:"";
  position:absolute;
  inset:0;
  pointer-events:none;
  background:radial-gradient(circle at top right, rgba(233,201,143,.1), transparent 0 42%);
}
.masthead-copy{
  overflow:hidden;
  display:grid;
  gap:14px;
  align-content:start;
}
.masthead-copy > *,
.masthead-side > *{
  position:relative;
  z-index:1;
}
.masthead-title-row{
  display:flex;
  flex-wrap:wrap;
  align-items:flex-end;
  gap:14px;
}
.masthead-title{
  margin:0;
  font-size:clamp(2.2rem,5vw,4.2rem);
  line-height:.92;
  letter-spacing:-.07em;
  font-weight:720;
}
.masthead-badge{
  display:inline-flex;
  align-items:center;
  min-height:32px;
  padding:0 12px;
  border-radius:999px;
  border:1px solid rgba(233,201,143,.14);
  background:rgba(233,201,143,.08);
  color:var(--accent-strong);
  font-family:var(--font-mono);
  font-size:.72rem;
  letter-spacing:.08em;
  text-transform:uppercase;
}
.masthead-sub{
  margin:0;
  max-width:58ch;
  color:var(--text-soft);
  font-size:1rem;
  line-height:1.72;
}
.masthead-side{
  display:grid;
  gap:18px;
  align-content:space-between;
  z-index:4;
}
.status-card{
  display:grid;
  gap:8px;
  padding:18px;
  border:1px solid rgba(232,214,184,.1);
  border-radius:22px;
  background:rgba(13,11,9,.42);
}
.runtime-note{
  color:var(--text);
  font-size:1rem;
  line-height:1.55;
}
.nav-actions{
  display:flex;
  flex-wrap:wrap;
  gap:10px;
  align-items:center;
  justify-content:flex-end;
}

.hero-kicker,
.field-label,
.group-label,
.status-label,
.batch-dock-label,
.badge,
.tab-count,
.meta-rank,
.detail-item strong{
  font-family:var(--font-mono);
  font-variant-numeric:tabular-nums;
}
.hero-kicker{
  display:inline-flex;
  align-items:center;
  gap:10px;
  color:var(--accent);
  font-size:10px;
  letter-spacing:.18em;
  text-transform:uppercase;
}
.status-label{
  color:var(--muted);
  font-size:10px;
  letter-spacing:.14em;
  text-transform:uppercase;
}
.status-value{
  min-width:0;
  color:var(--text-soft);
  font-size:.88rem;
  line-height:1.5;
}
.status-divider{
  width:1px;
  height:12px;
  background:rgba(232,214,184,.14);
}
.toolbar-utility,
.badges,
.meta-line,
.card-actions,
.panel-actions,
.settings-actions,
.topic-list{
  display:flex;
  gap:10px;
  flex-wrap:wrap;
  align-items:center;
}

.toolbar{margin-bottom:18px}
.control-shell{
  display:grid;
  gap:16px;
  padding:18px 20px;
  border:1px solid var(--border);
  border-radius:22px;
  background:linear-gradient(180deg, rgba(24,21,17,.94), rgba(18,16,13,.98));
  box-shadow:var(--shadow);
}
.toolbar-head{
  display:flex;
  justify-content:space-between;
  gap:16px;
  align-items:flex-end;
  flex-wrap:wrap;
}
.toolbar-copy{
  display:grid;
  gap:6px;
  min-width:0;
}
.summary{
  font-size:1rem;
  font-weight:620;
  letter-spacing:-.02em;
  line-height:1.35;
}
.sub{
  color:var(--muted);
  font-size:.84rem;
  line-height:1.58;
}
.metric-number{
  font-family:var(--font-mono);
  font-variant-numeric:tabular-nums;
}
.toolbar-main{
  display:grid;
  grid-template-columns:minmax(0,1fr) auto;
  gap:14px;
  align-items:end;
}
.toolbar-filters{
  display:grid;
  grid-template-columns:minmax(0,1.45fr) minmax(220px,.74fr) minmax(0,1.2fr);
  gap:14px;
  align-items:end;
}
.discover-shell{
  display:grid;
  gap:20px;
  padding:24px 0;
  background:transparent;
  border:none;
}
.discover-grid{
  display:grid;
  grid-template-columns:minmax(0,1.7fr) minmax(220px,.8fr) minmax(140px,.4fr);
  gap:14px;
}
.discover-actions{
  display:flex;
  gap:12px;
  flex-wrap:wrap;
  align-items:center;
}
.checkline{
  display:inline-flex;
  align-items:center;
  gap:8px;
  min-height:40px;
  padding:0 12px;
  border:1px solid rgba(232,214,184,.1);
  border-radius:999px;
  background:rgba(12,10,8,.3);
  color:var(--text-soft);
}
.checkline input{
  accent-color:var(--accent);
}
.discover-panel,
.discover-meta,
.discover-top{
  display:grid;
  gap:10px;
}
.discover-saved{
  display:flex;
  gap:10px;
  flex-wrap:wrap;
}
.discover-chip{
  min-width:min(100%,260px);
  padding:12px 14px;
  border:1px solid rgba(232,214,184,.1);
  border-radius:16px;
  background:rgba(12,10,8,.32);
  display:grid;
  gap:8px;
}
.discover-chip-head,
.discover-chip-actions,
.reason-strip,
.discover-top-grid{
  display:flex;
  gap:8px;
  flex-wrap:wrap;
  align-items:center;
}
.discover-chip-title{
  font-weight:620;
  line-height:1.3;
  word-break:break-word;
}
.discover-chip-note{
  color:var(--muted);
  font-size:.8rem;
}
.discover-meta-card{
  padding:14px 16px;
  border:1px solid rgba(232,214,184,.1);
  border-radius:16px;
  background:rgba(12,10,8,.28);
  color:var(--text-soft);
}
.discover-meta-card.loading{
  border-color:rgba(233,201,143,.26);
  background:linear-gradient(180deg, rgba(36,30,22,.88), rgba(16,13,10,.9));
}
.discover-meta-title{
  color:var(--muted);
  font-size:11px;
  letter-spacing:.12em;
  text-transform:uppercase;
}
.discover-loading-row{
  display:flex;
  gap:10px;
  align-items:center;
  margin-bottom:8px;
}
.discover-spinner{
  width:16px;
  height:16px;
  border-radius:999px;
  border:2px solid rgba(233,201,143,.18);
  border-top-color:var(--accent);
  animation:discover-spin .8s linear infinite;
}
.discover-loading-copy{
  color:var(--muted);
  font-size:.84rem;
}
@keyframes discover-spin{
  from{transform:rotate(0deg)}
  to{transform:rotate(360deg)}
}
.discover-top-grid{
  display:grid;
  grid-template-columns:repeat(5,minmax(0,1fr));
}
.discover-top-card{
  padding:14px;
  border:1px solid rgba(233,201,143,.12);
  border-radius:16px;
  background:linear-gradient(180deg, rgba(34,29,23,.92), rgba(18,16,13,.96));
  display:grid;
  gap:8px;
}
.discover-top-rank{
  color:var(--accent);
  font-family:var(--font-mono);
  font-size:.8rem;
}
.reason-strip{
  gap:6px;
}
.reason-pill{
  display:inline-flex;
  align-items:center;
  min-height:24px;
  padding:0 8px;
  border-radius:999px;
  background:rgba(233,201,143,.08);
  border:1px solid rgba(233,201,143,.1);
  color:var(--text-soft);
  font-size:.74rem;
}
.control-group{
  display:grid;
  gap:8px;
  min-width:0;
}
.control-group.is-disabled{opacity:.5}
    .group-label{
      padding-left:2px;
      color:var(--muted);
      font-size:11px;
      letter-spacing:.14em;
      text-transform:uppercase;
      line-height:1;
    }
    
.field{
  position:relative;
  display:grid;
  gap:8px;
  min-width:0;
}
.field-label{
  padding-left:2px;
  color:var(--muted);
  font-size:11px;
  letter-spacing:.14em;
  text-transform:uppercase;
  line-height:1;
}
.field-input{
  min-height:48px;
  width:100%;
  padding:0 16px;
  border-radius:16px;
  border:1px solid rgba(232,214,184,.12);
  background:linear-gradient(180deg, rgba(37,32,25,.96), rgba(19,17,13,.98));
  color:var(--text);
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,.03),
    0 1px 0 rgba(0,0,0,.18);
  transition:
    border-color .25s var(--ease-smooth),
    background .25s var(--ease-smooth),
    box-shadow .25s var(--ease-smooth),
    transform .25s var(--ease-smooth),
    opacity .25s var(--ease-smooth);
}
.field-input::placeholder{color:var(--muted-soft)}
.field-input:hover{
  border-color:rgba(233,201,143,.24);
  background:linear-gradient(180deg, rgba(43,38,30,.98), rgba(22,19,15,1));
}
.field-input:focus{
  outline:none;
  border-color:rgba(246,222,174,.42);
  box-shadow:
    0 0 0 4px rgba(233,201,143,.08),
    inset 0 1px 0 rgba(255,255,255,.03);
}
.field-input:disabled{
  opacity:.55;
  cursor:not-allowed;
}
.field-meta{
  padding-left:2px;
  color:var(--muted-soft);
  font-size:.78rem;
  line-height:1.45;
}
.search-field .field-input{
  padding-left:44px;
  padding-right:16px;
}
.search-field .field-icon{
  position:absolute;
  left:16px;
  bottom:15px;
  width:16px;
  height:16px;
  color:var(--muted);
  pointer-events:none;
}
.search-field .field-icon svg{
  display:block;
  width:100%;
  height:100%;
}
.select-field{position:relative}
.select-field::after{
  content:"";
  position:absolute;
  right:16px;
  bottom:19px;
  width:9px;
  height:9px;
  border-right:1.5px solid var(--muted);
  border-bottom:1.5px solid var(--muted);
  transform:rotate(45deg);
  transform-origin:center;
  pointer-events:none;
  transition:
    transform .25s var(--ease-smooth),
    border-color .25s var(--ease-smooth),
    opacity .25s var(--ease-smooth);
  opacity:.9;
}
.select-field:focus-within::after{
  border-color:var(--accent);
  transform:rotate(225deg);
}
.select-field.custom-select.open::after{
  border-color:var(--accent);
  transform:rotate(225deg);
}
.native-select{display:none}
.select-trigger{
  display:flex;
  align-items:center;
  justify-content:flex-start;
  padding-right:44px;
  text-align:left;
  cursor:pointer;
}
.select-trigger-text{
  flex:1;
  min-width:0;
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:nowrap;
}
.custom-select.open .select-trigger{
  border-color:rgba(246,222,174,.42);
  box-shadow:
    0 0 0 4px rgba(233,201,143,.08),
    inset 0 1px 0 rgba(255,255,255,.03);
}
select.field-input{
  appearance:none;
  -webkit-appearance:none;
  -moz-appearance:none;
  padding-right:44px;
  cursor:pointer;
}
select.field-input option{
  background:#17130f;
  color:var(--text);
}
input.field-input[type="search"]::-webkit-search-decoration,
input.field-input[type="search"]::-webkit-search-cancel-button{
  -webkit-appearance:none;
  appearance:none;
}
input.field-input[type="number"]{
  appearance:textfield;
  -moz-appearance:textfield;
}
input.field-input[type="number"]::-webkit-outer-spin-button,
input.field-input[type="number"]::-webkit-inner-spin-button{
  -webkit-appearance:none;
  margin:0;
}

.action-quiet,
.action-primary,
.tab,
.seg-btn,
.menu-item,
.action-quiet,
.action-primary{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  gap:8px;
  width:auto;
  cursor:pointer;
  white-space:nowrap;
  transition:
    border-color .25s var(--ease-smooth),
    background .25s var(--ease-smooth),
    color .25s var(--ease-smooth),
    transform .25s var(--ease-smooth),
    box-shadow .25s var(--ease-smooth),
    opacity .25s var(--ease-smooth);
}
.action-quiet{
  min-height:42px;
  padding:0 14px;
  border-radius:14px;
  border:1px solid rgba(232,214,184,.1);
  background:rgba(17,15,12,.38);
  color:var(--muted);
}
.action-quiet:hover{
  border-color:rgba(233,201,143,.18);
  background:rgba(24,21,17,.56);
  color:var(--text-soft);
}
.action-primary{
  min-height:44px;
  padding:0 16px;
  border-radius:14px;
  border:1px solid rgba(246,222,174,.18);
  background:linear-gradient(180deg, var(--accent-strong), #dcb778);
  color:var(--accent-ink);
  font-weight:620;
}
.action-primary:hover{
  background:linear-gradient(180deg, #f7e2bb, #e0bd7e);
}
.action-quiet.danger:hover{
  color:var(--danger);
  border-color:rgba(241,164,152,.26);
  background:rgba(47,22,18,.48);
}
button:active:not(:disabled),
.tab:active:not(:disabled),
.menu-item:active:not(:disabled){
  transform:translateY(1px) scale(0.98);
}
.action-quiet:disabled,
.action-primary:disabled,
.seg-btn:disabled,
.menu-item:disabled{
  opacity:.48;
  cursor:not-allowed;
  transform:none;
  box-shadow:none;
}
.action-quiet.compact,
.action-primary.compact{
  min-height:36px;
  padding:0 12px;
  border-radius:12px;
  font-size:.82rem;
}
.action-split{
  position:relative;
  display:flex;
  align-items:stretch;
  min-width:min(100%,260px);
}
.action-split .action-primary{
  border-radius:16px 0 0 16px;
}
.action-split .split-main{
  justify-content:flex-start;
  min-width:240px;
  padding:0 18px;
}
.split-main-label{
  display:grid;
  justify-items:start;
  gap:2px;
  line-height:1.08;
}
.split-main-title{font-weight:650}
.split-main-note{
  font-size:.72rem;
  font-weight:540;
  opacity:.8;
}
    .action-split .split-trigger{
      min-width:50px;
      padding:0 14px;
      border-left:1px solid rgba(35,24,10,.14);
      border-radius:0 16px 16px 0;
    }
    
.menu-wrap{
  position:relative;
  display:inline-flex;
}
.menu-toggle{
  display:inline-flex;
  align-items:center;
  gap:8px;
}
.menu-caret{
  width:8px;
  height:8px;
  border-right:1.5px solid currentColor;
  border-bottom:1.5px solid currentColor;
  transform:rotate(45deg);
  transform-origin:center;
  transition:transform .25s var(--ease-smooth),opacity .25s var(--ease-smooth);
}
[data-menu-id].open > .menu-toggle .menu-caret,
[data-menu-id].open > .seg-btn .menu-caret,
[data-menu-id].open > .split-trigger .menu-caret{
  transform:rotate(225deg);
}
.menu-panel{
  position:absolute;
  top:calc(100% + 10px);
  right:0;
  z-index:60;
  min-width:220px;
  padding:8px;
  border:1px solid rgba(232,214,184,.14);
  border-radius:18px;
  background:rgba(20,17,13,.98);
  box-shadow:0 22px 44px rgba(0,0,0,.34);
  backdrop-filter:blur(14px);
  display:grid;
  gap:4px;
  opacity:0;
  visibility:hidden;
  transform:translateY(-6px);
  transition:
    opacity .2s var(--ease-smooth),
    transform .2s var(--ease-smooth),
    visibility .2s var(--ease-smooth);
}
.menu-panel.align-left{
  left:0;
  right:auto;
}
.menu-panel.upward{
  top:auto;
  bottom:calc(100% + 10px);
}
[data-menu-id].open .menu-panel{
  opacity:1;
  visibility:visible;
  transform:translateY(0);
}
.select-menu{
  left:0;
  right:auto;
  width:max-content;
  min-width:100%;
  max-width:min(420px, calc(100vw - 32px));
  max-height:min(320px, 42vh);
  overflow:auto;
}
.select-menu .menu-item{
  min-height:44px;
  padding:10px 12px;
  justify-content:flex-start;
  align-items:flex-start;
  text-align:left;
  line-height:1.5;
  white-space:normal;
}
.menu-item{
  min-height:40px;
  padding:0 12px;
  border:none;
  border-radius:12px;
  background:transparent;
  color:var(--text-soft);
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:12px;
  cursor:pointer;
  transition:background .2s var(--ease-smooth),color .2s var(--ease-smooth);
}
.menu-item:hover{
  background:rgba(233,201,143,.08);
  color:var(--text);
}
.menu-item.active{
  background:rgba(233,201,143,.12);
  color:var(--accent-strong);
}
.menu-item--check::before{
  content:"";
  display:inline-block;
  width:1em;
  margin-right:6px;
  flex-shrink:0;
}
.menu-item--check.active::before{
  content:"✓";
}
.menu-divider{
  height:1px;
  margin:4px 0;
  background:rgba(232,214,184,.08);
}
.menu-note{
  padding:6px 12px 2px;
  color:var(--muted);
  font-size:.78rem;
  line-height:1.5;
}

.segmented{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  padding:6px;
  border:1px solid var(--border);
  border-radius:18px;
  background:rgba(15,13,10,.55);
}
.seg-btn{
  min-height:40px;
  padding:0 14px;
  border:none;
  border-radius:999px;
  background:transparent;
  color:var(--muted);
  display:inline-flex;
  align-items:center;
  justify-content:center;
  gap:8px;
  cursor:pointer;
  transition:
    background .25s var(--ease-smooth),
    color .25s var(--ease-smooth),
    box-shadow .25s var(--ease-smooth),
    transform .25s var(--ease-smooth);
}
.seg-btn:hover{
  background:rgba(255,255,255,.035);
  color:var(--text-soft);
}
.seg-btn.active,
.seg-btn.is-subactive,
[data-menu-id].open > .seg-btn{
  background:rgba(233,201,143,.14);
  box-shadow:inset 0 0 0 1px rgba(233,201,143,.14);
  color:var(--text);
}
.seg-btn-note{
  color:var(--muted-soft);
  font-size:.8rem;
}
.seg-btn.active .seg-btn-note,
.seg-btn.is-subactive .seg-btn-note{
  color:var(--accent);
}

.tabs{
  position:sticky;
  top:14px;
  z-index:20;
  display:block;
  margin-bottom:20px;
  padding:12px;
  border:1px solid var(--border);
  border-radius:24px;
  background:rgba(20,18,14,.9);
  backdrop-filter:blur(10px);
  box-shadow:var(--shadow-soft);
}
.tab-groups{
  display:flex;
  flex-wrap:wrap;
  gap:12px;
  align-items:stretch;
}
.tab-group{
  display:flex;
  align-items:center;
  gap:6px;
  min-height:52px;
  padding:4px;
  border:1px solid rgba(232,214,184,.08);
  border-radius:999px;
  background:rgba(12,10,8,.42);
}
.tab-group-title{
  padding:0 12px;
  color:var(--muted);
  font-family:var(--font-mono);
  font-size:10px;
  letter-spacing:.12em;
  text-transform:uppercase;
  white-space:nowrap;
}
.tab-group-row{
  display:flex;
  flex-wrap:wrap;
  gap:4px;
}
.tab{
  display:inline-flex;
  align-items:center;
  gap:8px;
  min-height:40px;
  padding:0 15px;
  border:none;
  border-radius:999px;
  background:transparent;
  color:var(--muted);
  cursor:pointer;
  font-weight:560;
  transition:background .25s var(--ease-smooth),color .25s var(--ease-smooth),transform .25s var(--ease-smooth);
}
.tab:hover{
  background:rgba(255,255,255,.035);
  color:var(--text);
}
.tab.active{
  background:rgba(233,201,143,.14);
  color:var(--text);
  box-shadow:inset 0 0 0 1px rgba(233,201,143,.16);
}
.tab-count{
  color:var(--accent);
  font-size:.82rem;
}

.empty{
  grid-column:1/-1;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  gap:0;
  min-height:300px;
  color:var(--muted);
  font-size:1.05rem;
  letter-spacing:0.02em;
}
.empty span { margin-top: -30px; opacity: 0.8; }
.cards{
  display:grid;
  grid-template-columns:repeat(3,minmax(0,1fr));
  gap:18px;
  align-items:stretch;
}
.card,
.update-card,
.compare-card{
  display:flex;
  flex-direction:column;
  gap:16px;
  padding:22px;
  border-radius:22px;
  border:1px solid rgba(232,214,184,.1);
  background:linear-gradient(180deg, rgba(29,26,21,.95), rgba(21,19,15,.98));
  box-shadow:var(--shadow-soft);
  transition:border-color .25s var(--ease-smooth),transform .25s var(--ease-smooth),box-shadow .25s var(--ease-smooth),background .25s var(--ease-smooth);
}
.card.selectable,
.update-card.selectable{cursor:pointer}
.card.selectable:focus-visible,
.update-card.selectable:focus-visible{
  outline:none;
  box-shadow:0 0 0 3px rgba(227,198,145,.16);
}
.card.selectable:hover,
.update-card.selectable:hover{
  transform:translateY(-2px);
  border-color:rgba(246,222,174,.18);
  box-shadow:0 18px 36px rgba(0,0,0,.22);
}
.card.selectable:active,
.update-card.selectable:active{
  transform:translateY(0) scale(0.99);
  transition-duration:.1s;
}
.card.selected,
.update-card.selected{
  background:
    radial-gradient(ellipse at top right, rgba(233,201,143,.12), transparent 60%),
    linear-gradient(180deg, rgba(37,30,20,.96), rgba(21,19,15,.98));
  border-color:rgba(233,201,143,.45);
  box-shadow:
    0 0 0 1px rgba(233,201,143,.2) inset,
    0 24px 44px rgba(0,0,0,.32);
}
.card-head{
  display:flex;
  justify-content:space-between;
  gap:12px;
  align-items:flex-start;
}
.card-body{
  display:flex;
  flex-direction:column;
  gap:14px;
  flex:1;
}
.card-title-wrap{
  display:grid;
  gap:10px;
  min-width:0;
}
.card-topline{
  display:flex;
  justify-content:space-between;
  gap:14px;
  align-items:flex-start;
}
.card-footer{
  margin-top:auto;
  display:grid;
  gap:12px;
  padding-top:16px;
  border-top:1px solid rgba(232,214,184,.08);
}
.card-metrics,
.card-state-actions,
.card-utility-actions{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  align-items:center;
}
.card-state-row{
  display:flex;
  flex-wrap:wrap;
  gap:12px;
  align-items:flex-start;
  justify-content:space-between;
}
.state-chip{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  min-height:34px;
  padding:0 12px;
  border-radius:999px;
  border:1px solid rgba(232,214,184,.1);
  background:rgba(15,13,10,.3);
  color:var(--muted);
  cursor:pointer;
  transition:
    border-color .25s var(--ease-smooth),
    background .25s var(--ease-smooth),
    color .25s var(--ease-smooth),
    transform .25s var(--ease-smooth);
}
.state-chip:hover{
  border-color:rgba(233,201,143,.18);
  background:rgba(233,201,143,.08);
  color:var(--text-soft);
}
.state-chip.active{
  border-color:rgba(233,201,143,.24);
  background:rgba(233,201,143,.14);
  color:var(--text);
}
    
.badges{gap:6px}
.badge{
  display:inline-flex;
  align-items:center;
  gap:4px;
  min-height:24px;
  padding:0 8px;
  border-radius:999px;
  border:1px solid rgba(232,214,184,.12);
  background:rgba(13,11,8,.48);
  color:var(--muted);
  font-size:.72rem;
  letter-spacing:.05em;
  text-transform:uppercase;
}
.badge.gain{
  color:var(--green);
  border-color:rgba(127,208,160,.18);
  background:rgba(127,208,160,.07);
}
.badge.source{
  color:var(--amber);
  border-color:rgba(216,175,103,.18);
  background:rgba(216,175,103,.06);
}
@keyframes pop-badge {
  0% { transform: scale(0.85); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}
.badge-selection{
  color:var(--accent);
  border-color:rgba(233,201,143,.22);
  background:rgba(233,201,143,.08);
  animation: pop-badge .25s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}
.title{
  display:block;
  margin:6px 0 0;
  color:var(--text);
  font-size:1.12rem;
  line-height:1.28;
  letter-spacing:-.02em;
  font-weight:650;
  overflow-wrap:anywhere;
  word-break:normal;
  transition:color .25s var(--ease-smooth);
}
.title:hover{color:var(--accent-strong)}
.meta-rank{
  color:rgba(233,201,143,.64);
  white-space:nowrap;
}
.desc-wrap{position:relative;min-width:0}
.desc{
  margin:0;
  color:var(--text-soft);
  font-size:.91rem;
  line-height:1.68;
  display:-webkit-box;
  -webkit-line-clamp:4;
  -webkit-box-orient:vertical;
  overflow:hidden;
}
.desc.muted{color:var(--muted)}
.desc-popover{
  position:absolute;
  left:-10px;
  right:-10px;
  bottom:calc(100% + 6px);
  padding:14px 16px;
  border:1px solid rgba(232,214,184,.14);
  border-radius:16px;
  background:rgba(16,14,11,.98);
  color:var(--text-soft);
  box-shadow:0 12px 32px rgba(0,0,0,.42);
  opacity:0;
  visibility:hidden;
  transform:translateY(6px);
  transition:opacity .2s var(--ease-smooth),transform .2s cubic-bezier(0.34, 1.56, 0.64, 1),visibility .2s var(--ease-smooth);
  pointer-events:none;
  z-index:26;
  max-height:min(260px,42vh);
  overflow:auto;
}
.desc-wrap:hover .desc-popover,
.desc-wrap:focus-within .desc-popover{
  opacity:1;
  visibility:visible;
  transform:translateY(0);
  pointer-events:auto;
}
.meta-line{
  gap:10px;
  align-items:flex-start;
}
.meta-pill{
  display:inline-flex;
  align-items:center;
  gap:6px;
  min-height:32px;
  padding:0 10px;
  border-radius:999px;
  border:1px solid rgba(232,214,184,.1);
  background:rgba(14,12,10,.54);
  font-size:.82rem;
  color:var(--text-soft);
}
.meta-pill strong{
  color:var(--muted);
  font-size:10px;
  letter-spacing:.08em;
  text-transform:uppercase;
}
.empty-icon{
  width:48px;
  height:48px;
  opacity:.42;
  color:var(--muted);
}
.notice{
  padding:16px 18px;
  border-radius:18px;
  border:1px solid rgba(232,214,184,.12);
  background:rgba(18,16,13,.84);
  color:var(--text-soft);
  font-size:.9rem;
  line-height:1.72;
}
.toast{
  position:fixed;
  right:20px;
  bottom:calc(26px + env(safe-area-inset-bottom, 0px));
  max-width:min(420px,calc(100vw - 32px));
  padding:14px 16px;
  border-radius:16px;
  border:1px solid rgba(233,201,143,.18);
  background:rgba(20,17,13,.96);
  color:var(--text);
  box-shadow:var(--shadow);
  opacity:0;
  transform:translateY(16px);
  transition:opacity .3s var(--ease-smooth),transform .3s var(--ease-smooth);
  pointer-events:none;
  z-index:70;
}
.toast.show{
  opacity:1;
  transform:translateY(0);
}

.batch-dock{
  position:fixed;
  left:50%;
  bottom:18px;
  z-index:45;
  display:grid;
  grid-template-columns:auto minmax(0,1fr);
  align-items:center;
  gap:10px 14px;
  width:min(980px,calc(100vw - 28px));
  padding:12px 14px;
  border:1px solid rgba(232,214,184,.14);
  border-radius:22px;
  background:rgba(17,15,12,.74);
  backdrop-filter:blur(14px);
  box-shadow:0 20px 44px rgba(0,0,0,.34);
  opacity:0;
  visibility:hidden;
  transform:translate(-50%,18px);
  transition:opacity .25s var(--ease-smooth),transform .25s var(--ease-smooth),visibility .25s var(--ease-smooth);
  max-width:calc(100vw - 24px);
}
.batch-dock.show{
  opacity:1;
  visibility:visible;
  transform:translate(-50%,0);
}
.batch-dock-meta{
  display:flex;
  align-items:center;
  gap:10px;
  min-height:46px;
  padding:0 12px 0 4px;
  border-right:1px solid rgba(232,214,184,.08);
}
.batch-dock-count{
  display:grid;
  gap:2px;
}
.batch-dock-actions{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  align-items:center;
  min-width:0;
}
.batch-divider{
  width:1px;
  height:16px;
  background:var(--border);
  margin:0 2px;
}
.batch-dock-label{
  color:var(--muted);
  font-size:10px;
  letter-spacing:.14em;
  text-transform:uppercase;
  line-height:1;
}
    .batch-dock-value{
      color:var(--text);
      font-size:.94rem;
      line-height:1.2;
    }
    
.overlay{
  position:fixed;
  inset:0;
  opacity:0;
  visibility:hidden;
  background:rgba(6,5,4,.54);
  backdrop-filter:blur(6px);
  z-index:50;
  transition:opacity .3s var(--ease-smooth),visibility .3s var(--ease-smooth);
}
.overlay.show{
  opacity:1;
  visibility:visible;
}
.panel{
  position:absolute;
  top:0;
  right:0;
  bottom:0;
  width:min(620px,100vw);
  background:linear-gradient(180deg, rgba(21,18,14,.98), rgba(15,13,10,1));
  border-left:1px solid rgba(232,214,184,.12);
  box-shadow:-24px 0 52px rgba(0,0,0,.32);
  display:flex;
  flex-direction:column;
  transform:translateX(100%);
  transition:transform .35s var(--ease-smooth);
}
.overlay.show .panel{transform:translateX(0)}
.overlay.compare .panel{width:min(760px,100vw)}
.overlay.settings .panel{width:min(560px,100vw)}
.panel-head{
  position:sticky;
  top:0;
  z-index:1;
  padding:26px 24px 18px;
  border-bottom:1px solid rgba(232,214,184,.1);
  background:linear-gradient(180deg, rgba(21,18,14,.98), rgba(18,16,13,.92));
  backdrop-filter:blur(12px);
  display:grid;
  grid-template-columns:minmax(0,1fr) auto;
  gap:16px;
  align-items:start;
}
.panel-title{
  margin:0 0 8px;
  font-size:1.5rem;
  line-height:1.08;
  letter-spacing:-.03em;
  font-weight:650;
}
.panel-body{
  padding:22px 24px 32px;
  overflow-y:auto;
  display:grid;
  gap:18px;
}
.detail-hero,
.detail-section{
  display:grid;
  gap:12px;
}
.detail-section{
  padding-top:18px;
  border-top:1px solid rgba(232,214,184,.08);
}
.section-label{
  color:var(--muted);
  font-family:var(--font-mono);
  font-size:10px;
  letter-spacing:.14em;
  text-transform:uppercase;
}
.settings-grid,
.settings-form{
  display:grid;
  gap:14px;
}
.settings-inline{
  display:grid;
  grid-template-columns:repeat(3,minmax(0,1fr));
  gap:14px;
}
.switch-row{
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:18px;
  padding:16px 18px;
  border:1px solid rgba(232,214,184,.12);
  border-radius:18px;
  background:rgba(18,16,13,.72);
}
.switch-copy{
  display:grid;
  gap:4px;
}
.switch-title{
  font-size:.98rem;
  font-weight:620;
  line-height:1.3;
}
.switch-desc{
  color:var(--muted);
  font-size:.84rem;
  line-height:1.55;
}
.switch{
  position:relative;
  display:inline-flex;
  align-items:center;
  cursor:pointer;
}
.switch input{
  position:absolute;
  opacity:0;
  pointer-events:none;
}
.switch-track{
  width:54px;
  height:32px;
  padding:3px;
  border-radius:999px;
  background:rgba(12,10,8,.65);
  border:1px solid rgba(232,214,184,.16);
  display:inline-flex;
  align-items:center;
  transition:
    background .25s var(--ease-smooth),
    border-color .25s var(--ease-smooth),
    box-shadow .25s var(--ease-smooth);
}
.switch-thumb{
  width:24px;
  height:24px;
  border-radius:999px;
  background:rgba(242,235,223,.88);
  box-shadow:0 4px 10px rgba(0,0,0,.25);
  transition:transform .25s var(--ease-smooth),background .25s var(--ease-smooth);
}
.switch input:focus + .switch-track{
  box-shadow:0 0 0 4px rgba(233,201,143,.08);
}
.switch input:checked + .switch-track{
  background:rgba(233,201,143,.18);
  border-color:rgba(233,201,143,.28);
}
.switch input:checked + .switch-track .switch-thumb{
  transform:translateX(22px);
  background:var(--accent-strong);
}
.detail-grid{
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  gap:18px 12px;
}
.compare-grid{
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  gap:16px;
}
.detail-item{
  display:flex;
  flex-direction:column;
  gap:4px;
}
.detail-item strong{
  display:block;
  margin-bottom:0;
  color:var(--muted);
  font-size:.75rem;
  letter-spacing:.12em;
  text-transform:uppercase;
}
.detail-item span{
  color:var(--text-soft);
  font-size:.92rem;
  line-height:1.55;
}
.topic{
  display:inline-flex;
  align-items:center;
  min-height:28px;
  padding:0 10px;
  border-radius:999px;
  background:rgba(233,201,143,.08);
  border:1px solid rgba(233,201,143,.12);
  color:var(--text-soft);
  font-size:.8rem;
}
.link-inline{
  color:var(--accent-strong);
  text-decoration:underline;
  text-underline-offset:3px;
}
.link-inline:hover{color:var(--text)}
.readme-block{
  padding:18px;
  border-radius:20px;
  border:1px solid rgba(232,214,184,.1);
  background:rgba(13,11,9,.38);
  color:var(--text-soft);
  font-size:.92rem;
  line-height:1.72;
}

@media (min-width:1600px){
  .cards{grid-template-columns:repeat(4,minmax(0,1fr))}
}
@media (max-width:1399px){
  .masthead{
    grid-template-columns:1fr;
  }
}
@media (max-width:1199px){
  .toolbar-main{grid-template-columns:1fr}
  .toolbar-filters{grid-template-columns:1fr 1fr}
  .discover-grid{grid-template-columns:1fr 1fr}
  .discover-top-grid{grid-template-columns:repeat(3,minmax(0,1fr))}
  .cards{grid-template-columns:repeat(2,minmax(0,1fr))}
  .compare-grid{grid-template-columns:1fr}
}
@media (max-width:959px){
  .page{padding:18px 14px 136px}
  .toolbar-filters,
  .settings-inline,
  .discover-grid,
  .discover-top-grid{
    grid-template-columns:1fr;
  }
  .nav-actions{
    justify-content:flex-start;
  }
  .tab-group{
    width:100%;
    justify-content:space-between;
  }
  .tab-group-row{
    flex:1;
  }
  .panel{
    width:100vw;
  }
}
@media (max-width:759px){
  .page{padding:16px 12px 146px}
  .masthead-copy,
  .masthead-side,
  .control-shell,
  .tabs,
  .card,
  .update-card,
  .compare-card{border-radius:20px}
  .masthead-title-row{
    align-items:flex-start;
  }
  .masthead-title{
    font-size:clamp(1.95rem,11vw,3rem);
  }
  .tabs{top:10px}
  .cards{grid-template-columns:1fr}
  .toolbar-utility{width:100%}
  .action-split{width:100%}
  .action-split .split-main{
    min-width:0;
    flex:1;
  }
  .detail-grid{grid-template-columns:1fr}
  .card-topline,
  .card-state-row{
    flex-direction:column;
    align-items:flex-start;
  }
  .card-metrics,
  .card-state-actions,
  .card-utility-actions{
    width:100%;
  }
  .panel-head,
  .panel-body{
    padding-left:20px;
    padding-right:20px;
  }
  .batch-dock{
    left:12px;
    right:12px;
    width:auto;
    grid-template-columns:1fr;
    transform:translateY(18px);
  }
  .batch-dock.show{transform:translateY(0)}
  .batch-dock-meta{
    width:100%;
    padding:0 0 10px;
    border-right:none;
    border-bottom:1px solid rgba(232,214,184,.08);
  }
  .batch-dock-actions{
    overflow-x:auto;
    flex-wrap:nowrap;
    padding-bottom:2px;
  }
  .batch-dock-actions > *{
    flex:0 0 auto;
  }
  .batch-divider{
    display:none;
  }
}
@media (prefers-reduced-motion:reduce){
  *,
  *::before,
  *::after{
    animation:none !important;
    transition:none !important;
    scroll-behavior:auto !important;
  }
}
@keyframes card-enter {
  0% { opacity: 0; transform: translateY(8px); }
  100% { opacity: 1; transform: translateY(0); }
}
.card, .update-card {
  animation: card-enter 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

@media (max-width:1000px){
  .batch-dock-label{
    display:block;
  }
  .batch-dock button{
    font-size:inherit;
  }
  .batch-dock button::before{
    content:none !important;
  }
}

body.has-batch-dock .toast{
  bottom:calc(118px + env(safe-area-inset-bottom, 0px));
}
"""
