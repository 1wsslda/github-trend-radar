#!/usr/bin/env python3
from __future__ import annotations

CSS = r""".toast{
  position:fixed;
  right:20px;
  bottom:calc(26px + env(safe-area-inset-bottom, 0px));
  max-width:min(420px,calc(100vw - 32px));
  padding:14px 16px;
  border-radius:16px;
  border:1px solid rgba(233,201,143,.18);
  background:rgba(20,17,13,.96);
  color:var(--text);
  box-shadow:var(--shadow-lift);
  opacity:0;
  transform:translateY(16px);
  transition:
    opacity .3s var(--ease-smooth),
    transform .3s var(--ease-smooth),
    bottom .25s var(--ease-smooth);
  pointer-events:none;
  z-index:70;
}
.toast.show{
  opacity:1;
  transform:translateY(0);
}

.workspace-back-to-top{
  position:fixed;
  right:20px;
  bottom:calc(94px + env(safe-area-inset-bottom, 0px));
  z-index:47;
  display:inline-flex;
  align-items:center;
  justify-content:center;
  width:52px;
  height:52px;
  padding:0;
  border:1px solid rgba(232,214,184,.14);
  border-radius:999px;
  background:rgba(20,17,13,.92);
  color:var(--text);
  box-shadow:var(--shadow);
  opacity:0;
  visibility:hidden;
  pointer-events:none;
  transform:translateY(10px);
  transition:
    opacity .24s var(--ease-smooth),
    transform .24s var(--ease-smooth),
    visibility .24s var(--ease-smooth),
    background .24s var(--ease-smooth),
    border-color .24s var(--ease-smooth);
}
.workspace-back-to-top svg{
  width:18px;
  height:18px;
}
.workspace-back-to-top:hover{
  border-color:rgba(233,201,143,.24);
  background:rgba(27,23,18,.96);
}
.workspace-back-to-top.is-visible{
  opacity:1;
  visibility:visible;
  pointer-events:auto;
  transform:translateY(0);
}
body.has-batch-dock .workspace-back-to-top{
  bottom:calc(148px + env(safe-area-inset-bottom, 0px));
}

.batch-dock{
  position:fixed;
  left:50%;
  bottom:18px;
  z-index:49;
  display:grid;
  grid-template-columns:auto minmax(0,1fr);
  align-items:center;
  gap:10px 14px;
  width:min(980px,calc(100vw - 28px));
  padding:12px 14px;
  border:1px solid rgba(232,214,184,.14);
  border-radius:22px;
  background:rgba(28,24,18,.88);
  backdrop-filter:blur(14px);
  border-top:1px solid rgba(233,201,143,.22);
  box-shadow:var(--shadow-lift);
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
  line-height:var(--lh-tight);
}
.batch-dock-value{
  color:var(--text);
  font-size:.94rem;
  line-height:var(--lh-tight);
}

.overlay{
  position:fixed;
  inset:0;
  opacity:0;
  visibility:hidden;
  background:rgba(6,5,4,.54);
  backdrop-filter:none;
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
  box-shadow:var(--shadow-lift);
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
  backdrop-filter:none;
  display:grid;
  grid-template-columns:minmax(0,1fr) auto;
  gap:16px;
  align-items:start;
}
.panel-title{
  margin:0 0 8px;
  font-size:1.5rem;
  line-height:var(--lh-heading);
  letter-spacing:-.03em;
  font-weight:650;
}
.panel-body{
  padding:22px 24px 32px;
  overflow-y:auto;
  overscroll-behavior:contain;
  contain:layout paint;
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
  line-height:var(--lh-base);
}
.switch-desc{
  color:var(--muted);
  font-size:.84rem;
  line-height:var(--lh-base);
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
  line-height:var(--lh-base);
}
.topic{
  display:inline-flex;
  align-items:center;
  min-height:28px;
  padding:0 10px;
  border-radius:999px;
  background:rgba(233,201,143,.08);
  border:1px solid transparent;
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
  line-height:var(--lh-relaxed);
}
.detail-section,
.readme-block{
  content-visibility:auto;
  contain-intrinsic-size:260px;
}
.repo-organizer{
  gap:14px;
}
.repo-tag-editor,
.repo-note-editor,
.repo-tag-suggestions{
  display:grid;
  gap:10px;
}
.repo-organizer-row{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:12px;
}
.repo-organizer-caption,
.repo-tag-count,
.repo-note-save-status{
  color:var(--muted);
  font-family:var(--font-mono);
  font-size:10px;
  letter-spacing:.14em;
  line-height:var(--lh-tight);
  text-transform:uppercase;
}
.repo-tag-count{
  color:var(--muted-soft);
}
.repo-tag-list{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  align-items:center;
  min-height:32px;
}
.repo-tag-chip{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  min-height:30px;
  max-width:100%;
  padding:0 11px;
  border:1px solid transparent;
  border-radius:999px;
  background:rgba(233,201,143,.07);
  color:var(--text-soft);
  font-size:.8rem;
  line-height:var(--lh-tight);
  white-space:nowrap;
  transition:
    background .22s var(--ease-smooth),
    border-color .22s var(--ease-smooth),
    color .22s var(--ease-smooth),
    transform .22s var(--ease-smooth);
}
.repo-tag-chip:hover{
  border-color:rgba(233,201,143,.28);
  background:rgba(233,201,143,.12);
  color:var(--text);
  transform:translateY(-1px);
}
.repo-tag-chip.selected{
  border-color:rgba(139,170,132,.32);
  background:rgba(139,170,132,.14);
  color:var(--text);
}
.repo-tag-empty{
  color:var(--muted);
  font-size:.84rem;
  line-height:var(--lh-copy);
}
.repo-tag-input{
  min-height:42px;
}
.repo-note-input{
  min-height:132px;
  padding-top:14px;
  padding-bottom:14px;
  resize:vertical;
  line-height:var(--lh-copy);
}
.repo-note-save-status[data-state="saving"]{color:var(--accent)}
.repo-note-save-status[data-state="saved"]{color:var(--green)}
.repo-note-save-status[data-state="dirty"]{color:var(--amber)}
.repo-note-save-status[data-state="failed"]{color:var(--danger)}
}"""
