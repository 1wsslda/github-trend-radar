#!/usr/bin/env python3
from __future__ import annotations

import json


HTML_TEMPLATE = (
    """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__APP_NAME__</title>
<style>
:root{
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
  max-width:1720px;
  margin:0 auto;
  padding:clamp(18px,2.6vw,30px) clamp(16px,2vw,28px) 148px;
}

.hero{
  display:grid;
  gap:14px;
  margin-bottom:16px;
}
.hero-copy{
  display:grid;
  gap:10px;
  padding:16px 20px 14px;
  border:1px solid var(--border);
  border-radius:24px;
  background:linear-gradient(180deg, rgba(26,23,19,.94), rgba(18,16,12,.98));
  box-shadow:var(--shadow-soft);
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
.hero-kicker::before{
  content:"";
  width:24px;
  height:1px;
  background:rgba(227,198,145,.72);
}
.hero h1{
  margin:0;
  font-size:clamp(1.64rem,3.4vw,2.7rem);
  line-height:1.08;
  letter-spacing:-.04em;
  font-weight:680;
}
.hero-copy p{
  margin:0;
  color:var(--text-soft);
  font-size:.94rem;
  line-height:1.58;
}
.hero-support{color:var(--muted)}
.hero-band{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:14px;
  padding:12px 16px;
  border:1px solid var(--border);
  border-radius:18px;
  background:rgba(20,18,14,.9);
  box-shadow:var(--shadow-soft);
}
.hero-band-copy{
  display:flex;
  align-items:center;
  gap:10px 12px;
  flex-wrap:wrap;
  min-width:0;
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
.hero-actions,
.toolbar-utility,
.badges,
.meta-line,
.states,
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
    """
    """
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
.state-btn{
  font:inherit;
}
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
.action-quiet:active,
.action-primary:active,
.tab:active,
.seg-btn:active,
.state-btn:active,
.menu-item:active{
  transform:translateY(1px);
}
.action-quiet:disabled,
.action-primary:disabled,
.seg-btn:disabled,
.menu-item:disabled,
.state-btn:disabled{
  opacity:.42;
  cursor:not-allowed;
  transform:none;
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
    """
    """
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
.menu-wrap.open > .menu-toggle .menu-caret,
.menu-wrap.open > .seg-btn .menu-caret,
.menu-wrap.open > .split-trigger .menu-caret{
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
.menu-wrap.open .menu-panel{
  opacity:1;
  visibility:visible;
  transform:translateY(0);
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
.menu-wrap.open > .seg-btn{
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
  display:flex;
  gap:10px;
  flex-wrap:wrap;
  align-items:center;
  margin-bottom:20px;
  padding:10px;
  border:1px solid var(--border);
  border-radius:20px;
  background:rgba(20,18,14,.92);
  backdrop-filter:blur(10px);
  box-shadow:var(--shadow-soft);
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
  transition:border-color .25s var(--ease-smooth),transform .25s var(--ease-smooth),box-shadow .25s var(--ease-smooth);
}
.card.selectable,
.update-card.selectable{cursor:pointer}
.card.selectable:hover,
.update-card.selectable:hover{
  transform:translateY(-2px);
  border-color:rgba(246,222,174,.18);
  box-shadow:0 18px 36px rgba(0,0,0,.22);
}
.card.selected,
.update-card.selected{
  border-color:rgba(233,201,143,.36);
  box-shadow:
    0 0 0 1px rgba(233,201,143,.18) inset,
    0 20px 38px rgba(0,0,0,.24);
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
    """
    """
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
.badge-selection{
  color:var(--accent);
  border-color:rgba(233,201,143,.22);
  background:rgba(233,201,143,.08);
}
.title{
  display:block;
  margin:6px 0 0;
  color:var(--text);
  font-size:1.12rem;
  line-height:1.28;
  letter-spacing:-.02em;
  font-weight:650;
  word-break:break-word;
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
  top:calc(100% + 10px);
  padding:14px 16px;
  border:1px solid rgba(232,214,184,.14);
  border-radius:16px;
  background:rgba(16,14,11,.98);
  color:var(--text-soft);
  box-shadow:0 22px 42px rgba(0,0,0,.32);
  opacity:0;
  visibility:hidden;
  transform:translateY(6px);
  transition:opacity .2s var(--ease-smooth),transform .2s var(--ease-smooth),visibility .2s var(--ease-smooth);
  pointer-events:none;
  z-index:8;
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
.meta-line{gap:8px}
.meta-pill{
  display:inline-flex;
  align-items:center;
  gap:6px;
  min-height:28px;
  padding:0 10px;
  border-radius:999px;
  border:1px solid rgba(232,214,184,.08);
  background:rgba(12,10,8,.34);
  font-size:.78rem;
  color:var(--text-soft);
}
.meta-pill strong{
  color:var(--muted);
  font-size:10px;
  letter-spacing:.08em;
  text-transform:uppercase;
}
.states{gap:8px}
.state-btn{
  min-height:32px;
  padding:0 11px;
  border-radius:999px;
  border:1px solid rgba(232,214,184,.12);
  background:rgba(12,10,8,.4);
  color:var(--muted);
  cursor:pointer;
  transition:
    border-color .25s var(--ease-smooth),
    background .25s var(--ease-smooth),
    color .25s var(--ease-smooth),
    transform .25s var(--ease-smooth);
}
.state-btn:hover{
  border-color:rgba(232,214,184,.22);
  color:var(--text-soft);
}
.state-btn.active{
  background:rgba(233,201,143,.18);
  border-color:rgba(233,201,143,.22);
  color:var(--text);
}
.card-actions{gap:8px}

.empty{
  padding:78px 20px;
  border:1px dashed rgba(232,214,184,.14);
  border-radius:22px;
  background:rgba(16,14,11,.56);
  color:var(--muted);
  text-align:center;
  font-size:.95rem;
  display:flex;
  flex-direction:column;
  align-items:center;
  gap:16px;
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
  bottom:20px;
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
  bottom:22px;
  z-index:45;
  display:flex;
  align-items:center;
  gap:10px;
  padding:10px 12px;
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
  padding:0 6px 0 4px;
}
.batch-dock-count{
  display:grid;
  gap:2px;
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
    """
    """
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
  padding:24px 24px 18px;
  border-bottom:1px solid rgba(232,214,184,.1);
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
  gap:12px;
}
.compare-grid{display:grid;gap:16px}
.detail-item{
  padding:14px 15px;
  border-radius:16px;
  border:1px solid rgba(232,214,184,.08);
  background:rgba(24,21,17,.74);
}
.detail-item strong{
  display:block;
  margin-bottom:8px;
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

@media (min-width:1600px){
  .cards{grid-template-columns:repeat(4,minmax(0,1fr))}
}
@media (max-width:1199px){
  .toolbar-main{grid-template-columns:1fr}
  .toolbar-filters{grid-template-columns:1fr 1fr}
  .cards{grid-template-columns:repeat(2,minmax(0,1fr))}
}
@media (max-width:959px){
  .hero-band{
    display:grid;
    grid-template-columns:1fr;
    justify-content:stretch;
  }
  .toolbar-filters,
  .settings-inline{
    grid-template-columns:1fr;
  }
}
@media (max-width:759px){
  .page{padding:18px 14px 126px}
  .hero-copy,
  .hero-band,
  .control-shell,
  .tabs,
  .card,
  .update-card,
  .compare-card{border-radius:20px}
  .tabs{top:10px}
  .cards{grid-template-columns:1fr}
  .toolbar-utility{width:100%}
  .action-split{width:100%}
  .action-split .split-main{
    min-width:0;
    flex:1;
  }
  .detail-grid{grid-template-columns:1fr}
  .panel-head,
  .panel-body{
    padding-left:20px;
    padding-right:20px;
  }
  .batch-dock{
    left:12px;
    right:12px;
    width:auto;
    flex-wrap:wrap;
    justify-content:flex-start;
    transform:translateY(18px);
  }
  .batch-dock.show{transform:translateY(0)}
  .batch-dock-meta{width:100%;padding:0 2px}
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
</style>
</head>
<body>
<div class="page">
  <section class="hero">
    <div class="hero-copy">
      <div class="hero-kicker">GitHub Intelligence Desk</div>
      <h1>__APP_NAME__</h1>
      <p>把 GitHub 趋势、收藏追踪、仓库详情和 ChatGPT 分析收进一个更适合长期阅读的桌面情报台。</p>
      <p class="hero-support">默认先看内容，再做筛选、对比和批量判断。</p>
    </div>
    <div class="hero-band">
      <div class="hero-band-copy">
        <span class="status-label">Runtime</span>
        <span class="status-value" id="note"></span>
        <span class="status-divider"></span>
        <span class="status-label">Workspace</span>
        <span class="status-value">阅读、筛选、对比、批量分析</span>
      </div>
      <div class="hero-actions">
        <button class="action-quiet" type="button" onclick="refreshNow()">刷新</button>
        <button class="action-quiet" type="button" onclick="hideToTray()">隐藏到托盘</button>
        <button class="action-quiet" type="button" onclick="openSettings()">设置</button>
        <div class="menu-wrap" data-menu-id="app-more-menu">
          <button class="action-quiet menu-toggle" type="button" onclick="toggleMenu(event,'app-more-menu')">更多<span class="menu-caret"></span></button>
          <div class="menu-panel" id="app-more-menu-panel">
            <button class="menu-item" type="button" onclick="exportUserState();closeMenus();">导出数据</button>
            <button class="menu-item" type="button" id="clear-updates-menu-item" onclick="clearFavoriteUpdates();closeMenus();" hidden>清空收藏更新</button>
          </div>
        </div>
      </div>
    </div>
  </section>

  <section class="toolbar">
    <div class="control-shell">
      <div class="toolbar-head">
        <div class="toolbar-copy">
          <div class="summary">当前面板可见 <span class="metric-number" id="visible-count">0</span><span id="visible-label"> 个仓库</span> · 已选 <span class="metric-number" id="selected-count">0</span> 项</div>
          <div class="sub">程序本身不提供 VPN；如果当前网络无法访问 GitHub，请先准备好代理或 VPN，再到“设置”里填写代理地址。</div>
        </div>
      </div>
"""
    """
      <div class="toolbar-main">
        <label class="field search-field">
          <span class="field-label">搜索</span>
          <span class="field-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="7"></circle>
              <line x1="20" y1="20" x2="16.65" y2="16.65"></line>
            </svg>
          </span>
          <input id="search" class="field-input" type="search" placeholder="搜索仓库 / 描述 / 语言 / 更新内容">
        </label>

        <div class="action-split menu-wrap" data-menu-id="ai-target-menu">
          <button class="action-primary split-main" id="analyze-visible-btn" type="button" onclick="analyzeVisible()">
            <span class="split-main-label">
              <span class="split-main-title">分析当前列表</span>
              <span class="split-main-note" id="ai-target-label">ChatGPT 网页版</span>
            </span>
          </button>
          <button class="action-primary split-trigger" id="ai-target-trigger" type="button" aria-label="选择分析目标" onclick="toggleMenu(event,'ai-target-menu')">
            <span class="menu-caret"></span>
          </button>
          <div class="menu-panel" id="ai-target-menu-panel">
            <button class="menu-item" type="button" data-ai-target="web" onclick="setAiTarget('web')">ChatGPT 网页版</button>
            <button class="menu-item" type="button" data-ai-target="desktop" onclick="setAiTarget('desktop')">ChatGPT 桌面版</button>
            <button class="menu-item" type="button" data-ai-target="copy" onclick="setAiTarget('copy')">仅复制提示词</button>
          </div>
        </div>
      </div>

      <div class="toolbar-filters">
        <div class="control-group" id="state-filter-group">
          <div class="group-label">状态筛选</div>
          <div class="segmented" id="state-filter-seg">
            <button class="seg-btn" type="button" data-value="">全部</button>
            <button class="seg-btn" type="button" data-value="unmarked">未标记</button>
            <button class="seg-btn" type="button" data-value="favorites">收藏</button>
            <button class="seg-btn" type="button" data-value="watch_later">稍后看</button>
            <button class="seg-btn" type="button" data-value="read">已读</button>
            <button class="seg-btn" type="button" data-value="ignored">忽略</button>
          </div>
        </div>

        <label class="field select-field">
          <span class="field-label">语言</span>
          <select id="language" class="field-input">
            <option value="">全部语言</option>
          </select>
        </label>

        <div class="control-group" id="sort-primary-group">
          <div class="group-label">排序方式</div>
          <div class="segmented" id="sort-primary-seg">
            <button class="seg-btn" type="button" data-sort-primary="stars">总星标</button>
            <button class="seg-btn" type="button" data-sort-primary="trending">趋势</button>
            <button class="seg-btn" type="button" data-sort-primary="gained">增长</button>
            <div class="menu-wrap" data-menu-id="sort-more-menu">
              <button class="seg-btn" id="sort-more-toggle" type="button" onclick="toggleMenu(event,'sort-more-menu')">更多<span class="seg-btn-note" id="sort-more-current"></span><span class="menu-caret"></span></button>
              <div class="menu-panel align-left" id="sort-more-menu-panel">
                <button class="menu-item" type="button" data-sort-more="forks" onclick="setSortPrimary('forks')">Fork</button>
                <button class="menu-item" type="button" data-sort-more="name" onclick="setSortPrimary('name')">仓库名</button>
                <button class="menu-item" type="button" data-sort-more="language" onclick="setSortPrimary('language')">语言</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>

  <div class="tabs" id="tabs"></div>
  <div class="cards" id="cards"></div>
</div>

<div class="batch-dock" id="batch-dock">
  <div class="batch-dock-meta">
    <div class="batch-dock-count">
      <span class="batch-dock-label">已选条目</span>
      <span class="batch-dock-value"><span class="metric-number" id="batch-dock-count">0</span> 项</span>
    </div>
  </div>
  <button class="action-primary" type="button" onclick="analyzeSelected()">批量分析</button>
  <button class="action-quiet" id="compare-selected-btn" type="button" onclick="openCompareSelected()">对比</button>
  <div class="menu-wrap" data-menu-id="batch-more-menu">
    <button class="action-quiet menu-toggle" type="button" onclick="toggleMenu(event,'batch-more-menu')">更多<span class="menu-caret"></span></button>
    <div class="menu-panel upward align-left" id="batch-more-menu-panel">
      <div class="menu-note">低频动作收进这里，避免把顶部变成第二条导航。</div>
      <div class="menu-divider"></div>
      <button class="menu-item" type="button" onclick="batchSetState('favorites');closeMenus();">批量收藏</button>
      <button class="menu-item" type="button" onclick="batchSetState('watch_later');closeMenus();">批量稍后看</button>
      <button class="menu-item" type="button" onclick="batchSetState('read');closeMenus();">批量已读</button>
      <button class="menu-item" type="button" onclick="batchSetState('ignored');closeMenus();">批量忽略</button>
      <div class="menu-divider"></div>
      <button class="menu-item" type="button" onclick="selectVisible();closeMenus();">重新全选本页</button>
      <button class="menu-item" type="button" onclick="clearSelected();closeMenus();">清空选择</button>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<section class="overlay settings" id="settings-modal">
  <div class="panel">
    <div class="panel-head">
      <div>
        <div class="panel-title">设置</div>
        <div class="sub">配置 GitHub Token、代理、刷新频率、条目上限和关闭行为。</div>
      </div>
      <button class="action-quiet" type="button" onclick="closeSettings()">关闭</button>
    </div>
    <div class="panel-body settings-grid">
      <div class="settings-form">
        <label class="field">
          <span class="field-label">GitHub Token</span>
          <input id="setting-token" class="field-input" type="password" placeholder="可选，用于提高请求稳定性">
        </label>
        <label class="field">
          <span class="field-label">代理地址</span>
          <input id="setting-proxy" class="field-input" type="text" placeholder="留空则自动探测">
        </label>
        <div class="settings-inline">
          <label class="field">
            <span class="field-label">刷新间隔</span>
            <input id="setting-refresh-hours" class="field-input" type="number" min="1" max="24" placeholder="1">
            <span class="field-meta">1 - 24 小时</span>
          </label>
          <label class="field">
            <span class="field-label">结果上限</span>
            <input id="setting-result-limit" class="field-input" type="number" min="10" max="100" placeholder="25">
            <span class="field-meta">10 - 100 条</span>
          </label>
          <label class="field">
            <span class="field-label">端口</span>
            <input id="setting-port" class="field-input" type="number" min="1" max="65535" placeholder="8080">
            <span class="field-meta">修改后重启生效</span>
          </label>
        </div>
"""
    """
        <label class="field select-field">
          <span class="field-label">关闭行为</span>
          <select id="setting-close-behavior" class="field-input">
            <option value="tray">关闭主窗口时保留托盘运行</option>
            <option value="exit">关闭主窗口时直接退出程序</option>
          </select>
        </label>
        <div class="switch-row">
          <div class="switch-copy">
            <div class="switch-title">开机启动</div>
            <div class="switch-desc">随系统自动启动，方便后台持续跟踪 GitHub 变化。</div>
          </div>
          <label class="switch">
            <input id="setting-auto-start" type="checkbox">
            <span class="switch-track">
              <span class="switch-thumb"></span>
            </span>
          </label>
        </div>
      </div>
      <div class="notice">网络提醒：程序本身不提供 VPN。如果趋势列表刷不出来、仓库详情加载失败，通常需要先开启代理或 VPN，然后把代理地址填到上面的“代理地址”里。</div>
      <div class="notice">关闭提醒：如果选择“保留托盘运行”，主窗口关闭后程序仍会继续运行，图标可能收在任务栏右下角的隐藏图标里。</div>
      <div class="sub" id="settings-runtime-hint"></div>
      <div class="settings-actions">
        <button class="action-primary" type="button" onclick="saveSettings()">保存设置</button>
        <button class="action-quiet danger" type="button" onclick="exitApp()">退出程序</button>
      </div>
    </div>
  </div>
</section>

<section class="overlay detail" id="detail-modal">
  <div class="panel">
    <div class="panel-head">
      <div>
        <div class="panel-title">仓库详情</div>
        <div class="sub" id="detail-title">加载中...</div>
      </div>
      <button class="action-quiet" type="button" onclick="closeDetail()">关闭</button>
    </div>
    <div class="panel-body" id="detail-body"></div>
  </div>
</section>

<section class="overlay compare" id="compare-modal">
  <div class="panel">
    <div class="panel-head">
      <div>
        <div class="panel-title">仓库对比</div>
        <div class="sub">把两个仓库按同一组维度并排展开，便于快速判断方向、热度和长期价值。</div>
      </div>
      <button class="action-quiet" type="button" onclick="closeCompare()">关闭</button>
    </div>
    <div class="panel-body" id="compare-body"></div>
  </div>
</section>

<script>
const INITIAL = __PAYLOAD__;
const UPDATE_PANEL_KEY = "favorite-updates";
const INTERACTIVE_SELECTOR = "button,a,input,select,label,textarea";
const SORT_KEYS = new Set(["stars","trending","gained","forks","name","language"]);
const PRIMARY_SORT_KEYS = ["stars","trending","gained"];
const STATE_FILTER_KEYS = new Set(["","unmarked","favorites","watch_later","read","ignored"]);
const SORT_LABELS = {
  stars:"总星标",
  trending:"趋势",
  gained:"增长",
  forks:"Fork",
  name:"仓库名",
  language:"语言",
};
const AI_TARGET_LABELS = {
  web:"ChatGPT 网页版",
  desktop:"ChatGPT 桌面版",
  copy:"仅复制提示词",
};

let snapshot = INITIAL.snapshot || {};
let userState = INITIAL.userState || {};
let settings = INITIAL.settings || {};
let currentNote = INITIAL.note || "";
let panel = localStorage.getItem("gtr-tab") || "daily";
let stateFilter = normalizeStateFilter(localStorage.getItem("gtr-state-filter") || "");
let sortPrimary = normalizeSortKey(localStorage.getItem("gtr-sort-primary") || settings.default_sort || "stars");
let aiTarget = normalizeAiTarget(localStorage.getItem("gtr-ai-target") || "web");
let comparePrompt = "";
let selectedUrls = loadSelectedUrls();
let languageFilter = localStorage.getItem("gtr-language") || "";

function normalizeSortKey(value){
  const key = String(value || "").trim();
  return SORT_KEYS.has(key) ? key : "stars";
}

function normalizeStateFilter(value){
  const key = String(value || "").trim();
  return STATE_FILTER_KEYS.has(key) ? key : "";
}

function normalizeAiTarget(value){
  const key = String(value || "").trim();
  return ["web","desktop","copy"].includes(key) ? key : "web";
}

function closeBehaviorLabel(value){
  return String(value || "").trim() === "exit" ? "关闭主窗口时直接退出程序" : "关闭主窗口时保留托盘运行";
}
"""
    """
function loadSelectedUrls(){
  try{
    const raw = JSON.parse(localStorage.getItem("gtr-selected") || "[]");
    return new Set(Array.isArray(raw) ? raw.filter(Boolean) : []);
  }catch(_err){
    return new Set();
  }
}

function saveSelectedUrls(){
  localStorage.setItem("gtr-selected", JSON.stringify([...selectedUrls]));
}

function h(value){
  return String(value ?? "").replace(/[&<>"']/g, char => {
    if(char === "&") return "&amp;";
    if(char === "<") return "&lt;";
    if(char === ">") return "&gt;";
    if(char === '"') return "&quot;";
    return "&#39;";
  });
}

function sleep(ms){
  return new Promise(resolve => setTimeout(resolve, ms));
}

function toast(message){
  const node = document.getElementById("toast");
  node.textContent = message;
  node.classList.add("show");
  clearTimeout(window.__toastTimer);
  window.__toastTimer = setTimeout(() => node.classList.remove("show"), 2400);
}

async function copyText(text, label){
  const value = String(text || "").trim();
  if(!value){
    toast("没有可复制的内容");
    return false;
  }
  try{
    if(navigator.clipboard && navigator.clipboard.writeText){
      await navigator.clipboard.writeText(value);
    }else{
      throw new Error("clipboard");
    }
  }catch(_err){
    const area = document.createElement("textarea");
    area.value = value;
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.focus();
    area.select();
    document.execCommand("copy");
    document.body.removeChild(area);
  }
  toast(label || "已复制");
  return true;
}

async function requestJson(url, options, errorMessage = "无法连接本地服务"){
  let resp;
  try{
    resp = await fetch(url, options);
  }catch(_err){
    throw new Error(errorMessage);
  }
  const rawText = await resp.text();
  let data = {};
  if(rawText){
    try{
      data = JSON.parse(rawText);
    }catch(_err){
      throw new Error(resp.ok ? "服务返回了无效数据" : errorMessage);
    }
  }
  return {resp, data};
}

function current(key){
  return Array.isArray(snapshot[key]) ? snapshot[key] : [];
}

function saved(key){
  return (userState[key] || []).map(url => userState.repo_records?.[url]).filter(Boolean);
}

function updateByUrl(url){
  return (userState.favorite_updates || []).find(item => item.url === url) || null;
}

function synthesizeRepoFromUpdate(update){
  if(!update || !String(update.full_name || "").includes("/")) return null;
  const [owner, name] = String(update.full_name).split("/", 2);
  return {
    full_name:update.full_name,
    owner,
    name,
    url:update.url,
    description:"",
    description_raw:"",
    language:"",
    stars:update.stars || 0,
    forks:update.forks || 0,
    gained:0,
    gained_text:"",
    growth_source:"unavailable",
    rank:0,
    period_key:UPDATE_PANEL_KEY,
    source_label:"收藏更新",
  };
}

function repoByUrl(url){
  for(const period of INITIAL.periods || []){
    const hit = current(period.key).find(repo => repo.url === url);
    if(hit) return hit;
  }
  if(userState.repo_records?.[url]) return userState.repo_records[url];
  return synthesizeRepoFromUpdate(updateByUrl(url));
}

function panelRepoSource(){
  if(panel === UPDATE_PANEL_KEY) return [];
  return panel.startsWith("saved:") ? saved(panel.split(":")[1]) : current(panel);
}

function cleanupSelected(){
  const valid = [...selectedUrls].filter(url => repoByUrl(url) || updateByUrl(url));
  if(valid.length !== selectedUrls.size){
    selectedUrls = new Set(valid);
    saveSelectedUrls();
  }
}

function selectedRepos(){
  cleanupSelected();
  const seen = new Set();
  return [...selectedUrls]
    .map(url => repoByUrl(url))
    .filter(repo => repo && !seen.has(repo.url) && seen.add(repo.url));
}

function selectedCount(){
  cleanupSelected();
  return selectedUrls.size;
}

function growthSource(repo){
  return String(repo?.growth_source || "").trim();
}

function hasGrowthValue(repo){
  return Number(repo?.gained || 0) > 0 || growthSource(repo) === "trending";
}

function gainBadgeClass(repo){
  return hasGrowthValue(repo) ? "gain" : "source";
}
"""
    """
function gainLabel(repo){
  const source = growthSource(repo);
  if(source === "estimated"){
    return Number(repo?.gained || 0) > 0 ? `较上次 +${repo.gained}` : "较上次持平";
  }
  if(source === "unavailable"){
    if(String(repo?.source_label || "").includes("收藏更新")) return "更新追踪项";
    return "待下次估算";
  }
  if(repo.gained_text) return repo.gained_text;
  if((repo.gained || 0) > 0) return `+${repo.gained}`;
  return "暂无增长数据";
}

function repoLine(repo){
  return `- ${repo.full_name} | ${repo.language || "未知语言"} | Stars ${repo.stars || 0} | ${repo.url}\\n  简介: ${repo.description || repo.description_raw || "暂无描述"}`;
}

function buildRepoPrompt(repo){
  return `请用中文分析这个 GitHub 仓库，并按下面结构输出：
1. 这个项目是做什么的
2. 适合哪些用户或场景
3. 技术亮点与差异化
4. 商业化、产品化或副业机会
5. 可能的风险和局限
6. 是否值得持续关注

仓库: ${repo.full_name}
链接: ${repo.url}
语言: ${repo.language || "未知语言"}
总星标: ${repo.stars || 0}
增长: ${gainLabel(repo)}
来源: ${repo.source_label || "未知来源"}
简介: ${repo.description || repo.description_raw || "暂无描述"}`;
}

function buildBatchPrompt(repos, title, batchIndex, batchCount){
  const groupNote = batchCount > 1 ? `\\n当前是第 ${batchIndex}/${batchCount} 组。` : "";
  return `请用中文分别分析下面这些 GitHub 仓库，并对每个仓库分别输出：
1. 项目是做什么的
2. 适合哪些用户或场景
3. 技术亮点
4. 风险和注意点
5. 是否值得持续关注${groupNote}

分析范围: ${title}

仓库列表：
${repos.map(repoLine).join("\\n")}`;
}

function splitRepoPrompts(repos, title, maxEncodedLength = 2600, maxItemsPerBatch = 4){
  const normalized = repos.filter(Boolean);
  if(!normalized.length) return [];
  if(normalized.length === 1) return [buildRepoPrompt(normalized[0])];
  const batches = [];
  let currentBatch = [];
  const buildDraft = candidate => `请用中文分别分析下面这些 GitHub 仓库，并对每个仓库分别输出：1. 项目是做什么的 2. 适合哪些用户或场景 3. 技术亮点 4. 风险和注意点 5. 是否值得持续关注\\n分析范围: ${title}\\n仓库列表：\\n${candidate.map(repoLine).join("\\n")}`;
  for(const repo of normalized){
    const candidate = [...currentBatch, repo];
    const encodedLength = encodeURIComponent(buildDraft(candidate)).length;
    if(currentBatch.length && (encodedLength > maxEncodedLength || candidate.length > maxItemsPerBatch)){
      batches.push(currentBatch);
      currentBatch = [repo];
    }else{
      currentBatch = candidate;
    }
  }
  if(currentBatch.length) batches.push(currentBatch);
  return batches.map((batch, index) => buildBatchPrompt(batch, title, index + 1, batches.length));
}

async function openExternalUrl(url){
  const target = String(url || "").trim();
  if(!target) return false;
  try{
    const {resp, data} = await requestJson(
      "/api/open-external",
      {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({url:target}),
      },
      "打开链接失败",
    );
    if(resp.ok && data.ok) return true;
  }catch(_err){}
  window.open(target, "_blank", "noopener");
  return true;
}

async function openChatGPTPrompts(prompts){
  const queue = prompts.filter(Boolean);
  if(!queue.length) return false;
  const mode = normalizeAiTarget(aiTarget);
  aiTarget = mode;
  localStorage.setItem("gtr-ai-target", aiTarget);
  if(mode === "copy"){
    await copyText(queue.join("\\n\\n-----\\n\\n"), "分析提示词已复制");
    return true;
  }
  await copyText(
    queue[queue.length - 1],
    queue.length === 1 ? "分析提示词已复制，正在打开 ChatGPT" : `已准备 ${queue.length} 组提示词，正在批量打开 ChatGPT`,
  );
  for(let index = 0; index < queue.length; index += 1){
    const {resp, data} = await requestJson(
      "/api/chatgpt/open",
      {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({mode, prompt:queue[index]}),
      },
      "打开 ChatGPT 失败",
    );
    if(!resp.ok || !data.ok){
      toast(data.error || "打开 ChatGPT 失败");
      return false;
    }
    if(index < queue.length - 1) await sleep(300);
  }
  toast(queue.length === 1 ? "已打开 ChatGPT" : `已批量打开 ${queue.length} 组 ChatGPT 分析`);
  return true;
}

async function exportUserState(){
  try{
    const resp = await fetch("/api/export", {cache:"no-store"});
    if(!resp.ok) throw new Error("导出失败");
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `gitsonar-export-${new Date().toISOString().slice(0,10)}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    toast("已导出数据");
  }catch(error){
    toast(error.message || "导出失败");
  }
}

function compareByKey(a, b, key){
  if(key === "trending") return (a.rank || 9999) - (b.rank || 9999) || (b.gained || 0) - (a.gained || 0) || (b.stars || 0) - (a.stars || 0);
  if(key === "gained") return (b.gained || 0) - (a.gained || 0) || (b.stars || 0) - (a.stars || 0) || (a.rank || 9999) - (b.rank || 9999);
  if(key === "forks") return (b.forks || 0) - (a.forks || 0) || (b.stars || 0) - (a.stars || 0) || (a.rank || 9999) - (b.rank || 9999);
  if(key === "name") return String(a.full_name || "").localeCompare(String(b.full_name || ""), "zh-Hans-CN") || (a.rank || 9999) - (b.rank || 9999);
  if(key === "language") return String(a.language || "").localeCompare(String(b.language || ""), "zh-Hans-CN") || (b.stars || 0) - (a.stars || 0) || (a.rank || 9999) - (b.rank || 9999);
  return (b.stars || 0) - (a.stars || 0) || (b.gained || 0) - (a.gained || 0) || (a.rank || 9999) - (b.rank || 9999);
}

function visibleRepos(){
  if(panel === UPDATE_PANEL_KEY) return [];
  const raw = panelRepoSource();
  const query = document.getElementById("search").value.trim().toLowerCase();
  const language = document.getElementById("language").value;
  const repos = raw.filter(repo => {
    const haystack = `${repo.full_name} ${repo.description || ""} ${repo.description_raw || ""} ${repo.language || ""} ${repo.source_label || ""}`.toLowerCase();
    if(query && !haystack.includes(query)) return false;
    if(language && (repo.language || "") !== language) return false;
    if(stateFilter === "unmarked"){
      if((INITIAL.states || []).some(state => (userState[state.key] || []).includes(repo.url))) return false;
    }else if(stateFilter && !((userState[stateFilter] || []).includes(repo.url))){
      return false;
    }
    return true;
  });
  const sortKeys = [sortPrimary, "trending"].filter((key, index, array) => key && array.indexOf(key) === index);
  repos.sort((a, b) => {
    for(const key of sortKeys){
      const result = compareByKey(a, b, key);
      if(result) return result;
    }
    return 0;
  });
  return repos;
}
"""
    """
function visibleUpdates(){
  if(panel !== UPDATE_PANEL_KEY) return [];
  const query = document.getElementById("search").value.trim().toLowerCase();
  return (userState.favorite_updates || []).filter(update => {
    const haystack = `${update.full_name || ""} ${(update.changes || []).join(" ")} ${update.latest_release_tag || ""}`.toLowerCase();
    return !query || haystack.includes(query);
  });
}

function visibleLinkList(){
  return panel === UPDATE_PANEL_KEY ? visibleUpdates().map(update => update.url) : visibleRepos().map(repo => repo.url);
}

function tabsData(){
  return [
    ...(INITIAL.periods || []).map(period => ({key:period.key, label:period.label, count:current(period.key).length})),
    ...(INITIAL.states || []).map(state => ({key:`saved:${state.key}`, label:state.label, count:(userState[state.key] || []).length})),
    {key:UPDATE_PANEL_KEY, label:"收藏更新", count:(userState.favorite_updates || []).length},
  ];
}

function ensureValidPanel(){
  const keys = new Set(tabsData().map(tab => tab.key));
  if(!keys.has(panel)){
    panel = "daily";
    localStorage.setItem("gtr-tab", panel);
  }
}

function menuRoot(id){
  return document.querySelector(`[data-menu-id="${id}"]`);
}

function closeMenus(exceptId = ""){
  document.querySelectorAll("[data-menu-id].open").forEach(root => {
    if(root.dataset.menuId !== exceptId) root.classList.remove("open");
  });
}

function toggleMenu(event, id){
  if(event){
    event.preventDefault();
    event.stopPropagation();
    if(event.currentTarget?.disabled) return;
  }
  const root = menuRoot(id);
  if(!root) return;
  const willOpen = !root.classList.contains("open");
  closeMenus(willOpen ? id : "");
  root.classList.toggle("open", willOpen);
}

function setStateFilter(value){
  stateFilter = normalizeStateFilter(value);
  localStorage.setItem("gtr-state-filter", stateFilter);
  render();
}

function setSortPrimary(value){
  sortPrimary = normalizeSortKey(value);
  localStorage.setItem("gtr-sort-primary", sortPrimary);
  closeMenus();
  render();
}

function setAiTarget(value){
  aiTarget = normalizeAiTarget(value);
  localStorage.setItem("gtr-ai-target", aiTarget);
  closeMenus();
  syncAiTargetUI();
}

function syncStateFilterUI(){
  document.querySelectorAll("#state-filter-seg [data-value]").forEach(btn => {
    btn.classList.toggle("active", (btn.dataset.value || "") === stateFilter);
  });
}

function syncSortUI(){
  document.querySelectorAll("#sort-primary-seg [data-sort-primary]").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.sortPrimary === sortPrimary);
  });
  const isMoreSort = !PRIMARY_SORT_KEYS.includes(sortPrimary);
  const moreToggle = document.getElementById("sort-more-toggle");
  moreToggle.classList.toggle("is-subactive", isMoreSort);
  document.getElementById("sort-more-current").textContent = isMoreSort ? `· ${SORT_LABELS[sortPrimary] || ""}` : "";
  document.querySelectorAll("[data-sort-more]").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.sortMore === sortPrimary);
  });
}

function syncAiTargetUI(){
  document.getElementById("ai-target-label").textContent = AI_TARGET_LABELS[aiTarget] || AI_TARGET_LABELS.web;
  document.querySelectorAll("[data-ai-target]").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.aiTarget === aiTarget);
  });
}

function syncControlStates(){
  const isUpdatePanel = panel === UPDATE_PANEL_KEY;
  document.getElementById("language").disabled = isUpdatePanel;
  document.querySelectorAll("#state-filter-seg .seg-btn").forEach(btn => { btn.disabled = isUpdatePanel; });
  document.querySelectorAll("#sort-primary-seg .seg-btn").forEach(btn => { btn.disabled = isUpdatePanel; });
  document.getElementById("analyze-visible-btn").disabled = isUpdatePanel;
  document.getElementById("ai-target-trigger").disabled = isUpdatePanel;
  document.getElementById("state-filter-group").classList.toggle("is-disabled", isUpdatePanel);
  document.getElementById("sort-primary-group").classList.toggle("is-disabled", isUpdatePanel);
  document.getElementById("clear-updates-menu-item").hidden = !isUpdatePanel || !(userState.favorite_updates || []).length;
}

const emptyIcon = '<svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M16 16s-1.5-2-4-2-4 2-4 2"></path><line x1="9" y1="9" x2="9.01" y2="9"></line><line x1="15" y1="9" x2="15.01" y2="9"></line></svg>';

function selectedBadgeMarkup(index){
  return `<span class="badge badge-selection">#${index + 1} 已选</span>`;
}

function descBlockMarkup(text, muted = false){
  const safe = h(text || "暂无描述");
  return `<div class="desc-wrap"><div class="desc${muted ? " muted" : ""}" title="${safe}">${safe}</div><div class="desc-popover">${safe}</div></div>`;
}

function refreshSelectionSummary(){
  const isUpdatePanel = panel === UPDATE_PANEL_KEY;
  const repos = visibleRepos();
  const updates = visibleUpdates();
  const selected = selectedCount();
  document.getElementById("visible-count").textContent = isUpdatePanel ? updates.length : repos.length;
  document.getElementById("visible-label").textContent = isUpdatePanel ? " 条更新" : " 个仓库";
  document.getElementById("selected-count").textContent = selected;
  document.getElementById("batch-dock-count").textContent = selected;
  document.getElementById("compare-selected-btn").disabled = selectedRepos().length !== 2;
  document.getElementById("batch-dock").classList.toggle("show", selected > 0);
}

function syncCardSelectionState(){
  const urlArray = [...selectedUrls];
  document.querySelectorAll("[data-select-url]").forEach(card => {
    const url = card.getAttribute("data-select-url");
    const selectedIdx = urlArray.indexOf(url);
    const selected = selectedIdx !== -1;
    card.classList.toggle("selected", selected);
    const badgeRow = card.querySelector(".badges");
    const existingBadge = badgeRow?.querySelector(".badge-selection");
    const markup = selectedBadgeMarkup(selectedIdx);
    if(selected){
      if(!existingBadge && badgeRow){
        badgeRow.insertAdjacentHTML("afterbegin", markup);
      }else if(existingBadge && existingBadge.outerHTML !== markup){
        existingBadge.outerHTML = markup;
      }
    }else if(existingBadge){
      existingBadge.remove();
    }
  });
}

function refreshSelectionUI(){
  refreshSelectionSummary();
  syncCardSelectionState();
}
"""
    """
function renderRepoCards(repos){
  if(!repos.length) return `<div class="empty">${emptyIcon}<span>当前面板没有匹配结果。</span></div>`;
  const urlArray = [...selectedUrls];
  return repos.map(repo => {
    const selectedIdx = urlArray.indexOf(repo.url);
    const selected = selectedIdx !== -1;
    const descriptionText = repo.description || repo.description_raw || "暂无描述";
    return `<article class="card selectable ${selected ? "selected" : ""}" data-select-url="${h(repo.url)}">
      <div class="card-head">
        <div>
          <div class="badges">
            ${selected ? selectedBadgeMarkup(selectedIdx) : ""}
            <span class="badge ${gainBadgeClass(repo)}">${h(gainLabel(repo))}</span>
            <span class="badge source">${h(repo.source_label || "GitHub 来源")}</span>
          </div>
          <a class="title" href="${h(repo.url)}" target="_blank" rel="noopener" data-external-url="${h(repo.url)}">${h(repo.full_name)}</a>
        </div>
        <div class="meta-rank">#${repo.rank || "-"}</div>
      </div>
      <div class="card-body">
        ${descBlockMarkup(descriptionText)}
        <div class="meta-line">
          <span class="meta-pill"><strong>Stars</strong><span class="metric-number">${repo.stars || 0}</span></span>
          <span class="meta-pill"><strong>Forks</strong><span class="metric-number">${repo.forks || 0}</span></span>
          <span class="meta-pill"><strong>Language</strong><span>${h(repo.language || "未知语言")}</span></span>
        </div>
        <div class="states">
          ${(INITIAL.states || []).map(state => `<button class="state-btn ${(userState[state.key] || []).includes(repo.url) ? "active" : ""}" type="button" data-state-key="${h(state.key)}" onclick='toggleState(${JSON.stringify(state.key)}, ${JSON.stringify(repo.url)})'>${h(state.button)}</button>`).join("")}
        </div>
        <div class="card-actions">
          <button class="action-quiet" type="button" onclick='analyzeRepo(${JSON.stringify(repo.url)})'>分析</button>
          <button class="action-quiet" type="button" onclick='openDetail(${JSON.stringify(repo.owner)}, ${JSON.stringify(repo.name)}, ${JSON.stringify(repo.full_name)})'>详情</button>
        </div>
      </div>
    </article>`;
  }).join("");
}

function renderUpdateCards(items){
  if(!items.length) return `<div class="empty">${emptyIcon}<span>收藏仓库最近还没有检测到新的变化。</span></div>`;
  const urlArray = [...selectedUrls];
  return items.map(update => {
    const selectedIdx = urlArray.indexOf(update.url);
    const selected = selectedIdx !== -1;
    const changeBadges = (update.changes || []).map(change => `<span class="badge gain">${h(change)}</span>`).join("");
    const summary = (update.changes || []).length ? (update.changes || []).join(" · ") : "最近一次检测没有整理出可展示的变化摘要。";
    return `<article class="update-card selectable ${selected ? "selected" : ""}" data-select-url="${h(update.url)}">
      <div class="card-head">
        <div>
          <div class="badges">
            ${selected ? selectedBadgeMarkup(selectedIdx) : ""}
            <span class="badge source">收藏更新</span>
            ${update.latest_release_tag ? `<span class="badge source">${h(update.latest_release_tag)}</span>` : ""}
          </div>
          <a class="title" href="${h(update.url)}" target="_blank" rel="noopener" data-external-url="${h(update.url)}">${h(update.full_name)}</a>
        </div>
        <div class="meta-rank">${h(update.checked_at || "最近检查时间未知")}</div>
      </div>
      <div class="card-body">
        ${changeBadges ? `<div class="badges">${changeBadges}</div>` : ""}
        ${descBlockMarkup(summary)}
        <div class="meta-line">
          <span class="meta-pill"><strong>Stars</strong><span class="metric-number">${update.stars || 0}</span></span>
          <span class="meta-pill"><strong>Forks</strong><span class="metric-number">${update.forks || 0}</span></span>
          <span class="meta-pill"><strong>Pushed</strong><span>${h(update.pushed_at || "未知")}</span></span>
        </div>
        <div class="card-actions">
          <button class="action-quiet" type="button" onclick='analyzeRepo(${JSON.stringify(update.url)})'>分析</button>
          <button class="action-quiet" type="button" onclick='openDetailFromRecord(${JSON.stringify(update.full_name)}, ${JSON.stringify(update.url)})'>详情</button>
        </div>
      </div>
    </article>`;
  }).join("");
}

function render(){
  cleanupSelected();
  ensureValidPanel();
  const isUpdatePanel = panel === UPDATE_PANEL_KEY;
  document.getElementById("note").textContent = currentNote || "已显示最新数据";

  const languages = [...new Set(panelRepoSource().map(repo => repo.language).filter(Boolean))]
    .sort((a, b) => String(a).localeCompare(String(b), "zh-Hans-CN"));
  const languageNode = document.getElementById("language");
  languageNode.innerHTML = '<option value="">全部语言</option>' + languages.map(language => `<option value="${h(language)}">${h(language)}</option>`).join("");
  languageNode.value = languages.includes(languageFilter) ? languageFilter : "";
  languageFilter = languageNode.value;

  document.getElementById("tabs").innerHTML = tabsData().map(tab => `<button class="tab ${tab.key === panel ? "active" : ""}" type="button" onclick='setPanel(${JSON.stringify(tab.key)})'>${h(tab.label)} <span class="tab-count">${tab.count}</span></button>`).join("");

  const repos = visibleRepos();
  const updates = visibleUpdates();
  document.getElementById("cards").innerHTML = isUpdatePanel ? renderUpdateCards(updates) : renderRepoCards(repos);

  syncStateFilterUI();
  syncSortUI();
  syncAiTargetUI();
  syncControlStates();
  refreshSelectionSummary();
}

function setPanel(nextPanel){
  panel = String(nextPanel || "daily");
  localStorage.setItem("gtr-tab", panel);
  closeMenus();
  render();
}

function toggleSelected(url){
  if(selectedUrls.has(url)) selectedUrls.delete(url);
  else selectedUrls.add(url);
  saveSelectedUrls();
  refreshSelectionUI();
}

function clearSelected(){
  if(!selectedUrls.size){
    toast("当前没有已选条目");
    return;
  }
  selectedUrls.clear();
  saveSelectedUrls();
  refreshSelectionUI();
  toast("已清空选择");
}

function selectVisible(){
  const urls = visibleLinkList();
  if(!urls.length){
    toast(panel === UPDATE_PANEL_KEY ? "当前面板没有可选中的更新" : "当前面板没有可选中的仓库");
    return;
  }
  urls.forEach(url => selectedUrls.add(url));
  saveSelectedUrls();
  refreshSelectionUI();
  toast(`已选中 ${urls.length} 项`);
}

async function analyzeRepo(url){
  const repo = repoByUrl(url);
  if(!repo){
    toast("未找到仓库信息");
    return;
  }
  await openChatGPTPrompts([buildRepoPrompt(repo)]);
}
"""
    """
async function analyzeVisible(){
  if(panel === UPDATE_PANEL_KEY){
    toast("收藏更新面板不支持整页分析");
    return;
  }
  const repos = visibleRepos().slice(0, 20);
  if(!repos.length){
    toast("当前列表没有可分析的仓库");
    return;
  }
  await openChatGPTPrompts(splitRepoPrompts(repos, "当前 GitHub 趋势列表"));
}

async function analyzeSelected(){
  const repos = selectedRepos();
  if(!repos.length){
    toast("请先选中仓库");
    return;
  }
  await openChatGPTPrompts(splitRepoPrompts(repos, "已选仓库"));
}

async function fetchRepoDetails(repo){
  const {resp, data} = await requestJson(`/api/repo-details?owner=${encodeURIComponent(repo.owner)}&name=${encodeURIComponent(repo.name)}`, {cache:"no-store"}, "仓库详情加载失败");
  if(!resp.ok || !data.ok) throw new Error(data.error || "详情获取失败");
  return data.details;
}

function buildComparePrompt(a, b, detailA, detailB){
  return `请用中文对比下面两个 GitHub 仓库，并输出：
1. 两个项目分别解决什么问题
2. 功能定位和差异化对比
3. 社区热度与活跃度对比
4. 各自更适合哪些用户和场景
5. 如果只能长期关注一个，更建议关注哪一个，为什么

项目 A
名称: ${a.full_name}
链接: ${a.url}
语言: ${a.language || "未知语言"}
Stars: ${detailA.stars || a.stars || 0}
Forks: ${detailA.forks || a.forks || 0}
最近推送: ${detailA.pushed_at || "未知"}
简介: ${detailA.description || detailA.description_raw || a.description || a.description_raw || "暂无描述"}
README 摘要: ${detailA.readme_summary || detailA.readme_summary_raw || "暂无"}

项目 B
名称: ${b.full_name}
链接: ${b.url}
语言: ${b.language || "未知语言"}
Stars: ${detailB.stars || b.stars || 0}
Forks: ${detailB.forks || b.forks || 0}
最近推送: ${detailB.pushed_at || "未知"}
简介: ${detailB.description || detailB.description_raw || b.description || b.description_raw || "暂无描述"}
README 摘要: ${detailB.readme_summary || detailB.readme_summary_raw || "暂无"}`;
}

async function openCompareSelected(){
  const repos = selectedRepos();
  if(repos.length !== 2){
    toast("请先选中 2 个仓库再对比");
    return;
  }
  document.getElementById("compare-body").innerHTML = `<div class="empty">${emptyIcon}<span>正在拉取对比数据...</span></div>`;
  document.getElementById("compare-modal").classList.add("show");
  try{
    const [repoA, repoB] = repos;
    const [detailA, detailB] = await Promise.all([fetchRepoDetails(repoA), fetchRepoDetails(repoB)]);
    comparePrompt = buildComparePrompt(repoA, repoB, detailA, detailB);
    document.getElementById("compare-body").innerHTML = `<div class="notice">对比视图会把两个仓库按同一组维度并排展开，方便从语言、活跃度、README 摘要和项目定位几个层面做快速判断。</div><div class="panel-actions"><button class="action-primary" type="button" onclick="analyzeCompare()">ChatGPT 对比</button></div><div class="compare-grid">${renderCompareCard(repoA, detailA)}${renderCompareCard(repoB, detailB)}</div>`;
  }catch(error){
    comparePrompt = "";
    document.getElementById("compare-body").innerHTML = `<div class="empty">${emptyIcon}<span>${h(error.message || "对比数据加载失败")}</span></div>`;
  }
}

function renderCompareCard(repo, detail){
  return `<article class="compare-card">
    <div class="badges">
      <span class="badge ${gainBadgeClass(repo)}">${h(gainLabel(repo))}</span>
      <span class="badge source">${h(repo.source_label || "GitHub 来源")}</span>
    </div>
    <div class="title">${h(repo.full_name)}</div>
    <div class="desc">${h(detail.description || detail.description_raw || repo.description || repo.description_raw || "暂无描述")}</div>
    <div class="detail-grid">
      <div class="detail-item"><strong>语言</strong><span>${h(repo.language || "未知语言")}</span></div>
      <div class="detail-item"><strong>License</strong><span>${h(detail.license || "未标注")}</span></div>
      <div class="detail-item"><strong>Stars</strong><span class="metric-number">${detail.stars || repo.stars || 0}</span></div>
      <div class="detail-item"><strong>Forks</strong><span class="metric-number">${detail.forks || repo.forks || 0}</span></div>
      <div class="detail-item"><strong>最近推送</strong><span>${h(detail.pushed_at || "未知")}</span></div>
      <div class="detail-item"><strong>Open Issues</strong><span class="metric-number">${detail.open_issues || 0}</span></div>
    </div>
    <div class="desc muted">${h(detail.readme_summary || detail.readme_summary_raw || "暂无 README 摘要")}</div>
    <div class="panel-actions">
      <a class="action-quiet" href="${h(repo.url)}" target="_blank" rel="noopener" data-external-url="${h(repo.url)}">打开 GitHub</a>
    </div>
  </article>`;
}

async function analyzeCompare(){
  if(!comparePrompt){
    toast("当前没有可分析的对比内容");
    return;
  }
  await openChatGPTPrompts([comparePrompt]);
}

async function toggleState(key, url){
  const repo = repoByUrl(url);
  if(!repo) return;
  const {resp, data} = await requestJson(
    "/api/state",
    {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({state:key, enabled:!((userState[key] || []).includes(url)), repo}),
    },
    "保存状态失败",
  );
  if(!resp.ok || !data.ok){
    toast(data.error || "保存失败");
    return;
  }
  userState = data.user_state;
  render();
}

async function batchSetState(stateKey){
  const repos = selectedRepos();
  if(!repos.length){
    toast("请先选中仓库再批量操作");
    return;
  }
  let lastState = null;
  for(const repo of repos){
    const {resp, data} = await requestJson(
      "/api/state",
      {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({state:stateKey, enabled:true, repo}),
      },
      "批量操作失败",
    );
    if(!resp.ok || !data.ok){
      toast(data.error || "批量操作失败");
      return;
    }
    if(data.user_state) lastState = data.user_state;
  }
  if(lastState) userState = lastState;
  const label = (INITIAL.states || []).find(state => state.key === stateKey)?.label || stateKey;
  render();
  toast(`已将 ${repos.length} 个仓库加入“${label}”`);
}

async function clearFavoriteUpdates(){
  if(!(userState.favorite_updates || []).length){
    toast("当前没有收藏更新记录");
    return;
  }
  if(!window.confirm("确认清空收藏更新记录吗？")) return;
  const {resp, data} = await requestJson("/api/favorite-updates/clear", {method:"POST"}, "清空收藏更新记录失败");
  if(!resp.ok || !data.ok){
    toast(data.error || "清空失败");
    return;
  }
  userState = data.user_state;
  render();
  toast(data.message || "已清空收藏更新记录");
}
"""
    """
async function refreshNow(){
  try{
    const {resp, data} = await requestJson("/api/refresh", {method:"POST"}, "刷新请求失败");
    if(!resp.ok || !data.ok){
      toast(data.error || "刷新失败");
      return;
    }
    currentNote = data.message || "已开始后台刷新。";
    render();
    poll();
  }catch(error){
    toast(error.message || "刷新失败");
  }
}

function poll(){
  clearInterval(window.__pollTimer);
  window.__pollTimer = setInterval(async() => {
    try{
      const {resp, data} = await requestJson(`/api/status?ts=${Date.now()}`, {cache:"no-store"}, "状态轮询失败");
      if(!resp.ok){
        currentNote = data.error || "状态获取失败";
        document.getElementById("note").textContent = currentNote;
        return;
      }
      currentNote = data.refreshing ? "后台刷新中..." : (data.error || "已显示最新数据");
      document.getElementById("note").textContent = currentNote;
      if(!data.refreshing){
        clearInterval(window.__pollTimer);
        location.reload();
      }
    }catch(error){
      currentNote = error.message || "状态轮询失败";
      document.getElementById("note").textContent = currentNote;
    }
  }, 1500);
}

async function hideToTray(){
  try{
    const {resp, data} = await requestJson("/api/window/hide", {method:"POST"}, "隐藏到托盘失败");
    if(!resp.ok || !data.ok){
      toast(data.error || data.message || "隐藏到托盘失败");
      return;
    }
    toast(data.message || "已隐藏到系统托盘");
    setTimeout(() => window.close(), 150);
  }catch(error){
    toast(error.message || "隐藏到托盘失败");
  }
}

async function exitApp(){
  if(!window.confirm("确认直接退出 GitSonar 吗？")) return;
  try{
    const {resp, data} = await requestJson("/api/window/exit", {method:"POST"}, "退出程序失败");
    if(!resp.ok || !data.ok){
      toast(data.error || data.message || "退出程序失败");
      return;
    }
    toast(data.message || "正在退出程序");
    setTimeout(() => window.close(), 150);
  }catch(error){
    toast(error.message || "退出程序失败");
  }
}

async function openSettings(){
  try{
    const {resp, data} = await requestJson("/api/settings", {cache:"no-store"}, "读取设置失败");
    if(resp.ok) settings = data;
  }catch(_err){}
  document.getElementById("setting-token").value = settings.github_token || "";
  document.getElementById("setting-proxy").value = settings.proxy || "";
  document.getElementById("setting-refresh-hours").value = settings.refresh_hours || 1;
  document.getElementById("setting-result-limit").value = settings.result_limit || 25;
  document.getElementById("setting-port").value = settings.port || 8080;
  document.getElementById("setting-close-behavior").value = settings.close_behavior || "tray";
  document.getElementById("setting-auto-start").checked = !!settings.auto_start;
  document.getElementById("settings-runtime-hint").textContent = `当前生效端口 ${settings.effective_port || settings.port || 8080} · 当前代理 ${settings.effective_proxy || "未启用"} · 当前关闭行为 ${closeBehaviorLabel(settings.close_behavior)} · 程序不提供 VPN${settings.restart_required ? " · 修改端口后需重启生效" : ""}`;
  document.getElementById("settings-modal").classList.add("show");
}

function closeSettings(){
  document.getElementById("settings-modal").classList.remove("show");
}

async function saveSettings(){
  const payload = {
    github_token:document.getElementById("setting-token").value,
    proxy:document.getElementById("setting-proxy").value,
    refresh_hours:Number(document.getElementById("setting-refresh-hours").value || 1),
    result_limit:Number(document.getElementById("setting-result-limit").value || 25),
    port:Number(document.getElementById("setting-port").value || 8080),
    close_behavior:document.getElementById("setting-close-behavior").value,
    auto_start:document.getElementById("setting-auto-start").checked,
    default_sort:sortPrimary,
  };
  try{
    const {resp, data} = await requestJson(
      "/api/settings",
      {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify(payload),
      },
      "保存设置失败",
    );
    if(!resp.ok || !data.ok){
      toast(data.error || "保存失败");
      return;
    }
    settings = data.settings;
    toast(data.message || "设置已保存");
    closeSettings();
  }catch(error){
    toast(error.message || "保存设置失败");
  }
}

async function openDetail(owner, name, label){
  document.getElementById("detail-modal").classList.add("show");
  document.getElementById("detail-title").textContent = label;
  document.getElementById("detail-body").innerHTML = `<div class="empty">${emptyIcon}<span>正在拉取仓库详情...</span></div>`;
  try{
    const detail = await fetchRepoDetails({owner, name});
    const topics = Array.isArray(detail.topics) ? detail.topics.filter(Boolean) : [];
    document.getElementById("detail-body").innerHTML = `<div class="badges"><span class="badge source">${h(detail.license || "未标注 License")}</span><span class="badge source">${h(detail.default_branch || "未知分支")}</span>${detail.homepage ? `<a class="badge source" href="${h(detail.homepage)}" target="_blank" rel="noopener" data-external-url="${h(detail.homepage)}">Homepage</a>` : ""}</div><div class="desc">${h(detail.description || detail.description_raw || "暂无简介")}</div><div class="meta-line"><span class="meta-pill"><strong>Stars</strong><span class="metric-number">${detail.stars || 0}</span></span><span class="meta-pill"><strong>Forks</strong><span class="metric-number">${detail.forks || 0}</span></span><span class="meta-pill"><strong>Watchers</strong><span class="metric-number">${detail.watchers || 0}</span></span><span class="meta-pill"><strong>Issues</strong><span class="metric-number">${detail.open_issues || 0}</span></span></div><div class="detail-grid"><div class="detail-item"><strong>仓库</strong><span>${h(detail.full_name || label)}</span></div><div class="detail-item"><strong>最近推送</strong><span>${h(detail.pushed_at || "未知")}</span></div><div class="detail-item"><strong>最后更新</strong><span>${h(detail.updated_at || "未知")}</span></div><div class="detail-item"><strong>默认分支</strong><span>${h(detail.default_branch || "未知")}</span></div><div class="detail-item"><strong>License</strong><span>${h(detail.license || "未标注")}</span></div><div class="detail-item"><strong>主页</strong><span>${detail.homepage ? `<a class="link-inline" href="${h(detail.homepage)}" target="_blank" rel="noopener" data-external-url="${h(detail.homepage)}">${h(detail.homepage)}</a>` : "未填写"}</span></div></div><div class="desc muted">${h(detail.readme_summary || detail.readme_summary_raw || "暂无 README 摘要")}</div>${topics.length ? `<div class="topic-list">${topics.map(topic => `<span class="topic">${h(topic)}</span>`).join("")}</div>` : ""}<div class="panel-actions"><a class="action-quiet" href="${h(detail.html_url || "#")}" target="_blank" rel="noopener" data-external-url="${h(detail.html_url || "#")}">打开 GitHub</a></div>`;
  }catch(error){
    document.getElementById("detail-body").innerHTML = `<div class="empty">${emptyIcon}<span>${h(error.message || "详情获取失败")}</span></div>`;
  }
}

function openDetailFromRecord(fullName, url){
  const repo = repoByUrl(url) || (() => {
    const parts = String(fullName || "").split("/");
    return {full_name:fullName, owner:parts[0] || "", name:parts[1] || ""};
  })();
  if(!repo.owner || !repo.name){
    toast("缺少仓库标识");
    return;
  }
  openDetail(repo.owner, repo.name, repo.full_name || fullName);
}

function closeDetail(){
  document.getElementById("detail-modal").classList.remove("show");
}

function closeCompare(){
  document.getElementById("compare-modal").classList.remove("show");
}
"""
    """
document.getElementById("cards").addEventListener("click", event => {
  if(event.target.closest(INTERACTIVE_SELECTOR) || event.target.closest("[data-external-url]")) return;
  const card = event.target.closest("[data-select-url]");
  if(!card) return;
  toggleSelected(card.getAttribute("data-select-url"));
});

document.getElementById("search").value = localStorage.getItem("gtr-search") || "";
document.getElementById("search").addEventListener("input", event => {
  localStorage.setItem("gtr-search", event.target.value);
  render();
});

document.getElementById("language").addEventListener("change", event => {
  languageFilter = event.target.value;
  localStorage.setItem("gtr-language", languageFilter);
  render();
});

document.querySelectorAll("#state-filter-seg [data-value]").forEach(btn => {
  btn.addEventListener("click", () => {
    if(btn.disabled) return;
    setStateFilter(btn.dataset.value || "");
  });
});

document.querySelectorAll("#sort-primary-seg [data-sort-primary]").forEach(btn => {
  btn.addEventListener("click", () => {
    if(btn.disabled) return;
    setSortPrimary(btn.dataset.sortPrimary);
  });
});

document.getElementById("settings-modal").addEventListener("click", event => {
  if(event.target.id === "settings-modal") closeSettings();
});
document.getElementById("detail-modal").addEventListener("click", event => {
  if(event.target.id === "detail-modal") closeDetail();
});
document.getElementById("compare-modal").addEventListener("click", event => {
  if(event.target.id === "compare-modal") closeCompare();
});

document.addEventListener("click", event => {
  const externalTarget = event.target.closest("[data-external-url]");
  if(externalTarget){
    event.preventDefault();
    event.stopPropagation();
    openExternalUrl(externalTarget.getAttribute("data-external-url"));
    return;
  }
  if(!event.target.closest("[data-menu-id]")) closeMenus();
});

window.addEventListener("keydown", event => {
  if(event.key !== "Escape") return;
  closeMenus();
  closeSettings();
  closeDetail();
  closeCompare();
});

render();
if(INITIAL.pending) poll();
</script>
</body>
</html>
"""
)


def build_html(
    *,
    app_name: str,
    snapshot: dict[str, object],
    user_state: dict[str, object],
    settings: dict[str, object],
    periods: list[dict[str, object]],
    states: list[dict[str, object]],
    note: str,
    pending: bool,
) -> str:
    payload = json.dumps(
        {
            "snapshot": snapshot,
            "userState": user_state,
            "settings": settings,
            "periods": periods,
            "states": states,
            "note": note,
            "pending": pending,
        },
        ensure_ascii=False,
    ).replace("</", "<\\/")
    return HTML_TEMPLATE.replace("__APP_NAME__", app_name).replace("__PAYLOAD__", payload)
