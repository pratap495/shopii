import requests
import pika
import http.client
import urllib.parse
import os
import re
import json
import time
import random
import smtplib
import jwt
import datetime
from email.mime.text import MIMEText
from serpapi import GoogleSearch
from database import AuthDatabase

# Initialize Database
db = AuthDatabase()
db.setup_database()

SECRET_KEY = "your_secret_key"

def send_email(recipient_email, otp):
    """Sends the OTP via email using SMTP."""
    # TODO: Replace with your actual SMTP details
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "hackerpratap7@gmail.com" # TODO: Update this to your actual gmail address
    sender_password = "suto tqtz ylfg nlhq"  # For Gmail, use an App Password

    subject = "Password Reset OTP"
    body = f"Your OTP for password reset is: {otp}"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_email

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, sender_password.replace(" ", ""))
            server.sendmail(sender_email, recipient_email, msg.as_string())
        print(f" [EMAIL] OTP sent successfully to {recipient_email}")
        return True
    except Exception as e:
        print(f" [!] Failed to send email: {e}")
        return False

def parse_price(price_str):
    """Extracts numeric price from string (e.g., '₹1,299.00' -> 1299.0)."""
    if not price_str:
        return float('inf')
    try:
        # Remove non-numeric chars except dot
        clean_price = re.sub(r'[^\d.]', '', str(price_str))
        return float(clean_price) if clean_price else float('inf')
    except ValueError:
        return float('inf')

def parse_rating(rating_str):
    """Extracts numeric rating from string (e.g., '4.5 out of 5' -> 4.5)."""
    if not rating_str:
        return 0.0
    try:
        match = re.search(r"(\d+(\.\d+)?)", str(rating_str))
        return float(match.group(1)) if match else 0.0
    except ValueError:
        return 0.0

