const fileInput = document.getElementById('file-input');
const chapterList = document.getElementById('chapter-list');
const chapterTitle = document.getElementById('chapter-title');
const chapterPreview = document.getElementById('chapter-preview');
const errorMessage = document.getElementById('error-message');
const copyButton = document.getElementById('copy-button');
const exportButton = document.getElementById('export-button');
const positionSlider = document.getElementById('position-slider');

let chapters = [];
let activeChapterIndex = -1;
let isSyncingSlider = false;

fileInput.addEventListener('change', async (event) => {
  const [file] = event.target.files;
  if (!file) {
    return;
  }

  resetState();
  showError('正在解析，请稍候…', false);

  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch('/upload', {
      method: 'POST',
      body: formData,
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || '解析失败');
    }
    chapters = payload.chapters;
    populateChapterList(chapters);
    showError('', false);
  } catch (error) {
    showError(error.message || '上传失败');
  } finally {
    fileInput.value = '';
  }
});

function populateChapterList(data) {
  chapterList.innerHTML = '';
  if (!data.length) {
    chapterList.innerHTML = '<p class="empty">未获取到章节</p>';
    return;
  }

  data.forEach((chapter, index) => {
    const button = document.createElement('button');
    button.className = 'chapter-item';
    button.type = 'button';
    button.textContent = chapter.title || `章节 ${index + 1}`;
    button.addEventListener('click', () => selectChapter(index));
    chapterList.appendChild(button);
  });
}

function selectChapter(index) {
  activeChapterIndex = index;
  const chapter = chapters[index];
  chapterTitle.textContent = chapter.title || `章节 ${index + 1}`;
  chapterPreview.textContent = chapter.content || '';
  copyButton.disabled = false;
  exportButton.disabled = false;
  positionSlider.disabled = false;
  positionSlider.value = 0;

  [...chapterList.children].forEach((child, idx) => {
    if (child.classList.contains('chapter-item')) {
      child.classList.toggle('active', idx === index);
    }
  });

  chapterPreview.scrollTop = 0;
}

copyButton.addEventListener('click', async () => {
  if (activeChapterIndex < 0) return;
  try {
    await navigator.clipboard.writeText(chapters[activeChapterIndex].content);
    showError('章节内容已复制到剪贴板', false);
  } catch (error) {
    showError('复制失败，请手动选择文本。');
  }
});

exportButton.addEventListener('click', () => {
  if (activeChapterIndex < 0) return;
  const chapter = chapters[activeChapterIndex];
  const blob = new Blob([chapter.content], { type: 'text/plain;charset=utf-8' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `${chapter.title || '章节'}.txt`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(link.href);
});

positionSlider.addEventListener('input', (event) => {
  if (activeChapterIndex < 0) return;
  isSyncingSlider = true;
  const { scrollHeight, clientHeight } = chapterPreview;
  const maxScroll = scrollHeight - clientHeight;
  const ratio = Number(event.target.value) / 100;
  chapterPreview.scrollTop = maxScroll * ratio;
  window.setTimeout(() => (isSyncingSlider = false), 100);
});

chapterPreview.addEventListener('scroll', () => {
  if (isSyncingSlider || positionSlider.disabled) return;
  const { scrollTop, scrollHeight, clientHeight } = chapterPreview;
  const maxScroll = scrollHeight - clientHeight;
  const ratio = maxScroll > 0 ? scrollTop / maxScroll : 0;
  positionSlider.value = Math.round(ratio * 100);
});

function resetState() {
  chapters = [];
  activeChapterIndex = -1;
  chapterList.innerHTML = '';
  chapterTitle.textContent = '请选择章节';
  chapterPreview.innerHTML = '<p class="placeholder">导入文件后在左侧选择章节进行预览。</p>';
  copyButton.disabled = true;
  exportButton.disabled = true;
  positionSlider.disabled = true;
  positionSlider.value = 0;
}

function showError(message, isError = true) {
  if (!message) {
    errorMessage.hidden = true;
    errorMessage.textContent = '';
    return;
  }
  errorMessage.hidden = false;
  errorMessage.textContent = message;
  errorMessage.classList.toggle('is-info', !isError);
}
