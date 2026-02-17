from flask import Blueprint, render_template, request, redirect, url_for, flash

from fruitshop.auth.utils import admin_required
from fruitshop.database import db
from fruitshop.shop.models import Promotion

bp = Blueprint('admin', __name__)

@bp.route('/admin')
@admin_required
def index():
    promo_codes = db.session.query(Promotion).all()
    
    return render_template('admin.html', promo_codes=promo_codes)

@bp.route('/admin/promo', methods=['POST'])
@admin_required
def add_promo():
    try:
        code = request.form['code']
        discount = round(float(request.form['discount']), 2)
        uses_left = int(request.form['uses_left'])
        
        assert discount >= 0 and discount <= 100
        assert uses_left >= 0
    except:
        flash('Invalid input.', 'warning')
        return redirect(url_for('admin.index'))
    
    
    promo = Promotion(code=code, discount=discount, uses_left=uses_left)
    db.session.add(promo)
    db.session.commit()
    
    flash('Promo code added.', 'success')
    return redirect(url_for('admin.index'))

@bp.route('/admin/promo/<int:code_id>/delete', methods=['POST'])
@admin_required
def delete_promo(code_id):
    promo = Promotion.query.get(code_id)
    
    if not promo:
        flash('Promo code not found.', 'warning')
        return redirect(url_for('admin.index'))
    
    db.session.delete(promo)
    db.session.commit()
    
    flash('Promo code deleted.', 'success')
    return redirect(url_for('admin.index'))