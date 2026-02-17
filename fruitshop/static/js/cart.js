function loadCartFromStorage() {
    // Get existing cart from the local session
    var cart = JSON.parse(localStorage.getItem('cart')) || {'items': [], 'promoCode': null};

    // Return the cart
    return cart;
}

function saveCartToStorage(cart) {
    // Update the local session with the new cart items
    localStorage.setItem('cart', JSON.stringify(cart));
}

function clearCartStorage() {
    // Clear the local session
    localStorage.removeItem('cart');
}

async function openCart() {
    let cart = loadCartFromStorage();

    // If no items in the cart, do nothing
    if (cart.items.length === 0) {
        return;
    }

    // Display checkout preview loading
    updateCheckoutPreview(true, null);

    // Show cart
    var cartOffcanvas = new bootstrap.Offcanvas(document.getElementById('cartOffcanvas'));
    cartOffcanvas.show();

    // Get the checkout preview
    let checkoutPreview = await getCheckoutPreview(cart);

    // Update cart display
    updateCartDisplay(cart, checkoutPreview);
}

function closeCart() {
    // Hide cart
    bootstrap.Offcanvas.getInstance(document.getElementById('cartOffcanvas'))?.hide();
}

function addToCart(fruitId, fruitName, imageUrl) {
    // Get existing cart from the local session
    var cart = loadCartFromStorage();

    // Check if the fruit is already in the cart
    var existingItem = cart.items.find(item => item.id === fruitId);

    if (existingItem) {
        // Increment quantity if the item is already in the cart
        existingItem.quantity += 1;
    } else {
        // Add a new item to the cart
        cart.items.push({ id: fruitId, name: fruitName, imageUrl: imageUrl, quantity: 1 });
    }

    // Update the local session with the new cart items
    saveCartToStorage(cart);

    // Open the cart display
    openCart();
}

async function removeFromCart(index) {
    // Get existing cart from the local session
    var cart = loadCartFromStorage();

    // Remove the item at the specified index
    cart.items.splice(index, 1);

    // Update the local session with the updated cart items
    saveCartToStorage(cart);

    // Display checkout preview loading
    updateCheckoutPreview(true, null);

    // Get the checkout preview
    let checkoutPreview = await getCheckoutPreview(cart);

    // Refresh the cart display
    updateCartDisplay(cart, checkoutPreview);
}

function enableCheckout() {
    // Enable the Checkout button
    document.getElementById('checkoutButton').disabled = false;
}

function disableCheckout() {
    // Disable the Checkout button
    document.getElementById('checkoutButton').disabled = true;
}

function getCartDetails(cart) {
    // Prepare the cart for checkout
    let cartDetails = {
        items: Object.fromEntries(cart.items.map(item => [item.id, item.quantity])),
        promo: cart.promoCode
    };

    return cartDetails;
}

async function getCheckoutPreview(cart) {
    // Prepare the cart for checkout preview
    let cartDetails = getCartDetails(cart);

    // Send a POST request to /checkout/preview to get the cart price
    const response = await fetch('/checkout/preview', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(cartDetails),
    });
    const data = await response.json();
    return data;
}

function updateCartDisplay(cart, checkoutPreview) {
    // Clear error text
    clearCheckoutError();

    // Get the cart items container
    var cartItemsContainer = document.getElementById('cartItems');

    // Clear the existing content
    cartItemsContainer.innerHTML = '';

    // Display each item in the cart
    cart.items.forEach((item, index) => {
        var cartItem = document.createElement('div');
        cartItem.classList.add('mb-2');
        cartItem.innerHTML = `
            <div class="d-flex justify-content-between">
                <img src="${item.imageUrl}" alt="${item.name}" class="mr-2" style="width: 30px; height: 30px;">
                <span>${item.name} x${item.quantity}</span>
                <button class="btn btn-sm btn-danger" onclick="removeFromCart(${index})"><i class="fas fa-times"></i></button>
            </div>
        `;
        cartItemsContainer.appendChild(cartItem);
    });

    // Display the promo code input field
    var promoCodeInput = document.getElementById('promoCode');
    promoCodeInput.value = cart.promoCode;

    // Update checkout preview
    updateCheckoutPreview(false, checkoutPreview);

    // If no items in the cart, close the cart
    if (cart.items.length === 0) {
        closeCart();
    }
}

function updateCheckoutPreview(loading, checkoutPreview) {
    if (loading) {
        // Disable checking out
        disableCheckout();

        // Hide the checkout preview
        document.getElementById('checkoutPreview').classList.add('d-none');

        // Show the loading spinner
        document.getElementById('checkoutLoading').classList.remove('d-none');

        return;
    }

    // Hide the loading spinner
    document.getElementById('checkoutLoading').classList.add('d-none');

    if (!checkoutPreview) {
        // Disable checking out
        disableCheckout();
        return;
    }

    // Show the checkout preview
    document.getElementById('checkoutPreview').classList.remove('d-none');

    // Update the checkout preview
    var checkoutSubtotal = document.getElementById('checkoutSubtotal');
    var checkoutDiscount = document.getElementById('checkoutDiscount');
    var checkoutTotal = document.getElementById('checkoutTotal');

    checkoutSubtotal.textContent = '$' + checkoutPreview.subtotal.toFixed(2);
    checkoutDiscount.textContent = '-$' + checkoutPreview.discount.toFixed(2);
    checkoutTotal.textContent = '$' + checkoutPreview.total.toFixed(2);

    if (checkoutPreview.promo) {
        checkoutDiscount.textContent += ` (${checkoutPreview.promo})`
    }

    // Enable checking out
    enableCheckout();
}

function showCheckoutError(errorText) {
    // Show the error text
    document.getElementById('checkoutErrorText').textContent = errorText;
}

function clearCheckoutError() {
    showCheckoutError('');
}

async function applyPromoCode() {
    // Get the promo code from the input field
    const promoCodeInput = document.getElementById('promoCode');
    const promoCode = promoCodeInput.value;
    
    // Get existing cart from the local session
    var cart = loadCartFromStorage();

    // Update the cart with the promo code
    cart.promoCode = promoCode;

    // Update the local session with the updated cart items
    saveCartToStorage(cart);

    // Display checkout preview loading
    updateCheckoutPreview(true, null);

    // Get the checkout preview
    let checkoutPreview = await getCheckoutPreview(cart);

    // Check if the promo code is valid
    if (checkoutPreview.promo) {
        // Update the saved promo code
        cart.promoCode = checkoutPreview.promo;
    }

    // Refresh the cart display
    updateCartDisplay(cart, checkoutPreview);
}

async function checkout() {
    // Get existing cart from the local session
    var cart = loadCartFromStorage();

    // Clear the cart
    clearCartStorage();

    // Prepare the cart for checkout preview
    let cartDetails = getCartDetails(cart);

    // Post checkout request
    const response = await fetch('/checkout', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(cartDetails),
    });

    console.log(response);

    // If redirected, we probably aren't logged in
    if (response.redirected) {
        // Re-save the cart before redirecting
        saveCartToStorage(cart);

        // Redirect
        window.location.href = response.url;
        return;
    }

    // If the response is not OK, show an error
    if (!response.ok) {
        // Re-save the cart
        saveCartToStorage(cart);

        const data = await response.json();
        showCheckoutError(data['error']);
        return;
    }

    // Get the order ID
    const data = await response.json();
    const orderId = data['order_id'];

    // Redirect to the checkout result page
    window.location.href = '/orders/' + orderId;
}

// Open the cart when the page loads
window.onload = openCart;