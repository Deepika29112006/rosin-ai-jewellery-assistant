/* ==========================================================================
   RoSin Bangles & Jewellery - Wishlist Controller
   Dynamic Grid Rendering, Item Actions & Real-time State Synchronization
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  renderWishlistPage();

  // Listen for real-time wishlist changes (e.g. removals or additions)
  window.addEventListener('rosin:wishlist-updated', () => {
    renderWishlistPage();
  });
});

function renderWishlistPage() {
  const emptyView = document.getElementById('wishlist-empty-view');
  const filledView = document.getElementById('wishlist-filled-view');
  const gridContainer = document.getElementById('wishlist-grid-container');
  const countDisplay = document.getElementById('wishlist-header-count');

  if (!emptyView || !filledView || !gridContainer) return;

  const wishlist = getWishlist();
  const count = wishlist.length;

  if (countDisplay) {
    countDisplay.textContent = `${count} ${count === 1 ? 'item' : 'items'}`;
  }

  if (count === 0) {
    emptyView.style.display = 'block';
    filledView.style.display = 'none';
    gridContainer.innerHTML = '';
    return;
  }

  emptyView.style.display = 'none';
  filledView.style.display = 'block';
  gridContainer.innerHTML = '';

  wishlist.forEach(p => {
    const card = document.createElement('div');
    card.className = 'wishlist-card';
    card.setAttribute('data-id', p.id);

    const priceFormatted = Number(p.price).toLocaleString('en-IN');
    const availabilityText = p.availability || 'In Stock (Handcrafted)';

    card.innerHTML = `
      <div class="wishlist-card-img-wrapper">
        <button class="wishlist-btn-remove" title="Remove from Wishlist" aria-label="Remove ${p.title} from Wishlist">
          &times;
        </button>
        <img src="${p.image_url}" alt="${p.title}" class="wishlist-card-img" onerror="this.src='https://via.placeholder.com/300x300?text=RoSin+Jewellery'">
      </div>
      <div class="wishlist-card-body">
        <h3 class="wishlist-card-title">${p.title}</h3>
        <div class="wishlist-card-price">₹${priceFormatted}</div>
        <div class="wishlist-card-stock">
          <span>✓</span> ${availabilityText}
        </div>
        <div class="wishlist-card-actions">
          <a href="/product/${p.handle}" class="btn-wishlist-view">View Details</a>
          <button class="btn-wishlist-cart" aria-label="Add ${p.title} to Cart">Add to Cart</button>
        </div>
      </div>
    `;

    // Remove from wishlist button handler
    const removeBtn = card.querySelector('.wishlist-btn-remove');
    removeBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      removeFromWishlist(p.id);
      renderWishlistPage();
    });

    // Add to cart button handler
    const addCartBtn = card.querySelector('.btn-wishlist-cart');
    addCartBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const defaultSize = (p.sizes && p.sizes.length > 0) ? p.sizes[0] : null;
      addToCart(p, defaultSize, null, 1);
    });

    gridContainer.appendChild(card);
  });
}
