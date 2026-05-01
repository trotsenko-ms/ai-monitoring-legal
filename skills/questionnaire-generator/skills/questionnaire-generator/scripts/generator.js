#!/usr/bin/env node

/**
 * Questionnaire Generator
 * Generates interactive HTML forms from JSON question definitions
 */

const fs = require('fs');
const path = require('path');

function generateQuestionnaireHTML(config) {
  const { title, description, questions } = config;
  
  if (!questions || questions.length === 0) {
    throw new Error('No questions provided');
  }
  
  if (questions.length < 3 || questions.length > 8) {
    console.warn(`Warning: questionnaire should have 3-8 questions (you have ${questions.length})`);
  }

  let questionsHTML = '';
  questions.forEach((q, idx) => {
    const qNum = idx + 1;
    questionsHTML += generateQuestionHTML(q, qNum);
  });

  const html = `<html>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: var(--font-sans); }
  .form-container { padding: 1.5rem 0; }
  h2 { font-size: 18px; font-weight: 500; margin-bottom: 1.5rem; color: var(--color-text-primary); }
  .question-block { margin-bottom: 2rem; padding-bottom: 1.5rem; border-bottom: 0.5px solid var(--color-border-tertiary); }
  .question-block:last-child { border-bottom: none; }
  .q-number { font-size: 14px; font-weight: 500; color: var(--color-text-secondary); margin-bottom: 0.5rem; }
  .q-text { font-size: 16px; font-weight: 500; color: var(--color-text-primary); margin-bottom: 1rem; }
  .options-group { display: flex; flex-direction: column; gap: 0.75rem; margin-bottom: 1rem; }
  .option { display: flex; align-items: flex-start; gap: 8px; }
  input[type="radio"], input[type="checkbox"] { margin-top: 4px; cursor: pointer; flex-shrink: 0; }
  label { cursor: pointer; font-size: 14px; color: var(--color-text-primary); }
  input[type="text"], textarea { width: 100%; padding: 8px; border: 0.5px solid var(--color-border-secondary); border-radius: var(--border-radius-md); font-family: var(--font-sans); font-size: 14px; }
  input[type="text"]:focus, textarea:focus { outline: none; border-color: var(--color-border-primary); background: var(--color-background-secondary); }
  textarea { resize: vertical; min-height: 60px; }
  table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
  th, td { padding: 8px; border: 0.5px solid var(--color-border-tertiary); text-align: left; }
  th { background: var(--color-background-secondary); font-weight: 500; }
  input.table-cell { border: none; padding: 4px; }
  .button-group { display: flex; gap: 12px; margin-top: 2rem; }
  button { padding: 8px 16px; border: 0.5px solid var(--color-border-secondary); border-radius: var(--border-radius-md); background: transparent; cursor: pointer; font-size: 14px; font-weight: 500; }
  button:hover { background: var(--color-background-secondary); }
  .success-msg { padding: 12px; background: var(--color-background-info); color: var(--color-text-info); border-radius: var(--border-radius-md); margin-top: 1rem; display: none; }
</style>

<div class="form-container">
  <h2>${title || 'Questionnaire'}</h2>
  ${description ? `<p style="color: var(--color-text-secondary); font-size: 14px; margin-bottom: 1.5rem;">${description}</p>` : ''}
  
  <form id="questionnaire-form">
    ${questionsHTML}
  </form>
  
  <div class="button-group">
    <button onclick="exportAsJSON()">Завантажити JSON</button>
    <button onclick="copyToClipboard()">Копіювати в буфер</button>
    <button onclick="sendToClaude()">Відправити Клауду ↗</button>
  </div>
  
  <div class="success-msg" id="success">✓ Дані скопійовані в буфер обміну</div>
</div>

<script>
function getFormData() {
  const form = document.getElementById('questionnaire-form');
  const data = {};
  
  document.querySelectorAll('[data-question-id]').forEach(el => {
    const qId = el.dataset.questionId;
    const qType = el.dataset.questionType;
    
    if (qType === 'options') {
      data[qId] = document.querySelector(\`input[name="\${qId}"]:checked\`)?.value;
    } else if (qType === 'checkboxes') {
      data[qId] = Array.from(document.querySelectorAll(\`input[name="\${qId}"]:checked\`)).map(e => e.value);
    } else if (qType === 'text') {
      data[qId] = document.getElementById(\`text-\${qId}\`)?.value || '';
    } else if (qType === 'table') {
      const rows = [];
      document.querySelectorAll(\`[data-table-id="\${qId}"] tbody tr\`).forEach(row => {
        const cells = {};
        row.querySelectorAll('input').forEach((input, idx) => {
          cells[\`col\${idx}\`] = input.value;
        });
        rows.push(cells);
      });
      data[qId] = rows;
    }
    
    if (document.getElementById(\`comment-\${qId}\`)) {
      data[\`\${qId}_comment\`] = document.getElementById(\`comment-\${qId}\`).value;
    }
  });
  
  return data;
}

function exportAsJSON() {
  const data = getFormData();
  const json = JSON.stringify(data, null, 2);
  const blob = new Blob([json], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'questionnaire-response.json';
  a.click();
}

function copyToClipboard() {
  const data = getFormData();
  const text = JSON.stringify(data, null, 2);
  navigator.clipboard.writeText(text).then(() => {
    const msg = document.getElementById('success');
    msg.style.display = 'block';
    setTimeout(() => { msg.style.display = 'none'; }, 3000);
  });
}

function sendToClaude() {
  const data = getFormData();
  const text = \`[Відповіді на уточнюючі питання]\\n\${JSON.stringify(data, null, 2)}\`;
  sendPrompt(text);
}

// Auto-add rows to table
document.querySelectorAll('[data-table-id]').forEach(table => {
  const addBtn = document.createElement('button');
  addBtn.type = 'button';
  addBtn.textContent = '+ Додати рядок';
  addBtn.style.marginTop = '8px';
  addBtn.onclick = (e) => {
    e.preventDefault();
    const tbody = table.querySelector('tbody');
    const newRow = document.createElement('tr');
    const colCount = table.querySelector('thead th').length;
    for (let i = 0; i < colCount; i++) {
      const td = document.createElement('td');
      const input = document.createElement('input');
      input.type = 'text';
      input.className = 'table-cell';
      td.appendChild(input);
      newRow.appendChild(td);
    }
    tbody.appendChild(newRow);
  };
  table.parentNode.insertBefore(addBtn, table.nextSibling);
});
</script>
</html>`;

  return html;
}

