"""
4shared Search Tool
====================
Standalone searcher — no pip installs required, Python stdlib only.
Double-click 4shared_search.bat to launch, or run:  python 4shared_search.py
Then open your browser to http://localhost:8888
"""

import os, json, re, threading, webbrowser
import urllib.request, urllib.parse
from flask import Flask, request, jsonify, Response

PORT = 8888
UA   = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36")

# ---------------------------------------------------------------------------
# Embedded GUI
# ---------------------------------------------------------------------------
HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>4shared Search</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
  :root {
    --bg:       #0d0f14;
    --surface:  #161922;
    --border:   #252a35;
    --accent:   #f5a623;
    --accent2:  #e8831a;
    --text:     #e8eaf0;
    --muted:    #6b7280;
    --card-bg:  #1c2030;
    --card-hov: #222840;
    --green:    #34d399;
    --radius:   10px;
  }
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  html { scroll-behavior: smooth; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
    font-size: 15px;
    min-height: 100vh;
  }

  /* ── Header ── */
  header {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 18px 32px;
    display: flex;
    align-items: center;
    gap: 14px;
    position: sticky;
    top: 0;
    z-index: 100;
  }
  .logo-icon {
    width: 36px; height: 36px;
    background: var(--accent);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-family: 'Space Mono', monospace;
    font-weight: 700;
    color: #0d0f14;
    font-size: 14px;
    flex-shrink: 0;
  }
  .logo-text {
    font-family: 'Space Mono', monospace;
    font-size: 16px;
    font-weight: 700;
    letter-spacing: -0.5px;
    color: var(--text);
  }
  .logo-text span { color: var(--accent); }
  .header-sub {
    font-size: 12px;
    color: var(--muted);
    margin-left: auto;
    font-family: 'Space Mono', monospace;
  }

  /* ── Search panel ── */
  .search-panel {
    max-width: 100%;
    background: var(--bg);
    border-bottom: 1px solid var(--border);
    position: sticky;
    top: 73px;   /* height of header */
    z-index: 90;
    padding: 12px 24px;
    margin: 0;
  }
  .search-panel-inner {
    max-width: 1380px;
    margin: 0 auto;
  }
  .search-tagline {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    color: var(--accent);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 8px;
  }
  .search-bar {
    display: flex;
    gap: 10px;
    margin-bottom: 8px;
  }
  .search-bar input[type=text] {
    flex: 1;
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: var(--radius);
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
    font-size: 16px;
    padding: 13px 18px;
    outline: none;
    transition: border-color .2s;
  }
  .search-bar input[type=text]:focus { border-color: var(--accent); }
  .search-bar input[type=text]::placeholder { color: var(--muted); }
  .btn-search {
    background: var(--accent);
    color: #0d0f14;
    border: none;
    border-radius: var(--radius);
    font-family: 'Space Mono', monospace;
    font-size: 13px;
    font-weight: 700;
    padding: 0 24px;
    cursor: pointer;
    transition: background .2s, transform .1s;
    white-space: nowrap;
  }
  .btn-search:hover { background: var(--accent2); }
  .btn-search:active { transform: scale(.97); }

  .filters {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }
  select {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: 8px;
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
    font-size: 14px;
    padding: 9px 14px;
    cursor: pointer;
    outline: none;
    transition: border-color .2s;
  }
  select:focus { border-color: var(--accent); }
  .filter-label {
    font-size: 11px;
    color: var(--muted);
    display: flex;
    align-items: center;
    gap: 6px;
    font-family: 'Space Mono', monospace;
    letter-spacing: .5px;
  }

  /* ── Status bar ── */
  .status-bar {
    max-width: 1380px;
    margin: 12px auto 0;
    padding: 0 24px;
    display: flex;
    align-items: center;
    gap: 12px;
    min-height: 28px;
  }
  .status-text {
    font-family: 'Space Mono', monospace;
    font-size: 12px;
    color: var(--muted);
  }
  .status-text.active { color: var(--accent); }
  .spinner {
    width: 16px; height: 16px;
    border: 2px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin .7s linear infinite;
    display: none;
  }
  .spinner.show { display: block; }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* ── Results grid ── */
  .results-wrap {
    max-width: 1380px;
    margin: 16px auto 0;
    padding: 0 24px 60px;
  }
  .results-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 12px;
  }
  @media (max-width: 1100px) {
    .results-grid { grid-template-columns: repeat(4, 1fr); }
  }
  @media (max-width: 700px) {
    .results-grid { grid-template-columns: repeat(2, 1fr); }
  }

  /* ── Card ── */
  .card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
    transition: border-color .2s, transform .2s, background .2s;
    animation: fadeIn .3s ease forwards;
    opacity: 0;
  }
  .card:hover {
    border-color: var(--accent);
    transform: translateY(-2px);
    background: var(--card-hov);
  }
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  .card-thumb {
    width: 100%;
    aspect-ratio: 4/3;
    background: var(--border);
    background-size: cover;
    background-position: center;
    position: relative;
    overflow: hidden;
  }
  .card-thumb-placeholder {
    width: 100%;
    aspect-ratio: 4/3;
    background: var(--surface);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 32px;
    color: var(--border);
  }
  .card-ext-badge {
    position: absolute;
    top: 8px; right: 8px;
    background: rgba(0,0,0,.75);
    color: var(--accent);
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    font-weight: 700;
    padding: 3px 7px;
    border-radius: 4px;
    text-transform: uppercase;
  }
  .card-body {
    padding: 12px;
  }
  .card-name {
    font-size: 13px;
    font-weight: 500;
    color: var(--text);
    word-break: break-word;
    line-height: 1.4;
    margin-bottom: 8px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  .card-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 10px;
  }
  .meta-pill {
    font-size: 11px;
    color: var(--muted);
    background: var(--bg);
    border-radius: 4px;
    padding: 2px 7px;
    font-family: 'Space Mono', monospace;
  }
  .meta-pill.date { color: #7dd3fc; }
  .meta-pill.size { color: var(--green); }
  .card-owner {
    font-size: 12px;
    color: var(--muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-bottom: 10px;
  }
  .card-owner span { color: var(--text); }
  .card-actions {
    display: flex;
    gap: 7px;
  }
  .btn-open {
    flex: 1;
    background: var(--accent);
    color: #0d0f14;
    border: none;
    border-radius: 7px;
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    padding: 7px 10px;
    cursor: pointer;
    text-decoration: none;
    text-align: center;
    transition: background .15s;
    display: flex; align-items: center; justify-content: center; gap: 5px;
  }
  .btn-open:hover { background: var(--accent2); }
  .btn-folder {
    flex: 1;
    background: transparent;
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 7px;
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    padding: 7px 10px;
    cursor: pointer;
    text-decoration: none;
    text-align: center;
    transition: border-color .15s, color .15s;
    display: flex; align-items: center; justify-content: center; gap: 5px;
  }
  .btn-folder:hover { border-color: var(--accent); color: var(--accent); }

  /* ── Load more ── */
  .load-more-wrap {
    text-align: center;
    margin-top: 28px;
  }
  .btn-load-more {
    background: var(--surface);
    color: var(--accent);
    border: 1.5px solid var(--accent);
    border-radius: var(--radius);
    font-family: 'Space Mono', monospace;
    font-size: 13px;
    font-weight: 700;
    padding: 13px 36px;
    cursor: pointer;
    transition: background .2s, color .2s;
    display: none;
  }
  .btn-load-more:hover {
    background: var(--accent);
    color: #0d0f14;
  }
  .btn-load-more.show { display: inline-block; }

  /* ── Empty / error ── */
  .empty-state {
    text-align: center;
    padding: 60px 0;
    color: var(--muted);
    font-family: 'Space Mono', monospace;
    font-size: 13px;
    display: none;
  }
  .empty-state.show { display: block; }
  .empty-icon { font-size: 48px; margin-bottom: 16px; }

  /* ── Toast ── */
  .toast {
    position: fixed;
    bottom: 24px; left: 50%;
    transform: translateX(-50%) translateY(80px);
    background: var(--green);
    color: #0d0f14;
    font-family: 'Space Mono', monospace;
    font-size: 12px;
    font-weight: 700;
    padding: 10px 20px;
    border-radius: 8px;
    transition: transform .3s;
    z-index: 999;
    pointer-events: none;
  }
  .toast.show { transform: translateX(-50%) translateY(0); }

  @media (max-width: 600px) {
    header { padding: 14px 16px; }
    .search-panel { padding: 10px 14px; top: 61px; }
    .status-bar, .results-wrap { padding: 0 14px; }
    .search-bar { flex-direction: column; }
    .btn-search { padding: 13px; }
  }
</style>
</head>
<body>

<header>
  <div class="logo-icon">4S</div>
  <div class="logo-text">4shared <span>Search</span></div>
  <div class="header-sub">// archive browser</div>
</header>

<div class="search-panel">
  <div class="search-panel-inner">
  <div class="search-tagline">&#9632; find anything</div>
  <div class="search-bar">
    <input type="text" id="query" placeholder="e.g. 20240201  or  WA0001  or  Camera Roll" autocomplete="off">
    <button class="btn-search" onclick="doSearch()">SEARCH</button>
  </div>
  <div class="filters">
    <span class="filter-label">TYPE</span>
    <select id="category">
      <option value="0">All Files</option>
      <option value="3" selected>Images</option>
      <option value="2">Video</option>
      <option value="1">Music</option>
      <option value="4">Archives</option>
      <option value="5">Books</option>
      <option value="8">Apps</option>
    </select>
    <span class="filter-label">SORT</span>
    <select id="sort">
      <option value="time,desc">Newest First</option>
      <option value="downloads,desc">Most Downloaded</option>
      <option value="time,asc">Oldest First</option>
      <option value="name,asc">A – Z</option>
      <option value="name,desc">Z – A</option>
      <option value="size,desc">Largest First</option>
      <option value="size,asc">Smallest First</option>
    </select>
  </div>
  </div>
</div>

<div class="status-bar">
  <div class="spinner" id="spinner"></div>
  <div class="status-text" id="status">Ready — enter a search term above</div>
</div>

<div class="results-wrap">
  <div class="results-grid" id="grid"></div>
  <div class="empty-state" id="empty">
    <div class="empty-icon">🗂</div>
    No results found. Try a different search term or category.
  </div>
  <div class="load-more-wrap">
    <button class="btn-load-more" id="btnMore" onclick="loadMore()">LOAD MORE</button>
  </div>
</div>

<div class="toast" id="toast">Copied!</div>

<script>
let nextOffset  = 0;
let currentQuery  = '';
let currentCat    = '3';
let currentSort   = 'time,desc';
let totalLoaded   = 0;
let isLoading     = false;

const grid    = document.getElementById('grid');
const spinner = document.getElementById('spinner');
const status  = document.getElementById('status');
const btnMore = document.getElementById('btnMore');
const empty   = document.getElementById('empty');
const toast   = document.getElementById('toast');

document.getElementById('query').addEventListener('keydown', e => {
  if (e.key === 'Enter') doSearch();
});

function doSearch() {
  const q = document.getElementById('query').value.trim();
  currentQuery  = q;
  currentCat    = document.getElementById('category').value;
  currentSort   = document.getElementById('sort').value;
  nextOffset    = 0;
  totalLoaded   = 0;
  grid.innerHTML = '';
  empty.classList.remove('show');
  btnMore.classList.remove('show');
  fetchResults(3);
}

function loadMore() {
  fetchResults(3);
}

function fetchResults(pages) {
  if (isLoading) return;
  isLoading = true;
  spinner.classList.add('show');
  status.textContent = totalLoaded === 0 ? 'Searching...' : 'Loading more...';
  status.className = 'status-text active';
  btnMore.classList.remove('show');

  const params = new URLSearchParams({
    q:        currentQuery,
    category: currentCat,
    sort:     currentSort,
    offset:   nextOffset,
    pages:    pages
  });

  fetch('/search?' + params)
    .then(r => r.json())
    .then(data => {
      isLoading = false;
      spinner.classList.remove('show');

      if (data.error) {
        status.textContent = 'Error: ' + data.error;
        status.className = 'status-text';
        return;
      }

      const cards = data.results || [];
      totalLoaded += cards.length;
      nextOffset  += pages * 12;

      if (totalLoaded === 0 && cards.length === 0) {
        empty.classList.add('show');
        status.textContent = 'No results found';
        status.className = 'status-text';
        return;
      }

      cards.forEach((c, i) => {
        grid.appendChild(buildCard(c, i));
      });

      const qLabel = currentQuery ? `"${currentQuery}"` : 'all files';
      status.textContent = `Showing ${totalLoaded} result(s)  •  ${qLabel}`;
      status.className = 'status-text';

      if (cards.length >= 12) {
        btnMore.classList.add('show');
      }
    })
    .catch(err => {
      isLoading = false;
      spinner.classList.remove('show');
      status.textContent = 'Network error — is the server running?';
      status.className = 'status-text';
    });
}

const EXT_ICONS = {
  jpg: '🖼', jpeg: '🖼', png: '🖼', gif: '🖼', webp: '🖼',
  mp4: '🎬', mov: '🎬', avi: '🎬', mkv: '🎬',
  mp3: '🎵', m4a: '🎵', wav: '🎵',
  zip: '📦', rar: '📦', '7z': '📦',
  pdf: '📄', doc: '📄', docx: '📄',
};

function buildCard(c, idx) {
  const div = document.createElement('div');
  div.className = 'card';
  div.style.animationDelay = (idx % 12 * 40) + 'ms';

  const ext = (c.name || '').split('.').pop().toLowerCase();
  const icon = EXT_ICONS[ext] || '📁';

  let thumbHTML = '';
  if (c.thumb) {
    thumbHTML = `<div class="card-thumb" style="background-image:url('${c.thumb}')">
      <span class="card-ext-badge">${ext}</span>
    </div>`;
  } else {
    thumbHTML = `<div class="card-thumb-placeholder">
      ${icon}
      <span class="card-ext-badge" style="position:absolute;top:8px;right:8px;">${ext}</span>
    </div>`;
  }

  const fileUrl    = c.url || '#';
  const folderUrl  = c.folder_url || '';
  const filename   = c.name || 'download';
  const thumbUrl   = c.thumb || '';

  const IMAGE_EXT  = ['jpg','jpeg','png','gif','webp','bmp','tif','tiff'];
  const VIDEO_EXT  = ['mp4','mov','avi','mkv','webm','3gp','mpg','mpeg','wmv','flv'];
  const isImage    = IMAGE_EXT.includes(ext);
  const isVideo    = VIDEO_EXT.includes(ext);

  // For videos build the /get/ URL from the file page URL
  const getUrl     = fileUrl.replace(/\/(photo|video|zip|rar|archive|mp3|audio|file)\//i, '/get/');

  let folderBtn = '';
  if (folderUrl) {
    folderBtn = `<button class="btn-folder" onclick="copyFolder('${folderUrl}')">📋 Folder</button>`;
  }

  let downloadBtn = '';
  if (isImage) {
    downloadBtn = `<button class="btn-folder" onclick="startDownload(this,'${encodeURIComponent(fileUrl)}','${encodeURIComponent(filename)}','${encodeURIComponent(thumbUrl)}')" style="flex:1;text-align:center;">⬇ Download</button>`;
  }

  div.innerHTML = `
    ${thumbHTML}
    <div class="card-body">
      <div class="card-name" title="${c.name || ''}">${c.name || 'Unknown'}</div>
      <div class="card-meta">
        ${c.size ? `<span class="meta-pill size">${c.size}</span>` : ''}
        ${c.date ? `<span class="meta-pill date">${c.date}</span>` : ''}
      </div>
      <div class="card-owner">by <span>${c.owner || 'Unknown'}</span></div>
      <div class="card-actions">
        <a class="btn-open" href="${fileUrl}" target="_blank">↗ Open</a>
        ${folderBtn}
      </div>
      ${downloadBtn ? `<div class="card-actions" style="margin-top:6px;">${downloadBtn}</div>` : ''}
    </div>
  `;
  return div;
}

function startDownload(btn, encodedUrl, encodedFilename, encodedThumb) {
  const orig = btn.textContent;
  btn.textContent = '⏳ Fetching...';
  btn.disabled = true;
  const params = new URLSearchParams({
    file_url: encodedUrl,
    filename: encodedFilename,
    thumb:    encodedThumb || ''
  });
  fetch('/download?' + params)
    .then(r => {
      if (!r.ok) return r.json().then(d => { throw new Error(d.error || 'Failed'); });
      return r.blob();
    })
    .then(blob => {
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = decodeURIComponent(encodedFilename);
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      btn.textContent = '✅ Done!';
      setTimeout(() => { btn.textContent = orig; btn.disabled = false; }, 3000);
    })
    .catch(err => {
      btn.textContent = '❌ Failed';
      btn.disabled = false;
      setTimeout(() => { btn.textContent = orig; btn.disabled = false; }, 3000);
      showToast('Download failed: ' + err.message);
    });
}

function copyFolder(url) {
  if (!url) return;
  if (navigator.clipboard) {
    navigator.clipboard.writeText(url).then(() => showToast('Folder URL copied!'));
  } else {
    const ta = document.createElement('textarea');
    ta.value = url;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    showToast('Folder URL copied!');
  }
}

function showToast(msg) {
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2200);
}
</script>
</body>
</html>"""

# ---------------------------------------------------------------------------
# 4shared HTML parser (stdlib only)
# ---------------------------------------------------------------------------

def parse_cards(html: str):
    """Extract file cards from 4shared search results HTML using regex."""
    cards = []
    blocks = re.split(r'(?=<div[^>]+class="[^"]*jsCardItem[^"]*")', html)

    for block in blocks[1:]:
        card = {}

        # File page URL
        m = re.search(r'class="[^"]*jsGoFile[^"]*"\s+href="([^"]+)"', block)
        if not m:
            m = re.search(r'href="([^"]+)"\s+class="[^"]*jsGoFile[^"]*"', block)
        if m:
            card['url'] = m.group(1)

        # Filename
        m = re.search(r'jsFileName[^>]*>\s*(.*?)\s*</div>', block, re.DOTALL)
        if m:
            card['name'] = re.sub(r'<[^>]+>', '', m.group(1)).strip()

        # Size (non-mob-only)
        m = re.search(r'class="[^"]*jsFileSize[^"]*(?<!mob-only)[^"]*"[^>]*>\s*([^<]+?)\s*</div>', block)
        if m:
            card['size'] = m.group(1).strip()

        # Date
        m = re.search(r'jsUploadTime[^>]*>\s*([^<]+?)\s*</div>', block)
        if m:
            card['date'] = m.group(1).strip()

        # Owner name
        m = re.search(r'jsUserInfo[^>]*>.*?<span>\s*([^<]+?)\s*</span>', block, re.DOTALL)
        if not m:
            m = re.search(r'jsUserInfo[^>]*>\s*([^<\n]+?)\s*<i', block)
        if m:
            card['owner'] = re.sub(r'<[^>]+>', '', m.group(1)).strip()

        # Folder URL
        m = re.search(r'href="(/folder/[A-Za-z0-9_\-]+/[^"]+)"[^>]*class="[^"]*jsFolderInfo', block)
        if not m:
            m = re.search(r'class="[^"]*jsFolderInfo[^"]*"[^>]*href="(/folder/[A-Za-z0-9_\-]+/[^"]+)"', block)
        if m:
            path = m.group(1)
            card['folder_url'] = 'https://www.4shared.com' + path if not path.startswith('http') else path

        # Thumbnail (background-image in style)
        m = re.search(r'jsFileThumbOverlay[^>]+background-image:\s*url\([\'"]?([^\'")\s]+)[\'"]?\)', block)
        if m:
            card['thumb'] = m.group(1)

        if card.get('name'):
            cards.append(card)

    return cards


def _parse_media_url_from_html(html: str):
    """Extract direct media/download URL from a 4shared file detail page."""
    # Full image preview
    m = re.search(r'class="jsFilePreviewImage"[^>]+src=[\'"]([^\'"]+)[\'"]', html)
    if not m:
        m = re.search(r'src=[\'"]([^\'"]+)[\'"][^>]*class="jsFilePreviewImage"', html)
    if m:
        return m.group(1)
    # Video src
    m = re.search(r'<video[^>]+src=[\'"]([^\'"]+)[\'"]', html)
    if m:
        return m.group(1)
    m = re.search(r'<source[^>]+src=[\'"]([^\'"]+)[\'"]', html)
    if m:
        return m.group(1)
    # Direct download link (logged-in session token)
    m = re.search(r'id="jsDirectDownloadLink"[^>]+value=[\'"]([^\'"]+)[\'"]', html)
    if not m:
        m = re.search(r'value=[\'"]([^\'"]+)[\'"][^>]*id="jsDirectDownloadLink"', html)
    if m:
        return m.group(1)
    # CDN URL fallback
    m = re.search(r'https://dc\d+\.4shared\.com/(?:download|img)/[^\s"\'&]+', html)
    if m:
        return m.group(0)
    return None


def fetch_search(query: str, category: str, sort: str, offset: int, pages: int = 1):
    all_cards = []
    seen_urls = set()
    for i in range(pages):
        p = {'category': category, 'sort': sort, 'offset': offset + (i * 12)}
        if query:
            p['query'] = query
        params = urllib.parse.urlencode(p)
        url = f"https://www.4shared.com/web/q?{params}"
        req = urllib.request.Request(url, headers={
            'User-Agent': UA,
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode('utf-8', errors='replace')
        cards = parse_cards(html)
        for c in cards:
            url = c.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_cards.append(c)
        if len(cards) < 12:
            break  # no more results
    return all_cards


# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------

app = Flask(__name__)


@app.route('/')
def index():
    return Response(HTML_PAGE, mimetype='text/html')


@app.route('/search')
def search():
    query    = request.args.get('q',        '').strip()
    category = request.args.get('category', '0')
    sort     = request.args.get('sort',     'time,desc')
    offset   = int(request.args.get('offset', 0))
    pages    = int(request.args.get('pages',  1))
    try:
        results = fetch_search(query, category, sort, offset, pages)
        return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error': str(e), 'results': []})


@app.route('/download')
def download():
    file_url = urllib.parse.unquote(request.args.get('file_url', '').strip())
    filename = urllib.parse.unquote(request.args.get('filename',  'download').strip())
    thumb    = urllib.parse.unquote(request.args.get('thumb',     '').strip())

    if not file_url:
        return jsonify({'error': 'No file_url provided'}), 400

    IMAGE_EXT = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tif', '.tiff'}
    ext = os.path.splitext(filename)[1].lower()

    try:
        if ext in IMAGE_EXT and thumb:
            media_url = re.sub(r'\?.*$', '', thumb)
        else:
            req = urllib.request.Request(file_url, headers={
                'User-Agent': UA,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            })
            with urllib.request.urlopen(req, timeout=20) as resp:
                page_html = resp.read().decode('utf-8', errors='replace')
            media_url = _parse_media_url_from_html(page_html)

        if not media_url:
            return jsonify({'error': 'Could not find download URL for this file'}), 500

        dl_req = urllib.request.Request(media_url, headers={'User-Agent': UA})
        with urllib.request.urlopen(dl_req, timeout=60) as dl_resp:
            content_type = dl_resp.headers.get('Content-Type', 'application/octet-stream')
            data = dl_resp.read()

        if b'<html' in data[:200].lower() or b'<!doctype' in data[:200].lower():
            return jsonify({'error': 'File requires login to download — try the Open button instead'}), 500

        safe_name = re.sub(r'[^\w\.\- ]', '_', filename)
        return Response(
            data,
            mimetype=content_type,
            headers={'Content-Disposition': f'attachment; filename="{safe_name}"'}
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8888))
    # Local run — open browser automatically
    if os.environ.get('RENDER') is None:
        def open_browser():
            import time; time.sleep(0.8)
            webbrowser.open(f'http://localhost:{port}')
        threading.Thread(target=open_browser, daemon=True).start()
        print(f"╔══════════════════════════════════════╗")
        print(f"║      4shared Search Tool             ║")
        print(f"║  http://localhost:{port}               ║")
        print(f"║  Press Ctrl+C to stop                ║")
        print(f"╚══════════════════════════════════════╝")
    app.run(host='0.0.0.0', port=port, debug=False)