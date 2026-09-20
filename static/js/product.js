/* ==========================================================================
   RoSin Product Detail Controller
   Dynamic Image Gallery, Variant Selectors & Direct WhatsApp Inquiry
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  const handleElem = document.getElementById('product-handle-meta');
  if (!handleElem) return;

  const handle = handleElem.getAttribute('data-handle');
  if (!handle) return;

  loadProductDetails(handle);

  async function loadProductDetails(handle) {
    try {
      const resp = await fetch(`/api/product/${handle}`);
      const data = await resp.json();

      if (!data.success || !data.product) {
        document.getElementById('product-detail-container').innerHTML = `
          <div style="text-align: center; padding: 80px 20px;">
            <h2>Product Not Found</h2>
            <p>The requested item could not be found in RoSin's catalog.</p>
            <br>
            <a href="/shop" class="btn-primary">Return to Shop</a>
          </div>
        `;
        return;
      }

      const p = data.product;
      renderProductPage(p);
    } catch (e) {
      console.error('Error fetching product', e);
    }
  }

  function renderProductPage(p) {
    let selectedSize = p.sizes && p.sizes.length > 0 ? p.sizes[0] : null;
    let selectedColor = p.colors && p.colors.length > 0 ? p.colors[0] : null;
    let currentQuantity = 1;
    let currentPrice = p.price;

    // Document title
    document.title = `${p.title} — RoSin Bangles & Jewellery`;

    // 1. Gallery Setup
    const mainImg = document.getElementById('main-product-img');
    const thumbnailsContainer = document.getElementById('thumbnails-container');

    if (p.images && p.images.length > 0) {
      mainImg.src = p.images[0];
      thumbnailsContainer.innerHTML = '';
      p.images.forEach((imgSrc, idx) => {
        const thumb = document.createElement('img');
        thumb.src = imgSrc;
        thumb.className = `thumbnail-item ${idx === 0 ? 'active' : ''}`;
        thumb.addEventListener('click', () => {
          document.querySelectorAll('.thumbnail-item').forEach(t => t.classList.remove('active'));
          thumb.classList.add('active');
          mainImg.src = imgSrc;
        });
        thumbnailsContainer.appendChild(thumb);
      });
    }

    // 2. Info Fields
    document.getElementById('product-title').textContent = p.title;
    document.getElementById('product-category-breadcrumb').textContent = `${p.category} › ${p.subcategory}`;
    document.getElementById('product-subcategory-badge').textContent = p.subcategory;
    document.getElementById('product-price-display').textContent = `₹${Number(p.price).toLocaleString('en-IN')}`;

    // Description
    const descElem = document.getElementById('product-description-text');
    if (p.description) {
      descElem.textContent = p.description;
    } else {
      descElem.innerHTML = `<em>Handcrafted piece from RoSin's verified ${p.subcategory} collection. Crafted with attention to detail by skilled women artisans.</em>`;
    }

    // Wishlist Button Setup
    const detailWishlistBtn = document.getElementById('btn-detail-wishlist');
    if (detailWishlistBtn) {
      detailWishlistBtn.setAttribute('data-id', p.id);
      const inWish = isInWishlist(p.id);
      const icon = detailWishlistBtn.querySelector('.detail-heart-icon');
      if (icon) icon.textContent = inWish ? '♥' : '♡';
      detailWishlistBtn.setAttribute('title', inWish ? 'Remove from Wishlist' : 'Add to Wishlist');
      if (inWish) {
        detailWishlistBtn.classList.add('active');
      } else {
        detailWishlistBtn.classList.remove('active');
      }

      detailWishlistBtn.onclick = (e) => {
        e.preventDefault();
        toggleWishlist(p);
      };
    }

    // Source link
    const sourceLink = document.getElementById('product-official-source');
    if (sourceLink) {
      sourceLink.href = p.source_url;
    }

    // 3. Size Selector Setup
    const sizeContainer = document.getElementById('size-options-container');
    if (sizeContainer) {
      sizeContainer.innerHTML = '';
      if (p.sizes && p.sizes.length > 0) {
        document.getElementById('size-group-wrapper').style.display = 'block';
        p.sizes.forEach((s, idx) => {
          const btn = document.createElement('button');
          btn.className = `variant-pill ${idx === 0 ? 'active' : ''}`;
          btn.textContent = s;
          btn.addEventListener('click', () => {
            document.querySelectorAll('.variant-pill').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedSize = s;
            updateVariantPrice();
          });
          sizeContainer.appendChild(btn);
        });
      } else {
        document.getElementById('size-group-wrapper').style.display = 'none';
      }
    }

    function updateVariantPrice() {
      // Find variant with matching size
      const variant = p.variants.find(v => v.size === selectedSize);
      if (variant && variant.price) {
        currentPrice = variant.price;
        document.getElementById('product-price-display').textContent = `₹${Number(currentPrice).toLocaleString('en-IN')}`;
      }
    }

    // 4. Quantity Stepper
    const qtyInput = document.getElementById('qty-input');
    document.getElementById('qty-minus').addEventListener('click', () => {
      if (currentQuantity > 1) {
        currentQuantity--;
        qtyInput.value = currentQuantity;
      }
    });
    document.getElementById('qty-plus').addEventListener('click', () => {
      currentQuantity++;
      qtyInput.value = currentQuantity;
    });

    // 5. Add To Cart Button
    const addCartBtn = document.getElementById('btn-add-cart');
    addCartBtn.addEventListener('click', () => {
      const productToAdd = {
        ...p,
        price: currentPrice
      };
      addToCart(productToAdd, selectedSize, selectedColor, currentQuantity);
    });

    // 6. WhatsApp Inquiry Button
    const waBtn = document.getElementById('btn-order-whatsapp');
    waBtn.addEventListener('click', () => {
      let msg = `Hello RoSin Bangles, I am interested in ordering this product:\n`;
      msg += `*${p.title}*\n`;
      msg += `Price: ₹${Number(currentPrice).toLocaleString('en-IN')}\n`;
      if (selectedSize) msg += `Selected Size: ${selectedSize}\n`;
      msg += `Quantity: ${currentQuantity}\n`;
      msg += `Link: ${p.source_url}\n\n`;
      msg += `Please confirm availability and shipping time. Thank you!`;

      const encoded = encodeURIComponent(msg);
      window.open(`https://wa.me/918438990370?text=${encoded}`, '_blank');
    });

    // 7. Load Similar Products ("You May Also Like")
    loadSimilarProducts(p.handle);

    async function loadSimilarProducts(handle) {
      const section = document.getElementById('similar-products-section');
      const grid = document.getElementById('similar-products-grid');
      if (!section || !grid) return;

      try {
        const resp = await fetch(`/api/product/${handle}/similar?limit=6`);
        const data = await resp.json();

        if (!data.success || !data.products || data.products.length === 0) {
          section.style.display = 'none';
          return;
        }

        grid.innerHTML = '';
        data.products.forEach(item => {
          const card = document.createElement('div');
          card.className = 'product-card';

          const inWish = typeof isInWishlist === 'function' ? isInWishlist(item.id) : false;
          const heartChar = inWish ? '♥' : '♡';
          const heartClass = inWish ? 'wishlist-btn active' : 'wishlist-btn';
          const imgUrl = item.image_url || 'https://via.placeholder.com/300?text=RoSin';

          card.innerHTML = `
            <div class="product-img-wrapper" style="position:relative;">
              <img src="${imgUrl}" alt="${item.title}" class="product-img" loading="lazy" onerror="this.src='https://via.placeholder.com/300?text=RoSin'">
              <span class="badge-subcat" style="position:absolute; top:8px; left:8px;">${item.subcategory}</span>
              <button class="${heartClass}" data-id="${item.id}" title="${inWish ? 'Remove from Wishlist' : 'Add to Wishlist'}" aria-label="Toggle Wishlist" style="position:absolute; top:8px; right:8px; width:34px; height:34px; border-radius:50%; border:1px solid rgba(0,0,0,0.1); background:#ffffff; display:flex; align-items:center; justify-content:center; cursor:pointer; font-size:18px; color:${inWish ? '#e53935' : '#888'}; transition:all 0.2s;">
                <span class="heart-icon">${heartChar}</span>
              </button>
            </div>
            <div class="product-info" style="padding:14px;">
              <h3 class="product-title" title="${item.title}" style="font-size:15px; font-weight:600; margin-bottom:6px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                <a href="/product/${item.handle}" style="color:var(--text-main); text-decoration:none;">${item.title}</a>
              </h3>
              <div class="product-price-row" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <span class="product-price" style="font-size:16px; font-weight:700; color:var(--primary-color);">₹${Number(item.price).toLocaleString('en-IN')}</span>
                <span style="font-size:12px; color:#2e7d32; font-weight:500;">${item.availability || 'In Stock'}</span>
              </div>
              <div style="display:flex; gap:8px;">
                <a href="/product/${item.handle}" class="btn-outline" style="flex:1; text-align:center; padding:7px 10px; font-size:12px; border:1px solid var(--primary-color); color:var(--primary-color); border-radius:var(--radius-sm); text-decoration:none; font-weight:600;">View</a>
                <button class="btn-similar-add" style="flex:1; padding:7px 10px; font-size:12px; background:var(--primary-color); color:#fff; border:none; border-radius:var(--radius-sm); font-weight:600; cursor:pointer;">Add to Cart</button>
              </div>
            </div>
          `;

          // Wishlist click handler
          const wishBtn = card.querySelector('.wishlist-btn');
          if (wishBtn) {
            wishBtn.addEventListener('click', (e) => {
              e.preventDefault();
              e.stopPropagation();
              if (typeof toggleWishlist === 'function') {
                toggleWishlist(item);
                const nowInWish = isInWishlist(item.id);
                wishBtn.querySelector('.heart-icon').textContent = nowInWish ? '♥' : '♡';
                wishBtn.style.color = nowInWish ? '#e53935' : '#888';
                wishBtn.setAttribute('title', nowInWish ? 'Remove from Wishlist' : 'Add to Wishlist');
              }
            });
          }

          // Add to cart click handler
          const addBtn = card.querySelector('.btn-similar-add');
          if (addBtn) {
            addBtn.addEventListener('click', (e) => {
              e.preventDefault();
              if (typeof addToCart === 'function') {
                const defaultSize = (item.sizes && item.sizes.length > 0) ? item.sizes[0] : null;
                addToCart({
                  id: item.id,
                  title: item.title,
                  handle: item.handle,
                  price: item.price,
                  image_url: imgUrl
                }, defaultSize);
                addBtn.textContent = '✓ Added';
                addBtn.style.background = '#25d366';
                setTimeout(() => {
                  addBtn.textContent = 'Add to Cart';
                  addBtn.style.background = '';
                }, 1500);
              }
            });
          }

          grid.appendChild(card);
        });

        section.style.display = 'block';
      } catch (err) {
        console.error('Error fetching similar products:', err);
        section.style.display = 'none';
      }
    }
  }
});
