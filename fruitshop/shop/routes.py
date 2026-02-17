from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, g, session

from fruitshop.database import db
from fruitshop.auth.models import User
from fruitshop.auth.utils import login_required
from fruitshop.shop.models import Fruit, Promotion, Order, OrderItem, OrderReview

bp = Blueprint('shop', __name__)

@bp.route('/')
def index():
    # Get fruits
    fruits = Fruit.query.all()
    
    # Get user, if logged in
    user = None
    if session.get('user_id'):
        user = User.query.get(session['user_id'])
    
    return render_template('index.html', fruits=fruits, user=user)

@bp.route('/checkout/preview', methods=['POST'])
def checkout_preview():
    # Get cart
    cart = request.json
    
    # Calculate subtotal
    subtotal = 0
    for fruit_id, quantity in cart['items'].items():
        fruit = Fruit.query.get(fruit_id)
        if not fruit:
            return jsonify({'error': 'Invalid fruit id'}), 400
        subtotal += fruit.price * quantity
    subtotal = round(subtotal, 2)

    # Calculate discount
    promo = Promotion.query.filter_by(code=cart['promo']).first()
    discount = 0
    if promo and promo.uses_left > 0:
        discount = promo.discount / 100 * subtotal
        discount = round(discount, 2)
        discount = min(discount, subtotal) # Discount cannot be more than subtotal
    else:
        promo = None
        
    # Calculate total
    total = round(subtotal - discount, 2)
    
    return jsonify({
        'subtotal': subtotal,
        'discount': discount,
        'total': total,
        'promo': promo.code if promo else None
    })

@bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    # Get cart
    cart = request.json
    
    # Check if cart is empty
    if len(cart['items']) == 0:
        return jsonify({'error': 'Cart is empty.'}), 400
    
    # Calculate subtotal
    subtotal = 0
    for fruit_id, quantity in cart['items'].items():
        fruit = Fruit.query.get(fruit_id)
        if not fruit:
            return jsonify({'error': 'Invalid fruit id.'}), 400
        subtotal += fruit.price * quantity
    subtotal = round(subtotal, 2)

    # Get promotion discount
    discount = 0
    promo = None
    if cart['promo']:
        promo = Promotion.query.filter_by(code=cart['promo']).first()
        if not promo:
            return jsonify({'error': 'This promo code does not exist.'}), 400
        if promo.uses_left <= 0:
            return jsonify({'error': 'This promo code has expired.'}), 400

        discount = promo.discount

    # Calculate discount
    discount = discount / 100 * subtotal
    discount = round(discount, 2)
    discount = min(discount, subtotal) # Discount cannot be more than subtotal
        
    # Calculate total
    total = round(subtotal - discount, 2)
    
    if g.user.balance < total:
        return jsonify({'error': 'You do not have enough balance for this purchase.'}), 400
    
    # Decrement promotion uses
    if promo:
        promo.uses_left = promo.uses_left - 1
        db.session.commit()
    
    # Create order
    order = Order(
        user_id=g.user.id,
        promo=promo.code if promo else None,
        subtotal=subtotal,
        discount=discount,
        total=total
    )
    db.session.add(order)
    db.session.commit()
    
    # Add items
    for fruit_id, quantity in cart['items'].items():
        fruit = Fruit.query.get(fruit_id)
        item = OrderItem(
            order=order,
            fruit_id=fruit.id,
            quantity=quantity
        )
        db.session.add(item)
        db.session.commit()
    
    # Deduct from balance
    g.user.balance = round(g.user.balance - total, 2)
    db.session.commit()
    
    flash('Order placed.', 'success')
    
    return jsonify({
        'success': True,
        'order_id': order.id
    }), 200

@bp.route('/orders')
@login_required
def orders():
    # Get orders in reverse chronological order
    orders = Order.query.filter_by(user_id=g.user.id).order_by(Order.date_created.desc()).all()
    
    return render_template('orders.html', orders=orders)

@bp.route('/orders/<int:order_id>')
@login_required
def order(order_id):
    order = Order.query.filter_by(id=order_id, user_id=g.user.id).first()
    if not order:
        flash('Order not found.', 'warning')
        return redirect(url_for('shop.orders'))
    
    return render_template('order.html', order=order)

@bp.route('/orders/<int:order_id>/review')
@login_required
def order_review(order_id):
    order = Order.query.filter_by(id=order_id, user_id=g.user.id).first()
    if not order:
        flash('Order not found.', 'warning')
        return redirect(url_for('shop.orders'))
    
    if order.review:
        flash('You have already reviewed this order.', 'warning')
        return redirect(url_for('shop.order', order_id=order_id))
    
    return render_template('order_review.html', order=order)

@bp.route('/orders/<int:order_id>/review', methods=['POST'])
@login_required
def order_review_submit(order_id):
    order = Order.query.filter_by(id=order_id, user_id=g.user.id).first()
    if not order:
        flash('Order not found.', 'warning')
        return redirect(url_for('shop.orders'))

    title = request.form.get('title')
    comments = request.form.get('comments')
    
    if not title or not comments:
        flash('Please enter your review title and comments.', 'warning')
        return redirect(url_for('shop.order_review', order_id=order_id))
    
    if len(title) > 50:
        flash('Review title cannot be more than 50 characters.', 'warning')
        return redirect(url_for('shop.order_review', order_id=order_id))
    
    if len(comments) > 1000:
        flash('Review comments cannot be more than 1000 characters.', 'warning')
        return redirect(url_for('shop.order_review', order_id=order_id))
    
    # Check if review already exists
    if order.review:
        flash('You have already reviewed this order.', 'warning')
        return redirect(url_for('shop.order_review', order_id=order_id))
    
    # Create new review
    review = OrderReview(
        order_id=order.id,
        title=title,
        comments=comments
    )
    
    db.session.add(review)
    db.session.commit()
    
    flash('Thank you for your review!', 'success')
    return redirect(url_for('shop.reviews'))

@bp.route('/reviews', defaults={'page': 1})
@bp.route('/reviews/<int:page>')
def reviews(page):
    per_page = 9
    review_count = OrderReview.query.count()
    total_pages = (review_count - 1) // per_page + 1
    total_pages = max(total_pages, 1)
    
    if page < 1 or page > total_pages:
        flash('Page not found.', 'warning')
        return redirect(url_for('shop.reviews'))
    
    reviews = OrderReview.query.order_by(OrderReview.date_created.desc()).paginate(page=page, per_page=per_page)
    
    reviews = [
        {
            'order_id': review.order_id,
            'title': review.title,
            'comments': review.comments,
            'date': review.date_created.strftime('%B %d %Y'),
            'username': review.order.user.username,
            'order_items': [
                {
                    'name': item.fruit.name
                }
                for item in review.order.items
            ]
        }
        for review in reviews
    ]

    review_contents = []

    for review in reviews:
        review_content = "<h5 class='card-title'>"
        review_content += f'"{review["title"]}" by {review["username"]}\n'
        for item in review["order_items"]:
            review_content += f'<img src="{ url_for("static", filename="images/" + item["name"].lower() + ".png") }" alt="{ item["name"] }" class="mr-2" style="width: 24px; height: 24px;">'
        review_content += "</h5>"
        review_content += f'<p class="card-text">{ review["comments"] }</p>'
        review_content += f'<p class="card-text">Written on { review["date"] }</p>'
        review_contents.append(review_content)
    
    return render_template('reviews.html', reviews=review_contents, page=page, total_pages=total_pages)