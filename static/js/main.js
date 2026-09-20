/* ==========================================================================
   RoSin Bangles & Jewellery - Main Client Script
   Cart State Management & Global Utilities
   ========================================================================== */

const CART_STORAGE_KEY = 'rosin_cart_items_v1';
const WISHLIST_STORAGE_KEY = 'rosin_wishlist_items_v1';

// Cart Helper Functions
function getCart() {
  try {
    const raw = localStorage.getItem(CART_STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    console.error('Failed to read cart from localStorage', e);
    return [];
  }
}

function saveCart(cart) {
  try {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart));
    updateCartCountBadge();
  } catch (e) {
    console.error('Failed to save cart to localStorage', e);
  }
}

function addToCart(product, size = null, color = null, quantity = 1) {
  const cart = getCart();
  const variantKey = `${product.id}_${size || 'default'}_${color || 'default'}`;
  
  const existingIndex = cart.findIndex(item => item.variantKey === variantKey);
  if (existingIndex > -1) {
    cart[existingIndex].quantity += quantity;
  } else {
    cart.push({
      variantKey: variantKey,
      id: product.id,
      title: product.title,
      handle: product.handle,
      price: product.price,
      size: size,
      color: color,
      image_url: product.image_url,
      quantity: quantity
    });
  }

  saveCart(cart);
  showToastNotification(`Added "${product.title}" to cart!`);
}

function removeFromCart(variantKey) {
  let cart = getCart();
  cart = cart.filter(item => item.variantKey !== variantKey);
  saveCart(cart);
}

function updateCartQuantity(variantKey, delta) {
  const cart = getCart();
  const item = cart.find(i => i.variantKey === variantKey);
  if (item) {
    item.quantity += delta;
    if (item.quantity <= 0) {
      removeFromCart(variantKey);
      return;
    }
  }
  saveCart(cart);
}

function updateCartCountBadge() {
  const cart = getCart();
  const totalQty = cart.reduce((sum, item) => sum + item.quantity, 0);
  const badges = document.querySelectorAll('.cart-badge');
  badges.forEach(b => {
    b.textContent = totalQty;
  });
}

// ==========================================================================
// Wishlist Helper Functions
// ==========================================================================
function getWishlist() {
  try {
    const raw = localStorage.getItem(WISHLIST_STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    console.error('Failed to read wishlist from localStorage', e);
    return [];
  }
}

function saveWishlist(wishlist) {
  try {
    localStorage.setItem(WISHLIST_STORAGE_KEY, JSON.stringify(wishlist));
    updateWishlistUI();
    window.dispatchEvent(new CustomEvent('rosin:wishlist-updated', { detail: wishlist }));
  } catch (e) {
    console.error('Failed to save wishlist to localStorage', e);
  }
}

function isInWishlist(productId) {
  if (!productId) return false;
  const list = getWishlist();
  return list.some(item => String(item.id) === String(productId));
}

function toggleWishlist(product) {
  if (!product || !product.id) return false;
  let list = getWishlist();
  const pid = String(product.id);
  const existingIndex = list.findIndex(item => String(item.id) === pid);

  let added = false;
  if (existingIndex > -1) {
    list.splice(existingIndex, 1);
    saveWishlist(list);
    showToastNotification(`Removed "${product.title || 'Product'}" from wishlist`);
    added = false;
  } else {
    list.push({
      id: product.id,
      title: product.title,
      handle: product.handle,
      price: product.price,
      image_url: product.image_url || (product.images && product.images.length > 0 ? product.images[0] : ''),
      category: product.category,
      subcategory: product.subcategory,
      sizes: product.sizes || [],
      availability: product.availability || 'In Stock'
    });
    saveWishlist(list);
    showToastNotification(`Added "${product.title || 'Product'}" to wishlist!`);
    added = true;
  }
  return added;
}

function removeFromWishlist(productId) {
  if (!productId) return;
  let list = getWishlist();
  const item = list.find(i => String(i.id) === String(productId));
  list = list.filter(i => String(i.id) !== String(productId));
  saveWishlist(list);
  if (item) {
    showToastNotification(`Removed "${item.title}" from wishlist`);
  }
}

function updateWishlistUI() {
  const list = getWishlist();
  const count = list.length;

  // 1. Update header badges and icons
  document.querySelectorAll('.wishlist-badge').forEach(el => {
    el.textContent = count;
  });
  document.querySelectorAll('.wishlist-heart-icon').forEach(el => {
    el.textContent = count > 0 ? '♥' : '♡';
    if (count > 0) {
      el.classList.add('active');
    } else {
      el.classList.remove('active');
    }
  });

  // 2. Update all card heart buttons on page
  document.querySelectorAll('.btn-wishlist-heart').forEach(btn => {
    const pid = btn.getAttribute('data-id');
    if (pid) {
      const active = isInWishlist(pid);
      btn.innerHTML = active ? '♥' : '♡';
      btn.setAttribute('title', active ? 'Remove from Wishlist' : 'Add to Wishlist');
      if (active) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    }
  });

  // 3. Update detail page wishlist button if present
  const detailBtn = document.getElementById('btn-detail-wishlist');
  if (detailBtn) {
    const pid = detailBtn.getAttribute('data-id');
    if (pid) {
      const active = isInWishlist(pid);
      const icon = detailBtn.querySelector('.detail-heart-icon');
      if (icon) icon.textContent = active ? '♥' : '♡';
      detailBtn.setAttribute('title', active ? 'Remove from Wishlist' : 'Add to Wishlist');
      if (active) {
        detailBtn.classList.add('active');
      } else {
        detailBtn.classList.remove('active');
      }
    }
  }
}

// Toast Notification
function showToastNotification(message) {
  let toast = document.getElementById('global-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'global-toast';
    toast.style.cssText = `
      position: fixed;
      bottom: 24px;
      left: 50%;
      transform: translateX(-50%);
      background: #111111;
      color: #ffffff;
      padding: 10px 20px;
      border-radius: 30px;
      font-size: 13px;
      font-weight: 600;
      z-index: 2000;
      box-shadow: 0 4px 14px rgba(0,0,0,0.3);
      display: none;
      transition: opacity 0.3s ease;
      border: 1px solid #c59b27;
    `;
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.style.display = 'block';
  toast.style.opacity = '1';
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => { toast.style.display = 'none'; }, 300);
  }, 2400);
}

document.addEventListener('DOMContentLoaded', () => {
  updateCartCountBadge();
  updateWishlistUI();
});
