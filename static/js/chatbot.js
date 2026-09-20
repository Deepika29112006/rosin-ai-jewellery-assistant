/* ==========================================================================
   RoSin AI Shopping Assistant - Client Controller
   Interactive RAG Chatbot with Embedded Product Recommendations
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  const widget = document.createElement('div');
  widget.className = 'ai-chatbot-widget';
  widget.innerHTML = `
    <!-- TRIGGER BUTTON -->
    <button class="chatbot-toggle-btn" id="chatbot-toggle-btn" title="Ask AI Shopping Assistant">
      <span class="sparkle-icon">✨</span>
      <span>RoSin AI Assistant</span>
    </button>

    <!-- CHAT WINDOW -->
    <div class="chatbot-window" id="chatbot-window">
      <!-- HEADER -->
      <div class="chatbot-header">
        <div class="chatbot-header-info">
          <div class="chatbot-header-title">
            <span>RoSin Assistant</span>
            <span class="chatbot-header-badge">Verified AI</span>
          </div>
          <div class="chatbot-header-sub">Grounded in verified RoSin business data</div>
        </div>
        <button class="chatbot-close-btn" id="chatbot-close-btn">&times;</button>
      </div>

      <!-- SUGGESTION CHIPS -->
      <div class="chatbot-suggestions">
        <button class="chip-btn" data-query="Show bridal bangles">Show bridal bangles</button>
        <button class="chip-btn" data-query="Show bridal jewellery">Show bridal jewellery</button>
        <button class="chip-btn" data-query="Show jhumkas">Show jhumkas</button>
        <button class="chip-btn" data-query="Do you have size 2.6?">Do you have size 2.6?</button>
        <button class="chip-btn" data-query="What is the return policy?">Return policy</button>
        <button class="chip-btn" data-query="What is your shipping policy?">Shipping policy</button>
      </div>

      <!-- MESSAGES LIST -->
      <div class="chatbot-messages" id="chatbot-messages">
        <div class="chat-bubble assistant">
          Hello! 👋 Welcome to <strong>RoSin Bangles & Jewellery</strong>. I am your verified shopping assistant.
          <br><br>
          You can ask me about our handcrafted bangles, prices, available sizes (2.4, 2.6, 2.8), custom outfit-matching, or store policies!
        </div>
      </div>

      <!-- INPUT BAR -->
      <form class="chatbot-input-bar" id="chatbot-form">
        <input type="text" class="chatbot-input" id="chatbot-input" placeholder="Ask about bangles, sizes, shipping..." autocomplete="off" required>
        <button type="submit" class="chatbot-send-btn" id="chatbot-send-btn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </button>
      </form>
    </div>
  `;
  document.body.appendChild(widget);

  const toggleBtn = document.getElementById('chatbot-toggle-btn');
  const chatWindow = document.getElementById('chatbot-window');
  const closeBtn = document.getElementById('chatbot-close-btn');
  const chatForm = document.getElementById('chatbot-form');
  const chatInput = document.getElementById('chatbot-input');
  const messagesList = document.getElementById('chatbot-messages');
  const chipButtons = document.querySelectorAll('.chip-btn');

  // Also bind to any nav buttons with class .btn-ai-nav
  document.querySelectorAll('.btn-ai-nav').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      openChat();
    });
  });

  function openChat() {
    chatWindow.style.display = 'flex';
    chatInput.focus();
  }

  function closeChat() {
    chatWindow.style.display = 'none';
  }

  toggleBtn.addEventListener('click', () => {
    if (chatWindow.style.display === 'flex') {
      closeChat();
    } else {
      openChat();
    }
  });

  closeBtn.addEventListener('click', closeChat);

  chipButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const q = btn.getAttribute('data-query');
      if (q) {
        sendMessage(q);
      }
    });
  });

  chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const query = chatInput.value.trim();
    if (query) {
      sendMessage(query);
      chatInput.value = '';
    }
  });

  async function sendMessage(text) {
    // 1. Append User Bubble
    appendMessage(text, 'user');

    // 2. Append Typing Indicator
    const typingElem = document.createElement('div');
    typingElem.className = 'chat-typing';
    typingElem.innerHTML = '<div class="chat-dot"></div><div class="chat-dot"></div><div class="chat-dot"></div>';
    messagesList.appendChild(typingElem);
    messagesList.scrollTop = messagesList.scrollHeight;

    // Detect product context if on product page
    const metaTag = document.getElementById('product-handle-meta');
    let currentHandle = null;
    if (metaTag) {
      currentHandle = metaTag.getAttribute('data-handle') || metaTag.value || null;
    }
    if (!currentHandle) {
      const urlMatch = window.location.pathname.match(/\/product\/([^\/]+)/);
      if (urlMatch && urlMatch[1]) {
        currentHandle = urlMatch[1];
      }
    }

    const payload = { message: text };
    if (currentHandle) {
      payload.handle = currentHandle;
      payload.product_handle = currentHandle;
    }

    let data;
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`Server HTTP error: ${response.status}`);
      }

      data = await response.json();
    } catch (err) {
      console.error('Chat network error:', err);
      typingElem.remove();
      appendMessage("Network error. Please make sure the RoSin server is running.", 'assistant');
      return;
    }

    typingElem.remove();

    if (data && data.success) {
      try {
        appendAssistantResponse(data);
      } catch (renderErr) {
        console.error('Chat render error:', renderErr);
        appendMessage(data.reply || "Sorry, I encountered an issue displaying the response.", 'assistant');
      }
    } else {
      const errMsg = (data && data.error) ? data.error : "Sorry, I encountered a temporary issue. Please ask again or contact WhatsApp (+91 8438990370).";
      appendMessage(errMsg, 'assistant');
    }
  }

  function appendMessage(text, sender) {
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${sender}`;
    bubble.textContent = text;
    messagesList.appendChild(bubble);
    messagesList.scrollTop = messagesList.scrollHeight;
  }

  function appendAssistantResponse(data) {
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble assistant';

    // Main text
    const textNode = document.createElement('div');
    textNode.textContent = data.reply;
    bubble.appendChild(textNode);

    // Product cards if recommended
    if (data.recommended_products && data.recommended_products.length > 0) {
      const carousel = document.createElement('div');
      carousel.className = 'chat-products-carousel';

      data.recommended_products.forEach(p => {
        const item = document.createElement('div');
        item.className = 'chat-product-item';
        const imgUrl = p.image_url || 'https://via.placeholder.com/60?text=RoSin';
        const sizesStr = p.sizes && p.sizes.length > 0 ? `Sizes: ${p.sizes.slice(0, 3).join(', ')}` : '';
        const inWish = typeof isInWishlist === 'function' ? isInWishlist(p.id) : false;
        const availText = (p.availability && p.availability.toLowerCase().includes('out')) ? 'Out of Stock' : 'In Stock';
        const catSubcatText = p.subcategory ? (p.category ? `${p.category} → ${p.subcategory}` : p.subcategory) : (p.category || '');

        item.innerHTML = `
          <img src="${imgUrl}" alt="${p.title}" class="chat-product-img" onerror="this.src='https://via.placeholder.com/60?text=RoSin'">
          <div class="chat-product-details">
            <div class="chat-product-title" title="${p.title}">${p.title}</div>
            ${catSubcatText ? `<div class="chat-product-cat" style="font-size:10px; color:#777; margin:1px 0;">${catSubcatText}</div>` : ''}
            <div class="chat-product-meta">
              <span class="chat-product-price">₹${Number(p.price).toLocaleString('en-IN')}</span>
              <span class="chat-product-avail">${availText}</span>
            </div>
            ${sizesStr ? `<div class="chat-product-sizes">${sizesStr}</div>` : ''}
          </div>
          <div class="chat-product-actions">
            <div style="display:flex; gap:4px; align-items:center;">
              <a href="/product/${p.handle}" class="btn-chat-view" title="View Product Details">View Product</a>
              <button class="btn-chat-wishlist" title="${inWish ? 'Remove from Wishlist' : 'Add to Wishlist'}" style="background:none; border:1px solid var(--border-color); border-radius:4px; cursor:pointer; font-size:14px; padding:3px 6px; color:${inWish ? '#e53935' : '#888'};">
                ${inWish ? '♥' : '♡'}
              </button>
            </div>
            <button class="btn-chat-add" title="Add to Cart">Add to Cart</button>
          </div>
        `;

        const wishBtn = item.querySelector('.btn-chat-wishlist');
        if (wishBtn) {
          wishBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (typeof toggleWishlist === 'function') {
              toggleWishlist(p);
              const nowInWish = isInWishlist(p.id);
              wishBtn.textContent = nowInWish ? '♥' : '♡';
              wishBtn.style.color = nowInWish ? '#e53935' : '#888';
              wishBtn.setAttribute('title', nowInWish ? 'Remove from Wishlist' : 'Add to Wishlist');
            }
          });
        }

        const addBtn = item.querySelector('.btn-chat-add');
        if (addBtn) {
          addBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (typeof addToCart === 'function') {
              const defaultSize = (p.sizes && p.sizes.length > 0) ? p.sizes[0] : null;
              addToCart({
                id: p.id,
                title: p.title,
                handle: p.handle,
                price: p.price,
                image_url: imgUrl
              }, defaultSize);
              addBtn.textContent = '✓ Added';
              addBtn.style.background = '#25d366';
              addBtn.style.color = '#ffffff';
              setTimeout(() => {
                addBtn.textContent = 'Add to Cart';
                addBtn.style.background = '';
                addBtn.style.color = '';
              }, 2000);
            }
          });
        }

        carousel.appendChild(item);
      });
      bubble.appendChild(carousel);
    }

    // Citation footer
    if (data.citations && data.citations.length > 0) {
      const cit = document.createElement('div');
      cit.className = 'chat-bubble-citation';
      const source = data.citations[0];
      if (source.startsWith('http')) {
        cit.innerHTML = `<span>Source:</span> <a href="${source}" target="_blank" rel="noopener">Official RoSin Policy</a>`;
      } else {
        cit.innerHTML = `<span>Source:</span> <strong>${source}</strong>`;
      }
      bubble.appendChild(cit);
    }

    messagesList.appendChild(bubble);
    messagesList.scrollTop = messagesList.scrollHeight;
  }
});
