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
  --muted:#a89b84;
  --muted-soft:#8f826d;
  --accent:#e3c691;
  --accent-strong:#f1d8aa;
  --accent-ink:#23180a;
  --green:#7fd0a0;
  --amber:#d7b171;
  --danger:#f1a498;
  --shadow-soft:0 1px 0 rgba(255,255,255,.025) inset, 0 10px 24px rgba(0,0,0,.16), 0 2px 8px rgba(0,0,0,.12);
  --shadow:0 1px 0 rgba(255,255,255,.03) inset, 0 18px 38px rgba(0,0,0,.24), 0 4px 14px rgba(0,0,0,.16);
  --shadow-lift:0 1px 0 rgba(255,255,255,.04) inset, 0 26px 56px rgba(0,0,0,.36), 0 8px 24px rgba(0,0,0,.22);
  --lh-tight:1.2;
  --lh-heading:1.08;
  --lh-base:1.5;
  --lh-copy:1.62;
  --lh-relaxed:1.7;
  --cluster-bar-end:rgba(127,208,160,.7);
}
*{box-sizing:border-box}
html,body{height:100%}
[hidden]{display:none !important}
body{
  margin:0;
  color:var(--text);
  background:
    radial-gradient(circle at top left, rgba(227,198,145,.08), transparent 0 34%),
    linear-gradient(180deg,#100f0c 0%,#14120f 50%,#15130f 100%);
  font-family:var(--font-sans);
  font-size:15px;
  line-height:var(--lh-relaxed);
  text-rendering:optimizeLegibility;
  font-kerning:normal;
  -webkit-font-smoothing:antialiased;
  -moz-osx-font-smoothing:grayscale;
}
button,input,select,textarea{font:inherit}
a{color:inherit;text-decoration:none}
:focus-visible{
  outline:2px solid transparent;
  box-shadow:0 0 0 3px rgba(227,198,145,.32);
}
::selection{background:rgba(227,198,145,.22);color:var(--text)}

::-webkit-scrollbar{width:8px;height:8px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{
  background:rgba(232,214,184,.14);
  border-radius:999px;
  border:2px solid var(--bg);
}
::-webkit-scrollbar-thumb:hover{background:rgba(232,214,184,.24)}
::-webkit-scrollbar-corner{background:transparent}
/* slim scrollbar for horizontal-overflow containers */
.workspace-subnav-row::-webkit-scrollbar,
.batch-dock-actions::-webkit-scrollbar{height:4px}
@media (forced-colors:active){
  :focus-visible{outline:2px solid ButtonText;box-shadow:none}
  .card,.update-card,.compare-card{border:1px solid ButtonText}
  .badge,.state-chip,.topic,.reason-pill,.meta-pill,.repo-tag-chip,.summary-strip-item,.discover-chip,.discover-meta-card,.discover-cluster-node,.discover-progress-strip,.discover-feedback-card,.discover-results-toolbar,.discover-selection-bar,.action-quiet,.field-input,.panel-close-btn,.checkline{border:1px solid ButtonText}
  .batch-dock,.workspace-drawer,.panel{border:1px solid ButtonText}
}

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
  line-height:var(--lh-relaxed);
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
  line-height:var(--lh-base);
}
.nav-actions{
  display:flex;
  flex-wrap:wrap;
  gap:10px;
  align-items:center;
  justify-content:flex-end;
}

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
.status-label{
  color:var(--text-soft);
  font-size:10px;
  letter-spacing:.14em;
  text-transform:uppercase;
}
.status-value{
  min-width:0;
  color:var(--text-soft);
  font-size:.88rem;
  line-height:var(--lh-base);
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
  font-weight:600;
  letter-spacing:-.02em;
  line-height:var(--lh-base);
}
.sub{
  color:var(--muted);
  font-size:.84rem;
  line-height:var(--lh-copy);
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
}"""
