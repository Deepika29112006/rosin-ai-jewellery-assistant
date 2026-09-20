/* ==========================================================================
   RoSin Catalogue Controller
   Interactive Multi-Facet Filtering, Dynamic Category Headers & Normal Vertical Grid
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  const productsContainer = document.getElementById('products-grid');
  const countBadge = document.getElementById('products-count-badge');
  const searchInput = document.getElementById('search-input');
  const sortSelect = document.getElementById('sort-select');
  const maxPriceSlider = document.getElementById('price-range-slider');
  const priceDisplay = document.getElementById('price-display');
  const clearFiltersBtn = document.getElementById('clear-filters-btn');
  const breadcrumbRoot = document.getElementById('breadcrumb-root');

  // State
  let currentCategory = null;
  let currentSubcategory = null;
  let currentSize = null;
  let currentAvailability = null;
  let currentColor = null;
  let currentMaxPrice = null;
  let currentQuery = '';
  let currentSort = 'featured';

  // Read URL query parameters on initial load
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.has('category')) currentCategory = urlParams.get('category');
  if (urlParams.has('subcategory')) currentSubcategory = urlParams.get('subcategory');
  if (urlParams.has('size')) currentSize = urlParams.get('size');
  if (urlParams.has('availability')) currentAvailability = urlParams.get('availability');
  if (urlParams.has('color')) currentColor = urlParams.get('color');
  if (urlParams.has('sort')) currentSort = urlParams.get('sort');
  if (urlParams.has('max_price')) {
    currentMaxPrice = urlParams.get('max_price');
    if (maxPriceSlider) maxPriceSlider.value = currentMaxPrice;
    if (priceDisplay) priceDisplay.textContent = `Up to ₹${Number(currentMaxPrice).toLocaleString('en-IN')}`;
  }
  if (urlParams.has('query')) {
    currentQuery = urlParams.get('query');
    if (searchInput) searchInput.value = currentQuery;
  }
  if (sortSelect && currentSort) {
    sortSelect.value = currentSort;
  }

  // Pre-activate size filter button if from URL
  if (currentSize) {
    document.querySelectorAll('.filter-size-btn').forEach(b => {
      if (b.getAttribute('data-size') === currentSize) b.classList.add('active');
    });
  }

  // Pre-activate availability button if from URL
  if (currentAvailability) {
    document.querySelectorAll('.filter-avail-btn').forEach(b => {
      if (b.getAttribute('data-avail') === currentAvailability) {
        b.classList.add('active');
      } else {
        b.classList.remove('active');
      }
    });
  }

  // Load Categories into Sidebar Nav
  loadCategoryNav();

  // Load Initial Products
  fetchAndRenderProducts();

  // --- Event Listeners ---

  // Search input with debounce
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener('input', (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        currentQuery = e.target.value.trim();
        syncURLState();
        fetchAndRenderProducts();
      }, 300);
    });
  }

  // Sort dropdown
  if (sortSelect) {
    sortSelect.addEventListener('change', (e) => {
      currentSort = e.target.value;
      syncURLState();
      fetchAndRenderProducts();
    });
  }

  // Price slider
  if (maxPriceSlider && priceDisplay) {
    maxPriceSlider.addEventListener('input', (e) => {
      currentMaxPrice = e.target.value;
      priceDisplay.textContent = `Up to ₹${Number(currentMaxPrice).toLocaleString('en-IN')}`;
    });
    maxPriceSlider.addEventListener('change', () => {
      syncURLState();
      fetchAndRenderProducts();
    });
  }

  // Size Filter Pills
  document.querySelectorAll('.filter-size-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const val = btn.getAttribute('data-size');
      if (currentSize === val) {
        currentSize = null;
        btn.classList.remove('active');
      } else {
        document.querySelectorAll('.filter-size-btn').forEach(b => b.classList.remove('active'));
        currentSize = val;
        btn.classList.add('active');
      }
      syncURLState();
      fetchAndRenderProducts();
    });
  });

  // Availability Filter Buttons
  document.querySelectorAll('.filter-avail-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-avail-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentAvailability = btn.getAttribute('data-avail') || null;
      syncURLState();
      fetchAndRenderProducts();
    });
  });

  // Breadcrumb Root Link ("All Collections")
  if (breadcrumbRoot) {
    breadcrumbRoot.addEventListener('click', (e) => {
      e.preventDefault();
      clearAllFilters();
    });
  }

  // Clear All Filters
  if (clearFiltersBtn) {
    clearFiltersBtn.addEventListener('click', () => {
      clearAllFilters();
    });
  }

  function clearAllFilters() {
    currentCategory = null;
    currentSubcategory = null;
    currentSize = null;
    currentAvailability = null;
    currentColor = null;
    currentMaxPrice = null;
    currentQuery = '';
    currentSort = 'featured';

    if (searchInput) searchInput.value = '';
    if (sortSelect) sortSelect.value = 'featured';
    if (maxPriceSlider) {
      maxPriceSlider.value = 3500;
      priceDisplay.textContent = 'Up to ₹3,500';
    }
    document.querySelectorAll('.filter-size-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.filter-avail-btn').forEach(b => {
      if (b.getAttribute('data-avail') === '') b.classList.add('active');
      else b.classList.remove('active');
    });
    document.querySelectorAll('.cat-nav-item, .subcat-nav-item').forEach(b => b.classList.remove('active'));
    const allItemLi = document.querySelector('.cat-nav-item[data-type="all"]');
    if (allItemLi) allItemLi.classList.add('active');

    syncURLState();
    fetchAndRenderProducts();
  }

  function syncURLState() {
    const url = new URL(window.location.href);
    if (currentCategory) url.searchParams.set('category', currentCategory);
    else url.searchParams.delete('category');

    if (currentSubcategory) url.searchParams.set('subcategory', currentSubcategory);
    else url.searchParams.delete('subcategory');

    if (currentSize) url.searchParams.set('size', currentSize);
    else url.searchParams.delete('size');

    if (currentAvailability) url.searchParams.set('availability', currentAvailability);
    else url.searchParams.delete('availability');

    if (currentMaxPrice && Number(currentMaxPrice) < 3500) url.searchParams.set('max_price', currentMaxPrice);
    else url.searchParams.delete('max_price');

    if (currentQuery) url.searchParams.set('query', currentQuery);
    else url.searchParams.delete('query');

    if (currentSort && currentSort !== 'featured') url.searchParams.set('sort', currentSort);
    else url.searchParams.delete('sort');

    window.history.replaceState({}, '', url.toString());
  }

  function updateCategoryHeader(matchingCount) {
    const pageTitle = document.getElementById('category-page-title');
    const pageCount = document.getElementById('category-page-count');
    const breadcrumbCat = document.getElementById('breadcrumb-cat');
    const breadcrumbCatSep = document.getElementById('breadcrumb-cat-sep');
    const breadcrumbSubcat = document.getElementById('breadcrumb-subcat');
    const breadcrumbSubcatSep = document.getElementById('breadcrumb-subcat-sep');

    // Determine Title
    let title = 'All Collections';
    if (currentSubcategory) {
      title = currentSubcategory;
    } else if (currentCategory) {
      title = currentCategory;
    } else if (currentQuery) {
      title = `Search: "${currentQuery}"`;
    }

    if (pageTitle) pageTitle.textContent = title;

    // Determine Count
    const countStr = `${matchingCount} ${matchingCount === 1 ? 'product' : 'products'}`;
    if (pageCount) pageCount.textContent = countStr;
    if (countBadge) countBadge.textContent = countStr;

    // Update Breadcrumbs
    if (breadcrumbCat && breadcrumbCatSep) {
      if (currentCategory) {
        breadcrumbCat.textContent = currentCategory;
        breadcrumbCat.style.display = 'inline';
        breadcrumbCatSep.style.display = 'inline';
      } else {
        breadcrumbCat.style.display = 'none';
        breadcrumbCatSep.style.display = 'none';
      }
    }

    if (breadcrumbSubcat && breadcrumbSubcatSep) {
      if (currentSubcategory) {
        breadcrumbSubcat.textContent = currentSubcategory;
        breadcrumbSubcat.style.display = 'inline';
        breadcrumbSubcatSep.style.display = 'inline';
      } else {
        breadcrumbSubcat.style.display = 'none';
        breadcrumbSubcatSep.style.display = 'none';
      }
    }

    // Document Title
    document.title = `${title} (${countStr}) — RoSin Bangles & Jewellery`;
  }

  async function loadCategoryNav() {
    const navContainer = document.getElementById('category-filter-list');
    if (!navContainer) return;

    try {
      const resp = await fetch('/api/categories');
      const data = await resp.json();
      if (!data.success) return;

      // Auto-resolve currentCategory from currentSubcategory if not specified
      if (currentSubcategory && !currentCategory) {
        for (const cat of data.categories) {
          if (cat.subcategories && cat.subcategories.some(s => s.name === currentSubcategory)) {
            currentCategory = cat.name;
            break;
          }
        }
      }

      navContainer.innerHTML = `
        <li class="cat-nav-item ${!currentCategory && !currentSubcategory ? 'active' : ''}" data-type="all">
          <span>All Items</span>
        </li>
      `;

      data.categories.forEach(cat => {
        const isCatActive = currentCategory === cat.name && !currentSubcategory;
        const catLi = document.createElement('li');
        catLi.className = `cat-nav-item ${isCatActive ? 'active' : ''}`;
        catLi.innerHTML = `<strong>${cat.name}</strong>`;
        catLi.addEventListener('click', () => {
          document.querySelectorAll('.cat-nav-item, .subcat-nav-item').forEach(b => b.classList.remove('active'));
          catLi.classList.add('active');
          currentCategory = cat.name;
          currentSubcategory = null;
          syncURLState();
          fetchAndRenderProducts();
        });
        navContainer.appendChild(catLi);

        // Subcategories
        if (cat.subcategories && cat.subcategories.length > 0) {
          const subUl = document.createElement('ul');
          subUl.className = 'subcat-list';
          cat.subcategories.forEach(sub => {
            // Hide empty subcategories with 0 products
            if (sub.count === 0 || sub.name === 'Korean Hair Claws' || sub.name === 'Saree Pins') return;

            const isSubActive = currentSubcategory === sub.name;
            const subLi = document.createElement('li');
            subLi.className = `subcat-nav-item ${isSubActive ? 'active' : ''}`;
            subLi.innerHTML = `${sub.name} <span class="count">(${sub.count})</span>`;
            subLi.addEventListener('click', (e) => {
              e.stopPropagation();
              document.querySelectorAll('.cat-nav-item, .subcat-nav-item').forEach(b => b.classList.remove('active'));
              subLi.classList.add('active');
              currentCategory = cat.name;
              currentSubcategory = sub.name;
              syncURLState();
              fetchAndRenderProducts();
            });
            subUl.appendChild(subLi);
          });
          navContainer.appendChild(subUl);
        }
      });

      // Bind the "All Items" click
      navContainer.querySelector('[data-type="all"]').addEventListener('click', () => {
        clearAllFilters();
      });
    } catch (e) {
      console.error('Failed to load categories', e);
    }
  }

  async function fetchAndRenderProducts() {
    if (!productsContainer) return;

    productsContainer.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 50px 0; color: #888;">
        Loading verified products...
      </div>
    `;

    const params = new URLSearchParams();
    if (currentCategory) params.set('category', currentCategory);
    if (currentSubcategory) params.set('subcategory', currentSubcategory);
    if (currentSize) params.set('size', currentSize);
    if (currentAvailability) params.set('availability', currentAvailability);
    if (currentColor) params.set('color', currentColor);
    if (currentMaxPrice) params.set('max_price', currentMaxPrice);
    if (currentQuery) params.set('query', currentQuery);
    if (currentSort) params.set('sort', currentSort);

    try {
      const resp = await fetch(`/api/products?${params.toString()}`);
      const data = await resp.json();

      if (!data.success || data.products.length === 0) {
        updateCategoryHeader(0);
        productsContainer.innerHTML = `
          <div style="grid-column: 1 / -1; text-align: center; padding: 60px 20px; background: #ffffff; border-radius: 12px; border: 1px dashed var(--border-color);">
            <h3 style="font-size: 20px; margin-bottom: 8px; color: var(--primary-color);">No products found</h3>
            <p style="font-size: 13.5px; color: var(--text-muted); margin-bottom: 20px; max-width: 440px; margin-left: auto; margin-right: auto; line-height: 1.5;">
              No products match the selected criteria in RoSin's verified catalog. Try clearing filters or searching another keyword.
            </p>
            <button class="btn-primary" id="btn-empty-clear">Clear All Filters</button>
          </div>
        `;
        const emptyBtn = document.getElementById('btn-empty-clear');
        if (emptyBtn) {
          emptyBtn.addEventListener('click', () => clearAllFilters());
        }
        return;
      }

      updateCategoryHeader(data.products.length);
      productsContainer.innerHTML = '';

      data.products.forEach(p => {
        const card = document.createElement('div');
        card.className = 'product-card';

        const sizesHtml = p.sizes && p.sizes.length > 0
          ? p.sizes.slice(0, 4).map(s => `<span class="size-pill">${s}</span>`).join('')
          : '<span class="size-pill" style="background:#eee; color:#888; border:none;">Standard</span>';

        const inWish = typeof isInWishlist === 'function' ? isInWishlist(p.id) : false;

        card.innerHTML = `
          <div class="product-card-img-wrapper">
            <span class="badge-subcat">${p.subcategory || p.category}</span>
            <button class="btn-wishlist-heart ${inWish ? 'active' : ''}" data-id="${p.id}" title="${inWish ? 'Remove from Wishlist' : 'Add to Wishlist'}" aria-label="Toggle Wishlist">${inWish ? '♥' : '♡'}</button>
            <a href="/product/${p.handle}" style="display:block; width:100%; height:100%;">
              <img src="${p.image_url}" alt="${p.title}" class="product-card-img" onerror="this.src='https://via.placeholder.com/300x300?text=RoSin+Jewellery'">
            </a>
          </div>
          <div class="product-card-body">
            <h3 class="product-card-title"><a href="/product/${p.handle}" style="color:inherit; text-decoration:none;">${p.title}</a></h3>
            <div class="product-card-price">₹${Number(p.price).toLocaleString('en-IN')}</div>
            <div class="product-card-stock"><span class="stock-dot"></span> In Stock</div>
            <div class="product-card-sizes">${sizesHtml}</div>
            <div class="product-card-actions">
              <a href="/product/${p.handle}" class="btn-card-view">View Details</a>
              <button class="btn-card-cart" data-handle="${p.handle}">Add to Cart</button>
            </div>
          </div>
        `;

        // Wishlist button click listener
        card.querySelector('.btn-wishlist-heart').addEventListener('click', (e) => {
          e.stopPropagation();
          e.preventDefault();
          if (typeof toggleWishlist === 'function') {
            toggleWishlist(p);
          }
        });

        // Add to cart click listener
        card.querySelector('.btn-card-cart').addEventListener('click', () => {
          const defaultSize = p.sizes && p.sizes.length > 0 ? p.sizes[0] : null;
          if (typeof addToCart === 'function') {
            addToCart(p, defaultSize, null, 1);
          }
        });

        productsContainer.appendChild(card);
      });
    } catch (e) {
      console.error('Failed to load products', e);
      productsContainer.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; color: red;">Error loading products.</div>`;
    }
  }
});
