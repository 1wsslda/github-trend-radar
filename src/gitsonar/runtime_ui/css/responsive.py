#!/usr/bin/env python3
from __future__ import annotations

CSS = r"""@media (min-width:1600px){
  .cards{grid-template-columns:repeat(3,minmax(0,1fr))}
}
@media (max-width:1439px){
  .workspace-drawer #control-drawer-list{
    grid-template-columns:1fr 1fr;
  }
  .workspace-action-group{
    gap:10px;
  }
}
@media (max-width:1199px){
  .workspace-bar-main{
    grid-template-columns:1fr;
    align-items:stretch;
  }
  .workspace-bar-main--discover{
    grid-template-columns:1fr;
  }
  .workspace-filter-group,
  .workspace-action-group{
    width:100%;
  }
  .workspace-action-group{
    justify-content:space-between;
    flex-wrap:wrap;
  }
  .workspace-selection-actions{
    justify-content:flex-start;
  }
  .discover-query-row{
    grid-template-columns:1fr;
  }
  .discover-query-main{
    grid-template-columns:1fr;
  }
  .discover-context-grid{
    grid-template-columns:1fr;
  }
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
  .workspace-nav-shell{
    top:8px;
  }
  .workspace-content-shell{
    padding:14px 12px 14px;
  }
  .workspace-bar-main{
    grid-template-columns:1fr;
  }
  .workspace-bar-main--discover{
    grid-template-columns:1fr;
  }
  .workspace-filter-group,
  .workspace-action-group{
    display:grid;
    grid-template-columns:1fr;
    justify-content:stretch;
  }
  .workspace-summary,
  .workspace-selection-actions,
  .workspace-ai-target,
  .workspace-drawer-trigger,
  .action-split{
    width:100%;
  }
  .workspace-summary{
    justify-content:flex-start;
  }
  .workspace-selection-actions{
    justify-content:flex-start;
  }
  .workspace-ai-target{
    max-width:none;
  }
  .workspace-drawer-head{
    grid-template-columns:1fr;
  }
  .workspace-subnav-row{
    flex-wrap:nowrap;
    overflow-x:auto;
    padding-bottom:2px;
  }
  .workspace-subnav-link{
    flex:0 0 auto;
  }
  .discover-top-grid,
  .settings-inline{
    grid-template-columns:1fr;
  }
  .discover-progress-strip,
  .discover-results-toolbar,
  .discover-selection-bar{
    flex-direction:column;
    align-items:flex-start;
  }
  .discover-progress-actions,
  .discover-results-toolbar-actions,
  .discover-selection-actions{
    width:100%;
    justify-content:flex-start;
  }
  .discover-inline-hint-actions{
    width:100%;
    justify-content:flex-start;
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
  .workspace-content-shell,
  .card,
  .update-card,
  .compare-card{
    border-radius:20px;
  }
  .workspace-title{
    font-size:clamp(1.55rem,8vw,2.2rem);
  }
  .workspace-primary-nav{
    flex-wrap:nowrap;
    overflow-x:auto;
    padding-bottom:2px;
  }
  .workspace-primary-link,
  .workspace-subnav-link{
    flex:0 0 auto;
  }
  .workspace-primary-nav::-webkit-scrollbar,
  .workspace-subnav-row::-webkit-scrollbar{
    display:none;
  }
  .discover-query-row{
    grid-template-columns:1fr;
  }
  .discover-query-main{
    grid-template-columns:1fr;
  }
  .action-split{
    width:100%;
  }
  .action-split .split-main{
    min-width:0;
    flex:1;
  }
  .discover-results-toolbar-actions,
  .discover-selection-actions{
    width:100%;
  }
  .workspace-selection-actions{
    width:100%;
  }
  .discover-inline-hint-actions{
    width:100%;
  }
  .workspace-selection-actions > *{
    flex:1 1 auto;
  }
  .discover-results-toolbar-actions > *,
  .discover-selection-actions > *,
  .discover-inline-hint-actions > *{
    flex:1 1 auto;
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
    grid-template-columns:repeat(2,minmax(0,1fr));
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
