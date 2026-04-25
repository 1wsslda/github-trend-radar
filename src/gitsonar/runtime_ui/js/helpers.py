#!/usr/bin/env python3
from __future__ import annotations

JS = r"""function h(value){
  return String(value ?? "").replace(/[&<>"']/g, char => {
    if(char === "&") return "&amp;";
    if(char === "<") return "&lt;";
    if(char === ">") return "&gt;";
    if(char === '"') return "&quot;";
    return "&#39;";
  });
}

function formatDisplayTime(value){
  function pad2(part){
    return String(part).padStart(2, "0");
  }
  function formatLocalDate(date){
    return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())} ${pad2(date.getHours())}:${pad2(date.getMinutes())}:${pad2(date.getSeconds())}`;
  }
  if(value === null || value === undefined) return "";
  if(value instanceof Date){
    return Number.isNaN(value.getTime()) ? String(value) : formatLocalDate(value);
  }
  const text = String(value).trim();
  if(!text) return "";
  const localMatch = /^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})(?:\.\d+)?$/.exec(text);
  if(localMatch){
    return `${localMatch[1]}-${localMatch[2]}-${localMatch[3]} ${localMatch[4]}:${localMatch[5]}:${localMatch[6]}`;
  }
  if(/(?:Z|[+-]\d{2}:?\d{2})$/i.test(text)){
    const parsed = new Date(text);
    if(!Number.isNaN(parsed.getTime())) return formatLocalDate(parsed);
  }
  return text;
}

function sleep(ms){
  return new Promise(resolve => setTimeout(resolve, ms));
}

function toast(message){
  const text = String(message || "").trim();
  if(!text) return;
  const node = document.getElementById("toast");
  node.textContent = text;
  node.classList.add("show");
  clearTimeout(window.__toastTimer);
  const duration = Math.min(5200, Math.max(2400, text.length * 70));
  window.__toastTimer = setTimeout(() => node.classList.remove("show"), duration);
}

function localApiOptions(options){
  const next = {...(options || {})};
  const headers = new Headers(next.headers || {});
  if(controlToken){
    headers.set(CONTROL_TOKEN_HEADER, controlToken);
  }
  next.headers = headers;
  return next;
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
    resp = await fetch(url, localApiOptions(options));
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

function isTerminalDiscoveryJob(job){
  return ["completed","failed","cancelled"].includes(String(job?.status || "").trim());
}

function applyActiveDiscoveryJob(job){
  activeDiscoveryJob = job && job.id ? job : null;
  discoveryBusy = !!(activeDiscoveryJob && !isTerminalDiscoveryJob(activeDiscoveryJob));
  if(activeDiscoveryJob){
    const elapsed = Number(activeDiscoveryJob.elapsed_seconds || 0);
    discoveryStartedAt = Date.now() - (Number.isFinite(elapsed) ? elapsed * 1000 : 0);
  }else{
    discoveryStartedAt = 0;
  }
}"""
