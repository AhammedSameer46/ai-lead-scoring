// popup.js - Handles button clicks and UI in the extension popup

const RENDER_URL = 'https://linkedin-lead-finder.onrender.com';

document.getElementById('captureBtn').addEventListener('click', async () => {
  const button = document.getElementById('captureBtn');
  const statusDiv = document.getElementById('status');
  
  // Disable button and show loading
  button.disabled = true;
  button.textContent = 'Capturing...';
  statusDiv.className = 'status loading';
  statusDiv.textContent = '🔄 Analyzing post...';
  
  try {
    // Get the active tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    // Check if we're on LinkedIn
    if (!tab.url.includes('linkedin.com')) {
      throw new Error('Please open a LinkedIn post first!');
    }
    
    // Inject script to extract post data from the page
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: extractLinkedInPost
    });
    
    const postData = results[0].result;
    
    if (!postData || !postData.post_content) {
      throw new Error('Could not find post content. Make sure you\'re on a LinkedIn post.');
    }
    
    // Send to your API
    const response = await fetch(`${RENDER_URL}/api/capture-post`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(postData)
    });
    
    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }
    
    const data = await response.json();
    
    // Show success with score
    statusDiv.className = 'status success';
    statusDiv.innerHTML = `
      <div class="score-display">
        <span class="score">${data.score}/100</span>
        <span class="tier ${data.tier}">${data.tier.toUpperCase()}</span>
      </div>
      <div style="margin-top: 8px;">
        ✅ Lead captured! Check Telegram for details.
      </div>
    `;
    
    button.textContent = '✓ Captured!';
    
    // Reset button after 3 seconds
    setTimeout(() => {
      button.disabled = false;
      button.textContent = 'Capture This Post';
    }, 3000);
    
  } catch (error) {
    console.error('Capture error:', error);
    statusDiv.className = 'status error';
    statusDiv.textContent = `❌ Error: ${error.message}`;
    
    button.disabled = false;
    button.textContent = 'Capture This Post';
  }
});

// This function runs inside the LinkedIn page to extract post data
function extractLinkedInPost() {
  // Try different selectors for post content
  const postContent = 
    document.querySelector('[data-test-id="main-feed-activity-card__commentary"]')?.innerText ||
    document.querySelector('.feed-shared-update-v2__description')?.innerText ||
    document.querySelector('.feed-shared-inline-show-more-text')?.innerText ||
    document.querySelector('[data-test-id="feed-shared-update-v2__description"]')?.innerText ||
    document.querySelector('.break-words')?.innerText ||
    '';
  
  // Try to get author name
  const authorName = 
    document.querySelector('.update-components-actor__name')?.innerText ||
    document.querySelector('[data-test-id="main-feed-activity-card__actor-name"]')?.innerText ||
    document.querySelector('.feed-shared-actor__name')?.innerText ||
    '';
  
  // Try to get author title
  const authorTitle = 
    document.querySelector('.update-components-actor__description')?.innerText ||
    document.querySelector('[data-test-id="main-feed-activity-card__actor-description"]')?.innerText ||
    document.querySelector('.feed-shared-actor__description')?.innerText ||
    '';
  
  // Try to get company name
  const authorCompany = 
    document.querySelector('.feed-shared-actor__sub-description')?.innerText ||
    '';
  
  return {
    post_content: postContent.trim(),
    author_name: authorName.trim(),
    author_title: authorTitle.trim(),
    author_company: authorCompany.trim(),
    linkedin_url: window.location.href
  };
}
