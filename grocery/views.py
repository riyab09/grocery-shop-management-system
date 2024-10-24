from django.shortcuts import render, HttpResponse, redirect
import mysql.connector as sql
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
from django.db import connection
from datetime import date

user_id = None  

def index(request):
    return render(request, 'index.html')

def login_view(request):
    global user_id
    if request.method == 'POST':
        # Get the data from the request
        data = json.loads(request.body)
        
        # Connect to the database
        connection = sql.connect(host="localhost", user="root", passwd="riya2003", database="shop")
        cursor = connection.cursor()

        email = data.get('email')
        password = data.get('password')

        # Check if the user exists
        cursor.execute("SELECT user_id FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()

        if user:
            user_id = user[0]
            # Redirect to the products page after successful login
            return JsonResponse({'redirect': '/products/'})  # Adjust the URL as needed
        else:
            return JsonResponse({'error': 'Invalid credentials'})

    # Render the login page for GET requests
    return render(request, 'login.html')




def admin_action(request):
    if request.method == "POST":
        m = sql.connect(host="localhost", user="root", passwd="riya2003", database="shop")
        cursor = m.cursor()

        action = request.POST.get('action')

        if action == "add":
            # Adding a new product
            name = request.POST.get("name")
            category = request.POST.get("category")
            price = request.POST.get("price")
            stock = request.POST.get("stock_quantity")

            c = "INSERT INTO products (name, category, price, stock_quantity) VALUES (%s, %s, %s, %s)"
            cursor.execute(c, (name, category, price, stock))

        elif action == "update":
            # Updating a product
            price = request.POST.get("price")
            stock = request.POST.get("updatestock")
            product_id = request.POST.get("id")

            cursor.execute("UPDATE products SET price = %s, stock_quantity = %s WHERE product_id = %s",
                           (price, stock, product_id))

        elif action == "delete":
            # Deleting a product
            product_id = request.POST.get("id")
            cursor.execute("DELETE FROM products WHERE product_id = %s", (product_id,))

        elif action == "vieworder":
            # Fetching order details from the orders table
            return fetch_orders(request)



        m.commit()  # Commit changes
        cursor.close()
        m.close()  # Close the connection

        # Redirect to the admin page to refresh the product list
        return redirect('admin_action')  # Replace with your actual admin page view name
        

    else:
        # Handle GET requests - Fetch and display products
        return fetch_products(request)

def fetch_products(request):
    m = sql.connect(host="localhost", user="root", passwd="riya2003", database="shop")
    cursor = m.cursor()

    # Handle sorting options from GET parameters
    price_sort = request.GET.get('price_sort')
    stock_sort = request.GET.get('stock_sort')
    search_term = request.GET.get('search')

    query = "SELECT product_id, name, category, price, stock_quantity FROM products"
    filters = []

    if search_term:
        filters.append(f"(name LIKE '%{search_term}%' OR category LIKE '%{search_term}%')")

    if filters:
        query += " WHERE " + " AND ".join(filters)

    sort_clauses = []
    if price_sort:
        sort_clauses.append(f"price {price_sort.upper()}")
    if stock_sort:
        sort_clauses.append(f"stock_quantity {stock_sort.upper()}")

    if sort_clauses:
        query += " ORDER BY " + ", ".join(sort_clauses)

    cursor.execute(query)
    products = cursor.fetchall()
    cursor.close()
    m.close()

    product_list = [
        {
            'id': product[0],
            'name': product[1],
            'category': product[2],
            'price': product[3],
            'stock_quantity': product[4],
        }
        for product in products
    ]

    return render(request, 'admin.html', {'products': product_list})
    
# views.py
def fetch_orders(request):
    # Fetch order details from the database
    m = sql.connect(host="localhost", user="root", passwd="riya2003", database="shop")
    cursor = m.cursor()

    query = """
    SELECT order_id, user_id, order_date, total_amount 
    FROM orders 
    ORDER BY order_date DESC
    """
    cursor.execute(query)
    orders = cursor.fetchall()
    cursor.close()
    m.close()

    # Create a list of orders to pass to the template
    orders_list = [
        {
            'order_id': order[0],
            'user_id': order[1],
            'order_date': order[2],
            'total_amount': order[3],
        }
        for order in orders
    ]

    return render(request, 'admin.html', {'orders': orders_list})



def customer_page(request):
    # Connect to the database
    m = sql.connect(host="localhost", user="root", passwd="riya2003", database="shop")
    cursor = m.cursor()
    
    # Fetch products from the database
    cursor.execute("SELECT product_id, name, category, price, stock_quantity FROM products")
    products = cursor.fetchall()

    # Format the products into a list of dictionaries for easy access in the template
    formatted_products = [
        {
            'product_id': product[0],
            'name': product[1],
            'category': product[2],
            'price': float(product[3]),
            'stock_quantity': product[4]
        }
        for product in products
    ]

    cursor.close()
    m.close()  # Close the connection

    context = {
        'products': formatted_products,
    }
    return render(request, 'customerpage.html', context)

def place_order(request):
    global user_id

    if request.method == 'POST':
        # Connect to the database
        conn = sql.connect(user='root', password='riya2003',
                           host='localhost', database='shop')
        cursor = conn.cursor()

        # Parse cart data sent from frontend
        cart_data = request.POST.get('cart')  # Example: "1,2;3,1"
        items = [item.split(',') for item in cart_data.split(';')]  
        # [['1', '2'], ['3', '1']] -> product_id, quantity pairs

        total_amount = 0

        # Calculate total amount by fetching product prices
        for product_id, quantity in items:
            cursor.execute(
                "SELECT price FROM products WHERE product_id = %s", (product_id,)
            )
            price = cursor.fetchone()[0]
            total_amount += price * int(quantity)

            # Reduce stock in the `products` table
            cursor.execute(
                "UPDATE products SET stock_quantity = stock_quantity - %s WHERE product_id = %s",
                (quantity, product_id)
            )

        # Insert order details into the `orders` table
        order_date = date.today()
        cursor.execute(
            "INSERT INTO orders (user_id, order_date, total_amount) VALUES (%s, %s, %s)",
            (user_id, order_date, total_amount)
        )
        conn.commit()

        cursor.close()
        conn.close()

        return JsonResponse({'success': 'Order placed successfully!'})

    return JsonResponse({'error': 'Invalid request'}, status=400)

print(user_id)