import fs from 'fs/promises';
import path from 'path';
import { marked } from '../../../../../node_modules/marked/lib/marked.esm.js';

const repoRoot = '/Users/evren/throughline-symbolic-os/Developer/evren-pcp/projects/ist505';
const docsDir = path.join(repoRoot, 'docs');
const outDir = path.join(repoRoot, 'share', '2026-03-28-group-packet');

const docs = [
  {
    source: 'GROUP_SHARE_PACKET_2026-03-28.md',
    outName: '01-IST505-Group-Packet',
    title: 'IST 505 Group Packet',
    subtitle: 'Shareable summary for the research group',
  },
  {
    source: 'PHASE3_DRAFT_2026-03-28.md',
    outName: '02-IST505-Phase3-Draft',
    title: 'IST 505 Phase 3 Draft',
    subtitle: 'Submission-shaped draft from current repo materials',
  },
  {
    source: 'PHASE3_ASSET_CHECKLIST_2026-03-28.md',
    outName: '03-IST505-Asset-Checklist',
    title: 'IST 505 Asset Checklist',
    subtitle: 'Remaining visuals, citations, and decisions before submission',
  },
];

function stripLocalLinks(markdown) {
  return markdown.replace(/\[([^\]]+)\]\((\/Users\/[^)]+)\)/g, '$1');
}

function wrapHtml({ title, subtitle, body }) {
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>${title}</title>
  <style>
    @page {
      size: Letter;
      margin: 0.7in;
    }
    :root {
      --bg: #f7f3eb;
      --paper: #fffdf8;
      --ink: #1b1d22;
      --muted: #5f6470;
      --line: #d9d0bf;
      --accent: #1e5aa8;
      --accent-soft: #e7f0fb;
      --warm: #a06b2c;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background: var(--bg);
      color: var(--ink);
      line-height: 1.55;
      font-size: 11pt;
    }
    .page {
      max-width: 8.5in;
      margin: 0 auto;
      background: var(--paper);
      padding: 0.35in 0.45in 0.45in;
    }
    header {
      border-bottom: 2px solid var(--line);
      padding-bottom: 0.18in;
      margin-bottom: 0.24in;
    }
    header h1 {
      margin: 0;
      font-size: 22pt;
      line-height: 1.15;
      color: var(--accent);
      font-weight: 700;
    }
    header p {
      margin: 0.08in 0 0;
      color: var(--muted);
      font-size: 10.5pt;
    }
    h1, h2, h3 {
      page-break-after: avoid;
      break-after: avoid;
      line-height: 1.2;
    }
    h1 {
      font-size: 18pt;
      margin: 0.26in 0 0.12in;
      color: var(--accent);
    }
    h2 {
      font-size: 14pt;
      margin: 0.24in 0 0.1in;
      padding-bottom: 0.04in;
      border-bottom: 1px solid var(--line);
      color: #24334f;
    }
    h3 {
      font-size: 11.8pt;
      margin: 0.16in 0 0.05in;
      color: #463928;
    }
    p, ul, ol, table, blockquote {
      margin: 0.08in 0 0.12in;
    }
    ul, ol {
      padding-left: 0.24in;
    }
    li {
      margin: 0.04in 0;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 10.2pt;
    }
    th, td {
      border: 1px solid var(--line);
      padding: 8px 9px;
      vertical-align: top;
      text-align: left;
    }
    th {
      background: var(--accent-soft);
      font-weight: 700;
    }
    code {
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 0.92em;
      background: #f0ede6;
      padding: 0 4px;
      border-radius: 3px;
    }
    pre {
      background: #f4efe6;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      overflow: auto;
      font-size: 9.6pt;
    }
    blockquote {
      border-left: 4px solid var(--warm);
      padding: 0.02in 0 0.02in 0.16in;
      color: #4b4f57;
      background: #fbf7ef;
    }
    hr {
      border: none;
      border-top: 1px solid var(--line);
      margin: 0.18in 0;
    }
    .footer {
      margin-top: 0.28in;
      color: var(--muted);
      font-size: 9pt;
      border-top: 1px solid var(--line);
      padding-top: 0.1in;
    }
  </style>
</head>
<body>
  <main class="page">
    <header>
      <h1>${title}</h1>
      <p>${subtitle}</p>
    </header>
    ${body}
    <div class="footer">Prepared from local IST505 project materials on March 28, 2026.</div>
  </main>
</body>
</html>`;
}

async function buildIndex(pages) {
  const items = pages.map((page) => `
    <tr>
      <td><strong>${page.title}</strong></td>
      <td>${page.subtitle}</td>
      <td><a href="./${page.outName}.html">${page.outName}.html</a></td>
      <td><a href="./${page.outName}.pdf">${page.outName}.pdf</a></td>
    </tr>
  `).join('');

  const body = `
    <h2>Contents</h2>
    <p>This folder is the cleaned share package for the IST505 group.</p>
    <table>
      <thead>
        <tr><th>Document</th><th>Purpose</th><th>HTML</th><th>PDF</th></tr>
      </thead>
      <tbody>${items}</tbody>
    </table>
  `;

  const html = wrapHtml({
    title: 'IST 505 Share Folder',
    subtitle: 'Curated packet for Google Drive sharing',
    body,
  });

  await fs.writeFile(path.join(outDir, 'INDEX.html'), html, 'utf8');
}

async function main() {
  await fs.mkdir(outDir, { recursive: true });

  const rendered = [];
  for (const doc of docs) {
    const sourcePath = path.join(docsDir, doc.source);
    const raw = await fs.readFile(sourcePath, 'utf8');
    const cleaned = stripLocalLinks(raw);
    const body = marked.parse(cleaned);
    const html = wrapHtml({ title: doc.title, subtitle: doc.subtitle, body });
    await fs.writeFile(path.join(outDir, `${doc.outName}.html`), html, 'utf8');
    rendered.push(doc);
  }

  await buildIndex(rendered);
}

await main();