function generateQuestionHTML(question, qNum) {
  const { id, question: qText, type, options, allowComment, placeholder, columns } = question;
  
  let inputHTML = '';
  
  if (type === 'options') {
    inputHTML = `<div class="options-group" data-question-id="${id}" data-question-type="options">
      ${options.map(opt => `
        <label class="option">
          <input type="radio" name="${id}" value="${opt.value}">
          <span>${opt.label}</span>
        </label>
      `).join('')}
    </div>`;
  } else if (type === 'checkboxes') {
    inputHTML = `<div class="options-group" data-question-id="${id}" data-question-type="checkboxes">
      ${options.map(opt => `
        <label class="option">
          <input type="checkbox" name="${id}" value="${opt.value}">
          <span>${opt.label}</span>
        </label>
      `).join('')}
    </div>`;
  } else if (type === 'text') {
    inputHTML = `<textarea id="text-${id}" placeholder="${placeholder || 'Ваша відповідь...'}" data-question-id="${id}" data-question-type="text"></textarea>`;
  } else if (type === 'table') {
    const headerRow = columns.map(col => `<th>${col}</th>`).join('');
    inputHTML = `<table data-table-id="${id}" data-question-type="table">
      <thead><tr>${headerRow}</tr></thead>
      <tbody>
        <tr>${columns.map(() => '<td><input type="text" class="table-cell"></td>').join('')}</tr>
      </tbody>
    </table>`;
  }
  
  const commentHTML = allowComment ? `<textarea id="comment-${id}" placeholder="Коментар до цього питання (опціонально)..." style="margin-top: 0.75rem; min-height: 40px;"></textarea>` : '';
  
  return `
    <div class="question-block">
      <div class="q-number">Питання ${qNum}</div>
      <div class="q-text">${qText}</div>
      ${inputHTML}
      ${commentHTML}
    </div>
  `;
}

// Main execution
if (require.main === module) {
  const configFile = process.argv[2];
  if (!configFile) {
    console.error('Usage: node generator.js <config.json>');
    process.exit(1);
  }
  
  const config = JSON.parse(fs.readFileSync(configFile, 'utf8'));
  const html = generateQuestionnaireHTML(config);
  console.log(html);
}

module.exports = { generateQuestionnaireHTML };