def search_amazon(keyword):
    """Searches Amazon using SerpApi and parses the results."""
    try:
        params = {
            "engine": "amazon",
            "k": keyword,
            "amazon_domain": "amazon.in",
            "language": "en_IN",
            "shipping_location": "IN",
            "delivery_zip": "560001",
            "api_key": "8147694a474fa1d7f9d20570827a0356fb3c2115c992ef55d187dcb1d4ca7b15"
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        
        # Algorithm: Extract and clean relevant product data
        products = []
        if "organic_results" in results:
            for item in results["organic_results"]:
                products.append({
                    "asin": item.get("asin"),
                    "title": item.get("title"),
                    "price": item.get("price"),
                    "rating": item.get("rating"),
                    "reviews": item.get("reviews"),
                    "thumbnail": item.get("thumbnail"),
                    "link": item.get("link"),
                    "description": item.get("snippet"),
                    "delivery": item.get("delivery")
                })
        return {"status": "SUCCESS", "data": products}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

def get_product_details(asin):
    """Fetches full product details from Amazon using SerpApi."""
    try:
        params = {
            "engine": "amazon_product",
            "asin": asin,
            "amazon_domain": "amazon.in",
            "api_key": "be8df5321312d370779b7d3e786b1f43e536fc92905ffd3f13b56cea6f58d1f6"
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        
        product = {
            "asin": results.get("asin"),
            "title": results.get("product_information", {}).get("product_name") or results.get("title"),
            "price": results.get("price"),
            "images": results.get("images"),
            "rating": results.get("rating"),
            "reviews": results.get("reviews"),
            "about": results.get("about_this_item") or results.get("feature_bullets"),
            "description": results.get("product_description"),
            "delivery": results.get("delivery_message"),
            "link": results.get("link")
        }
        
        # Filter out None values so we don't overwrite existing data (like delivery) from search results
        product = {k: v for k, v in product.items() if v is not None}
        
        return {"status": "SUCCESS", "data": product}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

def process_event(ch, method, properties, body):
    message = json.loads(body)
    event_type = message.get("eventType")
    data = message.get("data")
    
    print(f" [x] Received Event: {event_type}")

    if event_type == "USER_REGISTER":
        result = db.register_user(
            username=data['username'],
            email=data['email'],
            password=data['password']
        )
        print(f" [>] Register Result for {data['username']}: {result}")
        # Here you would typically publish a 'USER_REGISTERED' event back or update a status DB

    elif event_type == "USER_LOGIN":
        result = db.verify_user(
            username=data['username'],
            password=data['password']
        )
        
        if result.get('status') == 'SUCCESS':
            token = jwt.encode({
                'username': data['username'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, SECRET_KEY, algorithm="HS256")
            result['token'] = token

        print(f" [>] Login Result for {data['username']}: {result}")

    elif event_type == "FORGOT_PASSWORD":
        # Generate a 6-digit OTP
        otp = str(random.randint(100000, 999999))
        result = db.save_otp(data['email'], otp)
        
        if result.get('status') == 'SUCCESS':
            send_email(data['email'], otp)
        else:
            print(f" [!] Failed to generate OTP: {result.get('message')}")

    elif event_type == "RESET_PASSWORD":
        result = db.reset_password_with_otp(data['email'], data['otp'], data['new_password'])
        print(f" [>] Reset Password Result for {data['email']}: {result}")

    elif event_type == "SEARCH_PRODUCT":
        print(f" [SEARCH] Searching Amazon for: {data['keyword']}")
        amazon_res = search_amazon(data['keyword'])
        
        if amazon_res['status'] == 'ERROR':
            print(f" [!] Amazon Search Error: {amazon_res['message']}")

        results = []
        amaz_data = amazon_res.get('data', []) if amazon_res['status'] == 'SUCCESS' else []

        for item in amaz_data:
            item['source'] = 'Amazon'
            results.append(item)

        print(f" [>] Found {len(results)} combined products for '{data['keyword']}'")
        print(json.dumps(results, indent=4))
        if results:
            print(f"     Top Result: [{results[0].get('source')}] {results[0]['title']} - {results[0]['price']}")

        # Save results to a file so the API can read it
        request_id = data.get('requestId')
        if request_id:
            # Use the app root directory (parent of routes) to ensure both worker and API find the same path
            output_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            file_path = os.path.join(output_dir, f"search_results_{request_id}.json")
            with open(file_path, "w") as f:
                json.dump(results, f)
            print(f" [SAVED] Results saved to {file_path}")

    elif event_type == "GET_PRODUCT_DETAILS":
        print(f" [DETAILS] Getting details for ASIN: {data.get('asin')}")
        details_res = get_product_details(data.get('asin'))
        
        if details_res['status'] == 'ERROR':
            print(f" [!] Details Error: {details_res['message']}")
            
        result = details_res.get('data', {})

        # Save results to a file so the API can read it
        request_id = data.get('requestId')
        if request_id:
            output_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            file_path = os.path.join(output_dir, f"product_details_{request_id}.json")
            with open(file_path, "w") as f:
                json.dump(result, f)
            print(f" [SAVED] Details saved to {file_path}")

    elif event_type == "GET_BEST_DEALS":
        print(f" [DEALS] Finding best deals for: {data['keyword']}")
        amazon_res = search_amazon(data['keyword'])
        
        if amazon_res['status'] == 'ERROR':
            print(f" [!] Amazon Search Error: {amazon_res['message']}")

        all_products = []
        if amazon_res['status'] == 'SUCCESS':
            for p in amazon_res['data']:
                p['source'] = 'Amazon'
                all_products.append(p)

        # Calculate scores for sorting
        for p in all_products:
            p['parsed_price'] = parse_price(p.get('price'))
            p['parsed_rating'] = parse_rating(p.get('rating'))

        # Filter invalid prices and Sort: Price (Ascending) then Rating (Descending)
        valid_products = [p for p in all_products if p['parsed_price'] != float('inf')]
        sorted_products = sorted(valid_products, key=lambda x: (x['parsed_price'], -x['parsed_rating']))

        # Get top 5 products
        top_5 = sorted_products[:5]

        # Clean up temporary fields
        for p in top_5:
            p.pop('parsed_price', None)
            p.pop('parsed_rating', None)

        print(f" [>] Found {len(top_5)} best deals for '{data['keyword']}'")
        print(json.dumps(top_5, indent=4))

        # Save results to a file so the API can read it
        request_id = data.get('requestId')
        if request_id:
            # Use the app root directory (parent of routes) to ensure both worker and API find the same path
            output_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            file_path = os.path.join(output_dir, f"search_results_{request_id}.json")
            with open(file_path, "w") as f:
                json.dump(top_5, f)
            print(f" [SAVED] Best deals saved to {file_path}")

    else:
        print(f" [!] Unknown event type: {event_type}")

def start_worker():
    while True:
        try:
            rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbitmq_host)
            )
            break
        except pika.exceptions.AMQPConnectionError:
            print(" [!] RabbitMQ connection failed. Retrying in 5 seconds...")
            time.sleep(5)

    channel = connection.channel()

    # Connect to the same exchange as the publisher
    channel.exchange_declare(exchange='commerce.exchange', exchange_type='fanout')

    # Create a durable queue for this worker so messages persist if worker is offline
    queue_name = 'auth_queue'
    channel.queue_declare(queue=queue_name, durable=True)

    # Bind queue to exchange
    channel.queue_bind(exchange='commerce.exchange', queue=queue_name)

    print(' [*] Auth Worker waiting for messages. To exit press CTRL+C')

    channel.basic_consume(
        queue=queue_name, on_message_callback=process_event, auto_ack=True
    )
    channel.start_consuming()

if __name__ == "__main__":
    start_worker()