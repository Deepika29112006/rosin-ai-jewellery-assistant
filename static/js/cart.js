/* ==========================================================================
   RoSin Cart Controller
   Cart Items Table, Quantity Adjustment & Direct WhatsApp Order Generator
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  const tableBody = document.getElementById('cart-items-body');
  const emptyView = document.getElementById('cart-empty-view');
  const filledView = document.getElementById('cart-filled-view');
  const subtotalElem = document.getElementById('cart-subtotal');
  const grandTotalElem = document.getElementById('cart-grand-total');
  const waCheckoutBtn = document.getElementById('btn-cart-whatsapp');

  renderCart();

  function renderCart() {
    const cart = getCart();

    if (!cart || cart.length === 0) {
      if (emptyView) emptyView.style.display = 'block';
      if (filledView) filledView.style.display = 'none';
      return;
    }

    if (emptyView) emptyView.style.display = 'none';
    if (filledView) filledView.style.display = 'grid';

    tableBody.innerHTML = '';
    let subtotal = 0;

    cart.forEach(item => {
      const lineTotal = item.price * item.quantity;
      subtotal += lineTotal;

      const tr = document.createElement('tr');
      tr.className = 'cart-table-row';

      const sizeLabel = item.size ? `<span class="cart-item-size">Size: ${item.size}</span>` : '';

      tr.innerHTML = `
        <td class="cart-product-cell">
          <img src="${item.image_url}" alt="${item.title}" class="cart-thumb" onerror="this.src='https://via.placeholder.com/70?text=RoSin'">
          <div class="cart-item-info">
            <a href="/product/${item.handle}" class="cart-item-title">${item.title}</a>
            ${sizeLabel}
          </div>
        </td>
        <td class="cart-price-cell">₹${Number(item.price).toLocaleString('en-IN')}</td>
        <td class="cart-qty-cell">
          <div class="qty-stepper">
            <button class="qty-btn btn-minus" data-key="${item.variantKey}">-</button>
            <span class="qty-val">${item.quantity}</span>
            <button class="qty-btn btn-plus" data-key="${item.variantKey}">+</button>
          </div>
        </td>
        <td class="cart-total-cell">₹${Number(lineTotal).toLocaleString('en-IN')}</td>
        <td class="cart-remove-cell">
          <button class="btn-remove-item" data-key="${item.variantKey}" title="Remove item">&times;</button>
        </td>
      `;

      // Stepper events
      tr.querySelector('.btn-minus').addEventListener('click', () => {
        updateCartQuantity(item.variantKey, -1);
        renderCart();
      });

      tr.querySelector('.btn-plus').addEventListener('click', () => {
        updateCartQuantity(item.variantKey, 1);
        renderCart();
      });

      tr.querySelector('.btn-remove-item').addEventListener('click', () => {
        removeFromCart(item.variantKey);
        renderCart();
      });

      tableBody.appendChild(tr);
    });

    subtotalElem.textContent = `₹${Number(subtotal).toLocaleString('en-IN')}`;
    grandTotalElem.textContent = `₹${Number(subtotal).toLocaleString('en-IN')}`;

    // Configure WhatsApp Order Button
    if (waCheckoutBtn) {
      waCheckoutBtn.onclick = () => {
        let msg = `Hello RoSin Bangles, I would like to place an order from your website:\n\n`;
        cart.forEach((it, idx) => {
          msg += `${idx + 1}. *${it.title}*\n`;
          if (it.size) msg += `   Size: ${it.size}\n`;
          msg += `   Quantity: ${it.quantity} x ₹${Number(it.price).toLocaleString('en-IN')} = ₹${Number(it.price * it.quantity).toLocaleString('en-IN')}\n\n`;
        });
        msg += `----------------------------------------\n`;
        msg += `*Estimated Subtotal: ₹${Number(subtotal).toLocaleString('en-IN')}*\n`;
        msg += `(Shipping to be calculated based on destination pincode)\n\n`;
        msg += `Please send payment details and estimated dispatch date. Thank you!`;

        const encoded = encodeURIComponent(msg);
        window.open(`https://wa.me/918438990370?text=${encoded}`, '_blank');
      };
    }
  }
});
