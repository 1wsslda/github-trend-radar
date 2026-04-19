#!/usr/bin/env python3
from __future__ import annotations

CSS = r""".page{
  max-width:1780px;
  padding:clamp(14px,1.9vw,24px) clamp(14px,1.6vw,24px) 140px;
}
.workspace-header{
  position:relative;
  display:grid;
  grid-template-columns:minmax(0,1fr) auto;
  gap:14px;
  margin-bottom:14px;
  padding:16px 18px;
  border:1px solid var(--border);
  border-radius:24px;
  background:linear-gradient(180deg, rgba(28,24,19,.94), rgba(16,14,11,.98));
  box-shadow:var(--shadow);
}
.workspace-brand,
.workspace-status{
  position:relative;
  z-index:1;
}
.workspace-brand{
  display:grid;
  gap:8px;
  min-width:0;
}
.workspace-title-row{
  display:flex;
  flex-wrap:wrap;
  align-items:flex-end;
  gap:10px 14px;
}
.workspace-title{
  margin:0;
  font-size:clamp(1.72rem,3.2vw,2.7rem);
  line-height:.94;
  letter-spacing:-.06em;
  font-weight:720;
}
.workspace-panel-meta{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  align-items:center;
  min-width:0;
}
.workspace-badge{
  display:inline-flex;
  align-items:center;
  min-height:26px;
  padding:0 10px;
  border-radius:999px;
  border:1px solid rgba(233,201,143,.14);
  background:rgba(233,201,143,.08);
  color:var(--accent-strong);
  font-family:var(--font-mono);
  font-size:.68rem;
  letter-spacing:.08em;
  text-transform:uppercase;
}
.workspace-panel-summary{
  min-width:0;
  color:var(--text-soft);
  font-size:.9rem;
  line-height:1.5;
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
}
.workspace-status{
  display:grid;
  grid-auto-flow:column;
  gap:12px;
  align-items:center;
  justify-content:end;
}
.status-card{
  gap:6px;
  min-width:min(100%,280px);
  padding:12px 14px;
  border-radius:18px;
  background:rgba(13,11,9,.5);
}
.runtime-note{
  font-size:.9rem;
  line-height:1.45;
}
.workspace-bar{
  position:relative;
  display:grid;
  gap:12px;
  margin-bottom:16px;
  overflow:visible;
}
.workspace-bar-shell{
  --workspace-bar-emphasis-height:56px;
  position:sticky;
  top:12px;
  z-index:18;
  display:grid;
  gap:12px;
  padding:12px 14px 14px;
  border:1px solid var(--border);
  border-radius:22px;
  background:rgba(20,18,14,.9);
  backdrop-filter:blur(12px);
  box-shadow:var(--shadow-soft);
  overflow:visible;
}
.workspace-context{
  position:relative;
  display:grid;
  gap:12px;
}
.tabs{
  position:relative;
  top:auto;
  z-index:42;
  display:block;
  margin:0;
  padding:0;
  border:none;
  border-radius:0;
  background:transparent;
  box-shadow:none;
  overflow:visible;
}
.nav-main{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  align-items:center;
  overflow:visible;
}
.nav-pill{
  display:inline-flex;
  align-items:center;
  gap:8px;
  min-height:34px;
  padding:0 12px;
  border-radius:999px;
  border:1px solid rgba(232,214,184,.1);
  background:rgba(15,13,10,.44);
  color:var(--muted);
  cursor:pointer;
  transition:
    background .25s var(--ease-smooth),
    border-color .25s var(--ease-smooth),
    color .25s var(--ease-smooth),
    transform .25s var(--ease-smooth);
}
.nav-pill:hover{
  color:var(--text-soft);
  background:rgba(255,255,255,.035);
}
.nav-pill.active,
[data-menu-id].open > .nav-pill{
  background:rgba(233,201,143,.14);
  border-color:rgba(233,201,143,.18);
  color:var(--text);
}
.nav-pill-label{
  max-width:16ch;
  color:var(--text);
  font-weight:620;
  line-height:1;
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
}
.nav-pill-note{
  max-width:16ch;
  color:var(--text-soft);
  font-size:.78rem;
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
}
.nav-count{
  color:var(--accent);
  font-family:var(--font-mono);
  font-size:.76rem;
}
.nav-menu-panel{
  min-width:220px;
}
.workspace-bar-main{
  display:grid;
  grid-template-columns:minmax(280px,1.2fr) auto auto auto;
  gap:10px;
  align-items:end;
  position:relative;
  z-index:10;
}
.workspace-bar-main--discover{
  grid-template-columns:minmax(0,1fr);
  align-items:end;
}
.workspace-search-wrap{
  min-width:0;
}
.workspace-summary{
  display:flex;
  align-items:center;
  justify-content:center;
  min-height:var(--workspace-bar-emphasis-height);
  min-width:168px;
  padding:8px 15px;
  border:1px solid rgba(232,214,184,.12);
  border-radius:16px;
  background:linear-gradient(180deg, rgba(37,32,25,.72), rgba(19,17,13,.88));
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,.03),
    0 1px 0 rgba(0,0,0,.18);
}
.workspace-summary-copy{
  display:grid;
  align-content:center;
  gap:3px;
  width:100%;
  min-width:0;
}
.workspace-summary .summary{
  font-size:.92rem;
  line-height:1.22;
}
.workspace-summary .sub{
  font-size:.76rem;
  line-height:1.2;
}
.workspace-drawer-trigger{
  min-width:90px;
}
.workspace-drawer-trigger.active{
  border-color:rgba(233,201,143,.2);
  background:rgba(233,201,143,.1);
  color:var(--text);
}
.workspace-drawer{
  position:relative;
  display:grid;
  gap:14px;
  padding:14px 16px;
  border:1px solid rgba(232,214,184,.1);
  border-radius:20px;
  background:rgba(17,14,11,.56);
  box-shadow:var(--shadow-soft);
}
.workspace-drawer-head{
  display:grid;
  grid-template-columns:minmax(0,1fr) auto;
  gap:12px;
  align-items:start;
}
.workspace-drawer-title{
  margin:0 0 6px;
  font-size:1.08rem;
  line-height:1.06;
  letter-spacing:-.02em;
  font-weight:650;
}
.workspace-drawer-body{
  display:grid;
  gap:16px;
}
.workspace-drawer #control-drawer-list{
  grid-template-columns:minmax(0,1.45fr) minmax(220px,.74fr) minmax(0,1.2fr);
  gap:14px;
  align-items:end;
}
.workspace-summary-strip{
  padding:2px 2px 0;
}
.summary-strip-row{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  align-items:center;
}
.summary-strip-label{
  color:var(--muted);
  font-family:var(--font-mono);
  font-size:10px;
  letter-spacing:.14em;
  text-transform:uppercase;
}
.summary-strip-item{
  display:inline-flex;
  align-items:center;
  min-height:26px;
  padding:0 10px;
  border-radius:999px;
  border:1px solid rgba(232,214,184,.1);
  background:rgba(15,13,10,.38);
  color:var(--text-soft);
  font-size:.8rem;
}
.summary-strip-item strong{
  color:var(--text);
  font-weight:620;
}
.canvas-intro{
  display:grid;
  gap:12px;
  margin-bottom:14px;
}
.workspace-empty-card{
  display:grid;
  gap:10px;
  padding:26px 28px;
  border:1px solid rgba(232,214,184,.1);
  border-radius:22px;
  background:linear-gradient(180deg, rgba(31,27,21,.95), rgba(19,17,13,.98));
  box-shadow:var(--shadow-soft);
}
.workspace-empty-kicker{
  color:var(--accent);
  font-family:var(--font-mono);
  font-size:10px;
  letter-spacing:.16em;
  text-transform:uppercase;
}
.workspace-empty-title{
  font-size:clamp(1.18rem,2vw,1.58rem);
  line-height:1.1;
  letter-spacing:-.03em;
  font-weight:650;
}
.workspace-empty-copy{
  max-width:72ch;
  color:var(--text-soft);
  font-size:.92rem;
  line-height:1.64;
}
.workspace-empty-copy strong{
  color:var(--text);
}
.workspace-empty-actions{
  display:flex;
  flex-wrap:wrap;
  gap:10px;
  align-items:center;
}
.drawer-section{
  display:grid;
  gap:14px;
}
.drawer-support{
  display:grid;
  gap:14px;
  padding-top:4px;
}
.drawer-support-block{
  display:grid;
  gap:10px;
}
.drawer-note{
  padding:14px 16px;
  border:1px solid rgba(232,214,184,.1);
  border-radius:16px;
  background:rgba(13,11,9,.34);
  color:var(--text-soft);
  font-size:.88rem;
  line-height:1.62;
}
.discover-chip{
  min-width:0;
}
.discover-top-grid{
  display:grid;
  grid-template-columns:repeat(3,minmax(0,1fr));
}
.discover-top-card{
  padding:12px 14px;
}
.field-input{
  min-height:42px;
  padding:0 14px;
  border-radius:14px;
}
.search-field .field-input{
  padding-left:42px;
}
.search-field .field-icon{
  left:14px;
  bottom:13px;
}
.action-quiet{
  min-height:40px;
  padding:0 13px;
  border-radius:12px;
}
.action-primary{
  min-height:42px;
  padding:0 14px;
  border-radius:13px;
}
.action-quiet.compact,
.action-primary.compact{
  min-height:32px;
  padding:0 10px;
}
.action-split .action-primary{
  border-radius:14px 0 0 14px;
}
.action-split .split-main{
  min-width:220px;
  padding:0 16px;
}
.action-split .split-trigger{
  min-width:46px;
  border-radius:0 14px 14px 0;
}
.segmented{
  gap:6px;
  padding:4px;
  border-radius:16px;
}
.seg-btn{
  min-height:34px;
  padding:0 12px;
}
.state-chip{
  min-height:30px;
  padding:0 10px;
}
.badge{
  min-height:22px;
  padding:0 7px;
  font-size:.68rem;
}
.cards{
  grid-template-columns:repeat(3,minmax(0,1fr));
  gap:14px;
}
.card,
.update-card,
.compare-card{
  gap:12px;
  padding:16px;
  border-radius:18px;
}
.card-body{
  gap:10px;
}
.card-title-wrap{
  gap:8px;
}
.card-topline{
  gap:10px;
}
.card-footer{
  gap:10px;
  padding-top:12px;
}
.card-metrics,
.card-state-actions,
.card-utility-actions{
  gap:6px;
}
.card-state-row{
  gap:10px;
}
.title{
  margin:2px 0 0;
  font-size:1rem;
  line-height:1.26;
  display:-webkit-box;
  -webkit-line-clamp:2;
  -webkit-box-orient:vertical;
  overflow:hidden;
}
.desc{
  font-size:.87rem;
  line-height:1.58;
  -webkit-line-clamp:3;
}
.meta-rank{
  font-size:.76rem;
}
.empty{
  min-height:220px;
  font-size:.96rem;
}
.panel-head{
  padding:22px 20px 16px;
}
.panel-body{
  gap:16px;
  padding:18px 20px 28px;
}"""
