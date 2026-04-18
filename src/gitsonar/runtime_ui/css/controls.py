#!/usr/bin/env python3
from __future__ import annotations

CSS = r""".toolbar-filters{
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

.card.menu-host-open,
.update-card.menu-host-open,
.workspace-bar.menu-host-open,
.panel.menu-host-open,
.batch-dock.menu-host-open{
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
}"""
