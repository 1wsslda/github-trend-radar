#!/usr/bin/env python3
from __future__ import annotations

CSS = r"""@media (min-width:1600px){
  .cards{grid-template-columns:repeat(3,minmax(0,1fr))}
}
@media (max-width:1439px){
  .workspace-bar-main{
    grid-template-columns:minmax(220px,1fr) auto auto;
  }
  .workspace-drawer #control-drawer-list{
    grid-template-columns:1fr 1fr;
  }
  .workspace-summary{
    grid-column:1 / -1;
    grid-template-columns:repeat(2,minmax(0,max-content));
    align-items:center;
  }
}
@media (max-width:1199px){
  .workspace-bar-main{
    grid-template-columns:1fr 1fr;
    align-items:stretch;
  }
  .workspace-search-wrap{
    grid-column:1 / -1;
  }
  .workspace-summary{
    grid-column:auto;
    grid-template-columns:1fr;
  }
  .discover-grid,
  .settings-inline{
    grid-template-columns:1fr;
  }
  .workspace-drawer #control-drawer-list{
    grid-template-columns:1fr;
  }
  .compare-grid{
    grid-template-columns:1fr;
  }
  .cards{
    grid-template-columns:repeat(2,minmax(0,1fr));
  }
}
@media (max-width:959px){
  .page{
    padding:16px 14px 136px;
  }
  .workspace-header{
    grid-template-columns:1fr;
    padding:14px 16px;
  }
  .workspace-status{
    grid-auto-flow:row;
    justify-content:stretch;
  }
  .nav-actions{
    justify-content:flex-start;
  }
  .workspace-bar{
    top:8px;
    padding:10px 12px 12px;
  }
  .workspace-bar-main{
    grid-template-columns:1fr;
  }
  .workspace-summary{
    grid-template-columns:repeat(2,minmax(0,1fr));
  }
  .workspace-drawer-head{
    grid-template-columns:1fr;
  }
  .discover-grid,
  .discover-top-grid,
  .settings-inline{
    grid-template-columns:1fr;
  }
  .panel{
    width:100vw;
  }
}
@media (max-width:759px){
  .page{
    padding:14px 12px 146px;
  }
  .workspace-header,
  .workspace-bar,
  .card,
  .update-card,
  .compare-card{
    border-radius:20px;
  }
  .workspace-title-row{
    align-items:flex-start;
    flex-direction:column;
  }
  .workspace-title{
    font-size:clamp(1.55rem,8vw,2.2rem);
  }
  .workspace-panel-meta{
    width:100%;
  }
  .nav-main{
    flex-wrap:nowrap;
    overflow-x:auto;
    padding-bottom:2px;
  }
  .nav-pill{
    flex:0 0 auto;
  }
  .workspace-summary{
    grid-template-columns:1fr;
  }
  .action-split{
    width:100%;
  }
  .action-split .split-main{
    min-width:0;
    flex:1;
  }
  .cards{
    grid-template-columns:1fr;
  }
  .detail-grid{
    grid-template-columns:1fr;
  }
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
}"""
