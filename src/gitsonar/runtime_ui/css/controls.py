#!/usr/bin/env python3
from __future__ import annotations

CSS = r""".toolbar-filters{
  display:grid;
  grid-template-columns:minmax(0,1.45fr) minmax(220px,.74fr) minmax(0,1.2fr);
  gap:14px;
  align-items:end;
}

.discover-query-row{
  display:grid;
  gap:12px;
  align-items:stretch;
  min-width:0;
}
.discover-query-main{
  display:grid;
  grid-template-columns:minmax(0,1fr) minmax(240px,auto);
  gap:10px;
  align-items:stretch;
  min-width:0;
}
.discover-query-field{
  min-width:0;
  isolation:isolate;
}
.discover-query-field.is-open{
  z-index:47;
}
.discover-run-split{
  width:100%;
  min-width:0;
  isolation:isolate;
}
.discover-run-split .split-main{
  flex:1 1 auto;
  min-width:0;
}
.discover-run-split .split-main,
.discover-run-split .split-trigger{
  position:relative;
}
.discover-run-split .split-main:disabled,
.discover-run-split .split-trigger:disabled{
  opacity:1;
}
.discover-run-split.is-idle .split-main,
.discover-run-split.is-idle .split-trigger{
  border-color:rgba(221,193,145,.16);
  background:linear-gradient(180deg, rgba(160,137,99,.96), rgba(137,116,82,.98));
  color:rgba(35,24,10,.96);
  box-shadow:none;
}
.discover-run-split.is-idle .split-main-note{
  color:rgba(35,24,10,.72);
  opacity:1;
}
.discover-run-split.is-idle .split-main:disabled{
  cursor:not-allowed;
}
.discover-run-split.is-idle .split-trigger:hover,
[data-menu-id="discover-ranking-menu"].open.is-idle .split-trigger{
  border-color:rgba(246,222,174,.28);
  border-left-color:rgba(35,24,10,.18);
  background:linear-gradient(180deg, rgba(241,216,170,.98), rgba(226,196,136,.98));
  color:var(--accent-ink);
}
.discover-run-split.is-ready .split-main,
.discover-run-split.is-ready .split-trigger{
  border-color:rgba(246,222,174,.18);
  border-left-color:rgba(35,24,10,.14);
  color:var(--accent-ink);
}
.discover-run-split.is-busy .split-main,
.discover-run-split.is-busy .split-trigger{
  border-color:rgba(246,222,174,.16);
  border-left-color:rgba(35,24,10,.14);
  background:linear-gradient(180deg, rgba(236,211,163,.92), rgba(210,176,114,.94));
  color:rgba(35,24,10,.92);
  box-shadow:none;
}
.discover-run-split.is-busy .split-main-note{
  color:rgba(35,24,10,.74);
  opacity:1;
}
.discover-context{
  display:grid;
  gap:12px;
}
.discover-context-grid{
  display:grid;
  grid-template-columns:minmax(240px,.72fr) minmax(0,1fr);
  gap:12px;
  align-items:stretch;
}
.discover-limit-card{
  display:grid;
  gap:10px;
  padding:14px 16px;
  border:1px solid rgba(232,214,184,.1);
  border-radius:18px;
  background:rgba(14,12,10,.42);
}
.discover-limit-row{
  display:flex;
  flex-wrap:wrap;
  align-items:center;
  justify-content:space-between;
  gap:10px;
}
.discover-limit-copy{
  color:var(--text);
  font-size:.95rem;
  font-weight:620;
}
.discover-expand-card{
  width:100%;
  min-height:auto;
  background:rgba(14,12,10,.42);
}
.discover-filter-bar{
  display:flex;
  flex-wrap:wrap;
  align-items:center;
  gap:10px;
}
.discover-limit-field{
  width:112px;
  flex-shrink:0;
}
.discover-ranking-field{
  flex:1;
  min-width:0;
}
.discover-ranking-field .field-label{
  padding-left:0;
}
.discover-query-suggest{
  position:absolute;
  top:calc(100% + 12px);
  left:0;
  right:0;
  z-index:46;
  padding:10px;
  border:1px solid rgba(232,214,184,.14);
  border-radius:20px;
  background:linear-gradient(180deg, rgba(25,21,17,.98), rgba(16,14,11,.98));
  box-shadow:0 26px 52px rgba(0,0,0,.34);
  backdrop-filter:blur(16px);
  display:grid;
  gap:8px;
}
.discover-query-suggest-head{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:10px;
  padding:2px 4px 0;
}
.discover-query-suggest-kicker{
  color:var(--accent-strong);
  font-family:var(--font-mono);
  font-size:.68rem;
  letter-spacing:.14em;
  text-transform:uppercase;
}
.discover-query-suggest-note{
  color:var(--muted);
  font-size:.74rem;
  line-height:1.4;
}
.discover-query-suggest-list{
  display:grid;
  gap:4px;
}
.discover-query-suggest-item{
  width:100%;
  padding:12px 14px;
  border:1px solid transparent;
  border-radius:14px;
  background:rgba(255,255,255,.02);
  color:var(--text);
  display:grid;
  gap:8px;
  text-align:left;
  cursor:pointer;
  transition:
    border-color .25s var(--ease-smooth),
    background .25s var(--ease-smooth),
    transform .25s var(--ease-smooth);
}
.discover-query-suggest-item:hover{
  border-color:rgba(233,201,143,.16);
  background:rgba(233,201,143,.08);
}
.discover-query-suggest-title{
  font-size:.95rem;
  line-height:1.35;
  font-weight:620;
  word-break:break-word;
}
.discover-query-suggest-meta{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
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
.checkline--stacked{
  align-items:flex-start;
  gap:10px;
  min-height:48px;
  padding:12px 14px;
  border-radius:18px;
}
.checkline input{
  margin-top:2px;
  accent-color:var(--accent);
  flex:0 0 auto;
}
.checkline-copy{
  display:grid;
  gap:2px;
}
.checkline-title{
  color:var(--text);
  font-size:.88rem;
  line-height:1.3;
}
.checkline-note{
  color:var(--muted);
  font-size:.76rem;
  line-height:1.45;
}
.discover-panel,
.discover-meta,
.discover-top{
  display:grid;
  gap:10px;
}
.discover-chip{
  min-width:0;
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
.discover-inline-hint{
  display:flex;
  flex-wrap:wrap;
  gap:10px 12px;
  align-items:center;
  color:var(--muted);
  font-size:.9rem;
  line-height:1.6;
}
.discover-inline-hint strong{
  color:var(--text);
}
.discover-inline-hint--warning{
  padding:10px 12px;
  border:1px solid rgba(232,214,184,.1);
  border-radius:16px;
  background:rgba(17,14,11,.38);
}
.discover-inline-hint-actions{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  align-items:center;
}
.discover-progress-strip,
.discover-feedback-card,
.discover-results-toolbar,
.discover-selection-bar{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:12px 14px;
  padding:12px 14px;
  border:1px solid rgba(232,214,184,.1);
  border-radius:18px;
  background:rgba(14,12,10,.42);
}
.discover-progress-copy,
.discover-feedback-card,
.discover-results-toolbar-main,
.discover-selection-meta{
  min-width:0;
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  align-items:center;
}
.discover-progress-copy{
  display:flex;
  flex-wrap:wrap;
  gap:8px 12px;
  align-items:center;
}
.discover-progress-stage{
  color:var(--accent-strong);
  font-family:var(--font-mono);
  font-size:.72rem;
  letter-spacing:.12em;
  text-transform:uppercase;
}
.discover-progress-text,
.discover-progress-eta{
  color:var(--text-soft);
  font-size:.84rem;
}
.discover-progress-actions,
.discover-results-toolbar-actions,
.discover-selection-actions{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  align-items:center;
  justify-content:flex-end;
}
.discover-feedback-card{
  display:grid;
  justify-content:stretch;
}
.discover-feedback-card--error{
  border-color:rgba(241,164,152,.22);
  background:linear-gradient(180deg, rgba(46,24,21,.46), rgba(20,13,11,.9));
}
.discover-feedback-title{
  font-size:1rem;
  line-height:1.2;
  font-weight:620;
}
.discover-feedback-copy{
  color:var(--text-soft);
  font-size:.88rem;
  line-height:1.6;
}
.discover-feedback-actions{
  display:flex;
  flex-wrap:wrap;
  gap:10px;
  align-items:center;
}
.discover-diagnostic{
  display:grid;
  gap:8px;
}
.discover-diagnostic summary{
  color:var(--muted);
  cursor:pointer;
  font-size:.82rem;
}
.discover-diagnostic-copy{
  padding:10px 12px;
  border-radius:14px;
  background:rgba(12,10,8,.45);
  color:var(--text-soft);
  font-size:.82rem;
  line-height:1.55;
  overflow-wrap:anywhere;
}
.discover-results-toolbar{
  background:rgba(14,12,10,.34);
}
.discover-results-toolbar-main{
  display:grid;
  gap:8px;
}
.discover-results-toolbar-pills{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  align-items:center;
}
.discover-toolbar-note{
  color:var(--muted);
  font-size:.8rem;
  line-height:1.5;
}
.discover-toolbar-ai{
  color:var(--text-soft);
  font-size:.76rem;
  max-width:16ch;
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:nowrap;
}
.discover-selection-bar{
  background:rgba(23,19,15,.56);
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
input.field-input:-webkit-autofill,
input.field-input:-webkit-autofill:hover,
input.field-input:-webkit-autofill:focus{
  -webkit-text-fill-color:var(--text);
  box-shadow:0 0 0 1000px rgba(24,20,16,.98) inset;
  transition:background-color 9999s ease-out 0s;
}
.field-meta{
  padding-left:2px;
  color:var(--muted);
  font-size:.78rem;
  line-height:1.45;
}
.field-meta[data-state="checking"]{color:var(--accent)}
.field-meta[data-state="success"]{color:var(--green)}
.field-meta[data-state="insufficient"]{color:var(--amber)}
.field-meta[data-state="invalid"]{color:var(--danger)}
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
.select-field.custom-select::after{
  display:none;
}
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
  position:relative;
  display:flex;
  align-items:center;
  justify-content:flex-start;
  padding-right:44px;
  text-align:left;
  cursor:pointer;
}
.select-field.custom-select .select-trigger::after{
  content:"";
  position:absolute;
  right:16px;
  top:50%;
  width:9px;
  height:9px;
  border-right:1.5px solid var(--muted);
  border-bottom:1.5px solid var(--muted);
  transform:translateY(-62%) rotate(45deg);
  transform-origin:center;
  pointer-events:none;
  transition:
    transform .25s var(--ease-smooth),
    border-color .25s var(--ease-smooth),
    opacity .25s var(--ease-smooth);
  opacity:.9;
}
.select-trigger-text{
  flex:1;
  min-width:0;
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:nowrap;
}
.select-field.custom-select:focus-within .select-trigger::after,
.select-field.custom-select.open .select-trigger::after{
  border-color:var(--accent);
  transform:translateY(-38%) rotate(225deg);
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
button[aria-haspopup]:active:not(:disabled){
  transform:none;
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
.workspace-action-group > .action-split[data-menu-id="ai-target-menu"] .split-main,
.workspace-action-group > .action-split[data-menu-id="ai-target-menu"] .split-trigger{
  min-height:var(--workspace-bar-emphasis-height, 56px);
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

.workspace-header.menu-host-open,
.workspace-nav-shell.menu-host-open,
.workspace-content-shell.menu-host-open,
.workspace-control-stack.menu-host-open,
.workspace-bar-shell.menu-host-open,
.workspace-drawer.menu-host-open,
.panel.menu-host-open,
.batch-dock.menu-host-open{
  z-index:49;
}

.card.menu-host-open,
.card.desc-host-open,
.update-card.menu-host-open,
.update-card.desc-host-open,
.canvas-intro.menu-host-open{
  position:relative;
  z-index:48;
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
  max-width:min(360px, calc(100vw - 24px));
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
.menu-panel.menu-panel--measuring{
  opacity:0;
  visibility:hidden;
  transform:none;
  pointer-events:none;
  transition:none;
}
.menu-panel.align-left{
  left:0;
  right:auto;
}
.menu-panel.align-right{
  left:auto;
  right:0;
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
  justify-content:flex-start;
  gap:12px;
  text-align:left;
  cursor:pointer;
  transition:background .2s var(--ease-smooth),color .2s var(--ease-smooth);
}
.menu-item-copy{
  display:grid;
  flex:1;
  gap:2px;
  justify-items:start;
  min-width:0;
}
.menu-item-meta{
  color:var(--muted);
  font-size:.74rem;
  line-height:1.45;
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
  display:inline-flex;
  align-items:center;
  justify-content:center;
  align-self:flex-start;
  width:18px;
  min-width:18px;
  margin-top:1px;
  flex-shrink:0;
}
.menu-item--check.active::before{
  content:"✓";
}
#discover-ranking-menu-panel{
  min-width:max(100%, 320px);
}
#discover-ranking-menu-panel .menu-item{
  min-height:56px;
  padding:10px 12px;
  align-items:flex-start;
  white-space:normal;
}
#discover-ranking-menu-panel .menu-item-copy{
  gap:3px;
}
#discover-ranking-menu-panel .menu-item-copy > span:first-child{
  line-height:1.35;
  font-weight:620;
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
}"""
