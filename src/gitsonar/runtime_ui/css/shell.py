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
  align-content:center;
  min-width:0;
}
.workspace-tagline{
  margin:4px 0 0;
  color:var(--muted);
  font-size:.78rem;
  letter-spacing:.08em;
  line-height:var(--lh-base);
}
.workspace-title{
  margin:0;
  font-size:clamp(1.72rem,3.2vw,2.7rem);
  line-height:.94;
  letter-spacing:-.06em;
  font-weight:720;
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
  border-top:2px solid rgba(233,201,143,.18);
}
.runtime-note{
  font-size:.9rem;
  line-height:var(--lh-base);
}
.workspace-nav,
.workspace-bar{
  position:relative;
  display:grid;
  gap:12px;
  overflow:visible;
}
.workspace-nav{
  margin-bottom:14px;
}
.workspace-bar{
  margin-bottom:18px;
}
.workspace-nav-shell{
  position:relative;
  display:grid;
  padding:0;
  overflow:visible;
}
.workspace-content-shell{
  --workspace-bar-emphasis-height:56px;
  position:relative;
  display:grid;
  gap:18px;
  padding:18px clamp(14px,1.5vw,20px) 18px;
  border:1px solid var(--border);
  border-radius:24px;
  background:linear-gradient(180deg, rgba(24,21,17,.94), rgba(18,16,13,.98));
  backdrop-filter:blur(12px);
  box-shadow:var(--shadow);
  overflow:visible;
}
.workspace-control-stack{
  position:relative;
  z-index:18;
  display:grid;
  gap:14px;
}
.workspace-context{
  position:relative;
  display:grid;
  gap:14px;
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
.workspace-primary-nav{
  display:flex;
  flex-wrap:wrap;
  gap:18px;
  align-items:center;
  min-height:42px;
  overflow:visible;
}
.workspace-primary-link{
  display:inline-flex;
  position:relative;
  align-items:center;
  gap:10px;
  min-height:42px;
  padding:0 0 6px;
  border:none;
  background:transparent;
  color:var(--muted);
  cursor:pointer;
  transition:
    color .25s var(--ease-smooth),
    opacity .25s var(--ease-smooth),
    transform .25s var(--ease-smooth);
}
.workspace-primary-link::after{
  content:"";
  position:absolute;
  left:0;
  right:0;
  bottom:0;
  height:2px;
  border-radius:999px;
  background:var(--accent);
  transform:scaleX(0);
  transform-origin:left center;
  opacity:0;
  transition:
    transform .25s var(--ease-smooth),
    opacity .25s var(--ease-smooth);
}
.workspace-primary-link:hover{
  color:var(--text-soft);
  opacity:.88;
}
.workspace-primary-link.active{
  color:var(--text);
  opacity:1;
}
.workspace-primary-link.active::after{
  transform:scaleX(1);
  opacity:1;
}
.workspace-primary-label{
  color:var(--text);
  font-size:clamp(1.02rem,1.45vw,1.24rem);
  font-weight:680;
  line-height:var(--lh-heading);
  white-space:nowrap;
}
.workspace-primary-count{
  color:color-mix(in srgb, var(--muted) 74%, var(--accent) 26%);
  font-family:var(--font-mono);
  font-size:.68rem;
  line-height:var(--lh-tight);
  opacity:.72;
  transition:opacity .2s var(--ease-smooth),color .2s var(--ease-smooth);
}
.workspace-primary-link:hover .workspace-primary-count{
  opacity:1;
  color:var(--accent);
}
.nav-menu-panel{
  min-width:220px;
}
.workspace-subnav{
  display:grid;
  gap:6px;
  padding-top:4px;
}
.workspace-subnav-row{
  display:flex;
  flex-wrap:wrap;
  gap:6px;
  align-items:center;
}
.workspace-subnav-link{
  display:inline-flex;
  align-items:center;
  gap:7px;
  min-height:32px;
  padding:0 10px;
  border:none;
  border-radius:12px;
  background:transparent;
  color:var(--muted);
  font-size:.84rem;
  white-space:nowrap;
  cursor:pointer;
  transition:
    background .25s var(--ease-smooth),
    color .25s var(--ease-smooth),
    opacity .25s var(--ease-smooth);
}
.workspace-subnav-link:hover{
  background:rgba(233,201,143,.06);
  color:var(--text-soft);
}
.workspace-subnav-link.active{
  background:rgba(233,201,143,.08);
  color:var(--text);
}
.workspace-subnav-label{
  font-weight:580;
}
.workspace-subnav-count{
  color:var(--muted);
  font-family:var(--font-mono);
  font-size:.66rem;
  opacity:.72;
}
.workspace-bar-main{
  display:grid;
  grid-template-columns:minmax(0,1fr) auto;
  gap:14px;
  align-items:center;
  position:relative;
  z-index:10;
}
.workspace-bar-main--discover{
  grid-template-columns:minmax(0,1fr);
  align-items:end;
}
.workspace-filter-group,
.workspace-action-group{
  display:flex;
  align-items:center;
  gap:10px;
  min-width:0;
}
.workspace-filter-group{
  justify-content:flex-start;
}
.workspace-action-group{
  justify-content:flex-end;
}
.workspace-search-wrap{
  flex:1 1 auto;
  min-width:0;
}
.workspace-filter-group .workspace-drawer-trigger{
  min-height:48px;
  padding:0 14px;
  border-radius:16px;
}
.workspace-summary{
  display:flex;
  align-items:center;
  justify-content:flex-end;
  min-width:0;
  padding:0;
  border:none;
  background:none;
  box-shadow:none;
}
.workspace-summary-copy{
  display:flex;
  align-items:center;
  min-width:0;
}
.workspace-summary-line{
  color:var(--text-soft);
  font-size:.84rem;
  line-height:var(--lh-tight);
  white-space:nowrap;
}
.workspace-summary-line .metric-number{
  color:var(--text);
}
.workspace-ai-target{
  max-width:18ch;
  color:var(--muted);
  font-size:.76rem;
  line-height:var(--lh-tight);
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
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
  box-shadow:var(--shadow);
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
  line-height:var(--lh-heading);
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
  border:1px solid transparent;
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
  line-height:var(--lh-tight);
  letter-spacing:-.03em;
  font-weight:650;
}
.workspace-empty-copy{
  max-width:72ch;
  color:var(--text-soft);
  font-size:.92rem;
  line-height:var(--lh-copy);
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
  border:1px solid transparent;
  border-radius:16px;
  background:rgba(13,11,9,.34);
  color:var(--text-soft);
  font-size:.88rem;
  line-height:var(--lh-copy);
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
  line-height:var(--lh-tight);
  display:-webkit-box;
  -webkit-line-clamp:2;
  -webkit-box-orient:vertical;
  overflow:hidden;
}
.desc{
  font-size:.87rem;
  line-height:var(--lh-copy);
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
}
.panel-close-btn{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  flex-shrink:0;
  width:44px;
  height:44px;
  padding:0;
  border-radius:12px;
  border:1px solid transparent;
  background:rgba(17,15,12,.38);
  color:var(--muted);
  cursor:pointer;
  transition:
    background .25s var(--ease-smooth),
    border-color .25s var(--ease-smooth),
    color .25s var(--ease-smooth),
    transform .25s var(--ease-smooth);
}
.panel-close-btn:hover{
  border-color:rgba(233,201,143,.18);
  background:rgba(24,21,17,.56);
  color:var(--text-soft);
  transform:rotate(90deg);
}
.panel-close-btn svg{
  display:block;
  width:16px;
  height:16px;
}
@media (forced-colors:active){
  .workspace-header,
  .workspace-content-shell,
  .workspace-drawer,
  .card,
  .update-card,
  .compare-card,
  .panel,
  .batch-dock,
  .badge,
  .state-chip,
  .topic,
  .reason-pill,
  .meta-pill,
  .repo-tag-chip,
  .summary-strip-item,
  .discover-chip,
  .discover-meta-card,
  .discover-cluster-node,
  .discover-progress-strip,
  .discover-feedback-card,
  .discover-results-toolbar,
  .discover-selection-bar,
  .action-quiet,
  .field-input,
  .panel-close-btn,
  .checkline{
    border:1px solid ButtonText;
  }
  .card.selected,
  .update-card.selected{
    box-shadow:0 0 0 1px Highlight inset;
  }
}
"""
