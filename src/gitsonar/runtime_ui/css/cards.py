#!/usr/bin/env python3
from __future__ import annotations

CSS = r""".tabs{
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
  color:var(--text-soft);
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
  content-visibility:auto;
  contain-intrinsic-size:360px 280px;
  display:flex;
  flex-direction:column;
  gap:16px;
  padding:22px;
  border-radius:22px;
  border:1px solid rgba(232,214,184,.1);
  background:linear-gradient(180deg, rgba(29,26,21,.95), rgba(21,19,15,.98));
  box-shadow:var(--shadow-soft);
  transition:
    border-color .28s var(--ease-smooth),
    transform .25s var(--ease-smooth),
    box-shadow .32s var(--ease-smooth),
    background .32s var(--ease-smooth);
}
.card.selectable,
.update-card.selectable{
  position:relative;
  isolation:isolate;
  cursor:pointer;
}
.card.selectable > *,
.update-card.selectable > *{
  position:relative;
  z-index:1;
}
.card.selectable::before,
.update-card.selectable::before{
  content:"";
  position:absolute;
  top:-14%;
  bottom:-14%;
  left:-24%;
  width:32%;
  border-radius:inherit;
  background:linear-gradient(
    112deg,
    rgba(233,201,143,0) 24%,
    rgba(241,216,170,.08) 42%,
    rgba(241,216,170,.42) 50%,
    rgba(233,201,143,.12) 58%,
    rgba(233,201,143,0) 76%
  );
  opacity:0;
  pointer-events:none;
  transform:translate3d(-148%, 0, 0) skewX(-18deg);
  z-index:0;
}
@keyframes card-selection-sheen {
  0%{
    opacity:0;
    transform:translate3d(0, 0, 0) skewX(-18deg);
  }
  18%{
    opacity:.16;
  }
  44%{
    opacity:.52;
  }
  100%{
    opacity:0;
    transform:translate3d(420%, 0, 0) skewX(-18deg);
  }
}
.card.selection-enter::before,
.update-card.selection-enter::before{
  animation:card-selection-sheen .68s var(--ease-smooth) 1 forwards;
}
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
    radial-gradient(ellipse at top right, rgba(233,201,143,.14), transparent 62%),
    linear-gradient(180deg, rgba(39,31,20,.97), rgba(21,19,15,.98));
  border-color:rgba(233,201,143,.42);
  box-shadow:
    0 0 0 1px rgba(233,201,143,.18) inset,
    0 14px 34px rgba(66,48,19,.14),
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
@keyframes badge-selection-enter {
  0%{
    opacity:0;
    transform:translateY(4px) scale(.96);
  }
  100%{
    opacity:1;
    transform:translateY(0) scale(1);
  }
}
.badge-selection{
  color:var(--accent);
  border-color:rgba(233,201,143,.22);
  background:rgba(233,201,143,.08);
  animation:badge-selection-enter .32s var(--ease-smooth) forwards;
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
.desc-wrap{
  min-width:0;
  --desc-lines:4;
  --desc-line-height:1.68;
}
.desc{
  margin:0;
  color:var(--text-soft);
  font-size:.91rem;
  line-height:var(--desc-line-height);
  min-height:calc(1em * var(--desc-line-height) * var(--desc-lines));
  display:-webkit-box;
  -webkit-line-clamp:4;
  -webkit-box-orient:vertical;
  overflow:hidden;
}
.desc.muted{color:var(--muted)}
.desc-wrap.is-expandable.is-expanded .desc,
.desc-wrap.is-expandable:hover .desc{
  display:block;
  -webkit-line-clamp:unset;
  overflow:visible;
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
}"""
