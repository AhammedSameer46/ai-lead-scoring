// popup.js - Clean version

const RENDER_URL = 'https://linkedin-lead-finder.onrender.com';

document.getElementById('captureBtn').addEventListener('click', async () => {
  const button = document.getElementById('captureBtn');
  const statusDiv = document.getElementById('status');

  button.disabled = true;
  button.textContent = 'Capturing...';
  statusDiv.className = 'status loading';
  statusDiv.textContent = '🔄 Analyzing post...';

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (!tab.url.includes('linkedin.com')) {
      throw new Error('Please open a LinkedIn post first!');
    }

    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: extractLinkedInPost
    });

    const postData = results[0].result;

    console.log("📦 Extracted Data:", postData);

    if (!postData || !postData.post_content || postData.post_content.length < 50) {
      throw new Error('Post content too short or not found.');
    }

    const response = await fetch(`${RENDER_URL}/api/capture-post`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(postData)
    });

    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }

    const data = await response.json();

    statusDiv.className = 'status success';
    statusDiv.innerHTML = `
      <div class="score-display">
        <span class="score">${data.score}/100</span>
        <span class="tier ${data.tier}">${data.tier.toUpperCase()}</span>
      </div>
      <div style="margin-top: 8px;">
        ✅ Lead captured! Check Telegram.
      </div>
    `;

    button.textContent = '✓ Captured!';

    setTimeout(() => {
      button.disabled = false;
      button.textContent = 'Capture This Post';
    }, 3000);

  } catch (error) {
    console.error('❌ Capture error:', error);

    statusDiv.className = 'status error';
    statusDiv.textContent = `❌ ${error.message}`;

    button.disabled = false;
    button.textContent = 'Capture This Post';
  }
});


// 🔥 CLEAN extraction logic
function extractLinkedInPost() {

  function getPostContent() {
    const selectors = [
      '[data-testid="expandable-text"]',
      '.update-components-text',
      '.break-words'
    ];

    for (let selector of selectors) {
      const el = document.querySelector(selector);
      if (el && el.innerText && el.innerText.length > 50) {
        return el.innerText.trim();
      }
    }

    return '';
  }

  const postContent = getPostContent();

  // Author name
  const authorName =
    document.querySelector('.update-components-actor__name')?.innerText ||
    document.querySelector('.feed-shared-actor__name')?.innerText ||
    '';

  // Author title
  const authorTitle =
    document.querySelector('.update-components-actor__description')?.innerText ||
    document.querySelector('.feed-shared-actor__description')?.innerText ||
    '';

  // Company
  const authorCompany =
    document.querySelector('.feed-shared-actor__sub-description')?.innerText ||
    '';

  return {
    post_content: postContent,
    author_name: authorName.trim(),
    author_title: authorTitle.trim(),
    author_company: authorCompany.trim(),
    linkedin_url: window.location.href
  };
}
