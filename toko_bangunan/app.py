import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# --- App Configuration ---
app = Flask(__name__)
# Get the absolute path of the directory where the script is running
basedir = os.path.abspath(os.path.dirname(__file__))
# Configure the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'toko.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Database Models ---

class Product(db.Model):
    """Model untuk Master Barang"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    purchase_price = db.Column(db.Float, nullable=False, default=0.0)
    selling_price = db.Column(db.Float, nullable=False, default=0.0)
    stock = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f'<Product {self.name}>'

class Customer(db.Model):
    """Model untuk Master Pelanggan"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        return f'<Customer {self.name}>'

class Supplier(db.Model):
    """Model untuk Master Pemasok"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        return f'<Supplier {self.name}>'

class PurchaseOrder(db.Model):
    """Model untuk Purchase Order (Header)"""
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='Pending') # Pending, Completed

    supplier = db.relationship('Supplier', backref=db.backref('purchase_orders', lazy=True))
    items = db.relationship('PurchaseOrderItem', backref='purchase_order', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<PurchaseOrder {self.id}>'

class PurchaseOrderItem(db.Model):
    """Model untuk item barang dalam Purchase Order"""
    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)

    product = db.relationship('Product')

    def __repr__(self):
        return f'<PurchaseOrderItem PO:{self.purchase_order_id} Product:{self.product_id}>'

class SalesOrder(db.Model):
    """Model untuk Sales Order (Header)"""
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='Pending') # Pending, Shipped

    customer = db.relationship('Customer', backref=db.backref('sales_orders', lazy=True))
    items = db.relationship('SalesOrderItem', backref='sales_order', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<SalesOrder {self.id}>'

class SalesOrderItem(db.Model):
    """Model untuk item barang dalam Sales Order"""
    id = db.Column(db.Integer, primary_key=True)
    sales_order_id = db.Column(db.Integer, db.ForeignKey('sales_order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)

    product = db.relationship('Product')

    def __repr__(self):
        return f'<SalesOrderItem SO:{self.sales_order_id} Product:{self.product_id}>'

class PurchaseInvoice(db.Model):
    """Model untuk faktur pembelian dari supplier"""
    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_order.id'), nullable=False)
    invoice_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Unpaid') # Unpaid, Paid

    purchase_order = db.relationship('PurchaseOrder', backref=db.backref('invoice', uselist=False))

    def __repr__(self):
        return f'<PurchaseInvoice {self.id} for PO {self.purchase_order_id}>'

class SalesInvoice(db.Model):
    """Model untuk faktur penjualan ke customer"""
    id = db.Column(db.Integer, primary_key=True)
    sales_order_id = db.Column(db.Integer, db.ForeignKey('sales_order.id'), nullable=False)
    invoice_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Unpaid') # Unpaid, Paid

    sales_order = db.relationship('SalesOrder', backref=db.backref('invoice', uselist=False))

    def __repr__(self):
        return f'<SalesInvoice {self.id} for SO {self.sales_order_id}>'

# --- Routes ---

@app.route('/')
def index():
    """Homepage, redirect to products list"""
    return redirect(url_for('products'))

@app.route('/products')
def products():
    """Menampilkan daftar semua barang"""
    all_products = Product.query.all()
    return render_template('products.html', products=all_products)

@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    """Menambah barang baru"""
    if request.method == 'POST':
        new_product = Product(
            name=request.form['name'],
            description=request.form['description'],
            purchase_price=float(request.form['purchase_price']),
            selling_price=float(request.form['selling_price']),
            stock=0  # Stok awal diatur ke 0
        )
        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for('products'))
    return render_template('product_form.html')

@app.route('/products/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    """Mengedit barang yang ada"""
    product_to_edit = Product.query.get_or_404(id)
    if request.method == 'POST':
        product_to_edit.name = request.form['name']
        product_to_edit.description = request.form['description']
        product_to_edit.purchase_price = float(request.form['purchase_price'])
        product_to_edit.selling_price = float(request.form['selling_price'])
        db.session.commit()
        return redirect(url_for('products'))
    return render_template('product_form.html', product=product_to_edit)

@app.route('/products/delete/<int:id>', methods=['POST'])
def delete_product(id):
    """Menghapus barang"""
    product_to_delete = Product.query.get_or_404(id)
    db.session.delete(product_to_delete)
    db.session.commit()
    return redirect(url_for('products'))


# --- Customer Routes ---

@app.route('/customers')
def customers():
    """Menampilkan daftar semua customer"""
    all_customers = Customer.query.all()
    return render_template('customers.html', customers=all_customers)

@app.route('/customers/add', methods=['GET', 'POST'])
def add_customer():
    """Menambah customer baru"""
    if request.method == 'POST':
        new_customer = Customer(
            name=request.form['name'],
            address=request.form['address'],
            phone=request.form['phone']
        )
        db.session.add(new_customer)
        db.session.commit()
        return redirect(url_for('customers'))
    return render_template('customer_form.html')

@app.route('/customers/edit/<int:id>', methods=['GET', 'POST'])
def edit_customer(id):
    """Mengedit customer yang ada"""
    customer_to_edit = Customer.query.get_or_404(id)
    if request.method == 'POST':
        customer_to_edit.name = request.form['name']
        customer_to_edit.address = request.form['address']
        customer_to_edit.phone = request.form['phone']
        db.session.commit()
        return redirect(url_for('customers'))
    return render_template('customer_form.html', customer=customer_to_edit)

@app.route('/customers/delete/<int:id>', methods=['POST'])
def delete_customer(id):
    """Menghapus customer"""
    customer_to_delete = Customer.query.get_or_404(id)
    db.session.delete(customer_to_delete)
    db.session.commit()
    return redirect(url_for('customers'))


# --- Supplier Routes ---

@app.route('/suppliers')
def suppliers():
    """Menampilkan daftar semua supplier"""
    all_suppliers = Supplier.query.all()
    return render_template('suppliers.html', suppliers=all_suppliers)

@app.route('/suppliers/add', methods=['GET', 'POST'])
def add_supplier():
    """Menambah supplier baru"""
    if request.method == 'POST':
        new_supplier = Supplier(
            name=request.form['name'],
            address=request.form['address'],
            phone=request.form['phone']
        )
        db.session.add(new_supplier)
        db.session.commit()
        return redirect(url_for('suppliers'))
    return render_template('supplier_form.html')

@app.route('/suppliers/edit/<int:id>', methods=['GET', 'POST'])
def edit_supplier(id):
    """Mengedit supplier yang ada"""
    supplier_to_edit = Supplier.query.get_or_404(id)
    if request.method == 'POST':
        supplier_to_edit.name = request.form['name']
        supplier_to_edit.address = request.form['address']
        supplier_to_edit.phone = request.form['phone']
        db.session.commit()
        return redirect(url_for('suppliers'))
    return render_template('supplier_form.html', supplier=supplier_to_edit)

@app.route('/suppliers/delete/<int:id>', methods=['POST'])
def delete_supplier(id):
    """Menghapus supplier"""
    supplier_to_delete = Supplier.query.get_or_404(id)
    db.session.delete(supplier_to_delete)
    db.session.commit()
    return redirect(url_for('suppliers'))


# --- Purchase Order Routes ---

@app.route('/purchase-orders')
def list_purchase_orders():
    """Menampilkan daftar semua purchase order"""
    all_pos = PurchaseOrder.query.order_by(PurchaseOrder.order_date.desc()).all()
    return render_template('purchase_orders.html', purchase_orders=all_pos)

@app.route('/purchase-orders/add', methods=['GET', 'POST'])
def add_purchase_order():
    """Membuat header PO baru"""
    if request.method == 'POST':
        supplier_id = request.form.get('supplier_id')
        new_po = PurchaseOrder(supplier_id=supplier_id)
        db.session.add(new_po)
        db.session.commit()
        return redirect(url_for('view_purchase_order', id=new_po.id))

    suppliers = Supplier.query.all()
    return render_template('purchase_order_form.html', suppliers=suppliers)

@app.route('/purchase-orders/<int:id>')
def view_purchase_order(id):
    """Menampilkan detail PO dan item-itemnya"""
    po = PurchaseOrder.query.get_or_404(id)
    all_products = Product.query.all()
    return render_template('purchase_order_detail.html', po=po, all_products=all_products)

@app.route('/purchase-orders/<int:po_id>/add-item', methods=['POST'])
def add_po_item(po_id):
    """Menambah item ke PO"""
    po = PurchaseOrder.query.get_or_404(po_id)
    if po.status == 'Completed':
        # Optionally, add a flash message here to inform the user
        return redirect(url_for('view_purchase_order', id=po_id))

    product_id = request.form.get('product_id')
    quantity = request.form.get('quantity')
    price = request.form.get('price')

    new_item = PurchaseOrderItem(
        purchase_order_id=po_id,
        product_id=product_id,
        quantity=int(quantity),
        price_per_unit=float(price)
    )
    db.session.add(new_item)
    db.session.commit()
    return redirect(url_for('view_purchase_order', id=po_id))

@app.route('/purchase-orders/item/<int:item_id>/delete', methods=['POST'])
def delete_po_item(item_id):
    """Menghapus item dari PO"""
    item_to_delete = PurchaseOrderItem.query.get_or_404(item_id)
    po_id = item_to_delete.purchase_order_id
    po = PurchaseOrder.query.get_or_404(po_id)

    if po.status == 'Pending':
        db.session.delete(item_to_delete)
        db.session.commit()

    return redirect(url_for('view_purchase_order', id=po_id))

@app.route('/purchase-orders/<int:po_id>/receive', methods=['POST'])
def receive_po(po_id):
    """Menyelesaikan PO, menerima barang, memperbarui stok, dan membuat faktur."""
    po = PurchaseOrder.query.get_or_404(po_id)

    if po.status == 'Pending':
        total_amount = 0
        # Loop through each item in the PO
        for item in po.items:
            product = Product.query.get(item.product_id)
            if product:
                # Increase the stock
                product.stock += item.quantity
            total_amount += item.quantity * item.price_per_unit

        # Create invoice
        new_invoice = PurchaseInvoice(
            purchase_order_id=po.id,
            total_amount=total_amount
        )
        db.session.add(new_invoice)

        # Update the PO status
        po.status = 'Completed'

        db.session.commit()

    return redirect(url_for('view_purchase_order', id=po_id))


# --- Sales Order Routes ---

@app.route('/sales-orders')
def list_sales_orders():
    """Menampilkan daftar semua sales order"""
    all_sos = SalesOrder.query.order_by(SalesOrder.order_date.desc()).all()
    return render_template('sales_orders.html', sales_orders=all_sos)

@app.route('/sales-orders/add', methods=['GET', 'POST'])
def add_sales_order():
    """Membuat header SO baru"""
    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        new_so = SalesOrder(customer_id=customer_id)
        db.session.add(new_so)
        db.session.commit()
        return redirect(url_for('view_sales_order', id=new_so.id))

    customers = Customer.query.all()
    return render_template('sales_order_form.html', customers=customers)

@app.route('/sales-orders/<int:id>')
def view_sales_order(id):
    """Menampilkan detail SO dan item-itemnya"""
    so = SalesOrder.query.get_or_404(id)
    all_products = Product.query.order_by(Product.name).all()
    return render_template('sales_order_detail.html', so=so, all_products=all_products)

@app.route('/sales-orders/<int:so_id>/add-item', methods=['POST'])
def add_so_item(so_id):
    """Menambah item ke SO"""
    so = SalesOrder.query.get_or_404(so_id)
    if so.status != 'Pending':
        return redirect(url_for('view_sales_order', id=so_id))

    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity'))
    price = float(request.form.get('price'))

    product = Product.query.get_or_404(product_id)
    if product.stock < quantity:
        # Not enough stock, maybe add a flash message
        return redirect(url_for('view_sales_order', id=so_id))

    new_item = SalesOrderItem(
        sales_order_id=so_id,
        product_id=product_id,
        quantity=quantity,
        price_per_unit=price
    )
    db.session.add(new_item)
    db.session.commit()
    return redirect(url_for('view_sales_order', id=so_id))

@app.route('/sales-orders/item/<int:item_id>/delete', methods=['POST'])
def delete_so_item(item_id):
    """Menghapus item dari SO"""
    item_to_delete = SalesOrderItem.query.get_or_404(item_id)
    so_id = item_to_delete.sales_order_id
    so = SalesOrder.query.get_or_404(so_id)

    if so.status == 'Pending':
        db.session.delete(item_to_delete)
        db.session.commit()

    return redirect(url_for('view_sales_order', id=so_id))

@app.route('/sales-orders/<int:so_id>/ship', methods=['POST'])
def ship_so(so_id):
    """Menyelesaikan SO, mengirim barang, memperbarui stok, dan membuat faktur."""
    so = SalesOrder.query.get_or_404(so_id)

    if so.status != 'Pending':
        return redirect(url_for('view_sales_order', id=so_id))

    # 1. Check stock availability for all items first
    for item in so.items:
        if item.product.stock < item.quantity:
            # Not enough stock for at least one item, abort the whole operation
            print(f"ERROR: Insufficient stock for {item.product.name}. Required: {item.quantity}, Available: {item.product.stock}")
            return redirect(url_for('view_sales_order', id=so_id))

    # 2. If all checks pass, proceed with stock reduction and invoice calculation
    total_amount = 0
    for item in so.items:
        item.product.stock -= item.quantity
        total_amount += item.quantity * item.price_per_unit

    # 3. Create invoice
    new_invoice = SalesInvoice(
        sales_order_id=so.id,
        total_amount=total_amount
    )
    db.session.add(new_invoice)

    # 4. Update the SO status
    so.status = 'Shipped'

    db.session.commit()

    return redirect(url_for('view_sales_order', id=so_id))


# --- Financial Routes ---

@app.route('/reports/profit')
def profit_report():
    """Menampilkan laporan keuntungan kotor."""
    # Ambil semua item dari sales order yang sudah dikirim
    shipped_items = SalesOrderItem.query.join(SalesOrder).filter(SalesOrder.status == 'Shipped').all()
    return render_template('profit_report.html', sales_items=shipped_items)

@app.route('/invoices')
def list_invoices():
    """Menampilkan daftar semua faktur pembelian dan penjualan."""
    purchase_invoices = PurchaseInvoice.query.order_by(PurchaseInvoice.invoice_date.desc()).all()
    sales_invoices = SalesInvoice.query.order_by(SalesInvoice.invoice_date.desc()).all()
    return render_template('invoices.html', purchase_invoices=purchase_invoices, sales_invoices=sales_invoices)

@app.route('/invoices/purchase/<int:invoice_id>/pay', methods=['POST'])
def pay_purchase_invoice(invoice_id):
    """Menandai faktur pembelian sebagai lunas."""
    invoice = PurchaseInvoice.query.get_or_404(invoice_id)
    invoice.status = 'Paid'
    db.session.commit()
    return redirect(url_for('list_invoices'))

@app.route('/invoices/sales/<int:invoice_id>/pay', methods=['POST'])
def receive_payment_sales_invoice(invoice_id):
    """Menandai faktur penjualan sebagai lunas."""
    invoice = SalesInvoice.query.get_or_404(invoice_id)
    invoice.status = 'Paid'
    db.session.commit()
    return redirect(url_for('list_invoices'))

@app.route('/invoices/sales/<int:invoice_id>/print')
def print_sales_invoice(invoice_id):
    """Menampilkan halaman cetak untuk faktur penjualan."""
    invoice = SalesInvoice.query.get_or_404(invoice_id)
    return render_template('invoice_print.html', invoice=invoice)

@app.route('/invoices/purchase/<int:invoice_id>')
def view_purchase_invoice(invoice_id):
    """Menampilkan detail faktur pembelian."""
    invoice = PurchaseInvoice.query.get_or_404(invoice_id)
    return render_template('invoice_detail.html', invoice=invoice, invoice_type='purchase')

@app.route('/invoices/sales/<int:invoice_id>')
def view_sales_invoice(invoice_id):
    """Menampilkan detail faktur penjualan."""
    invoice = SalesInvoice.query.get_or_404(invoice_id)
    return render_template('invoice_detail.html', invoice=invoice, invoice_type='sales')

# --- Main Execution ---

if __name__ == '__main__':
    # This block will be used to initialize the database
    with app.app_context():
        # Check if the database file already exists
        db_path = os.path.join(basedir, 'toko.db')
        if not os.path.exists(db_path):
            print("Creating database and tables...")
            db.create_all()
            print("Database and tables created successfully.")

    # Run the Flask application
    app.run(debug=False, host='0.0.0.0')
