import json
import time
import random
from datetime import datetime
from confluent_kafka import Producer
from faker import Faker

fake = Faker('tr_TR')

PRODUCTS = {
    "Elektronik": ["Telefon", "Laptop", "Kulaklık", "Tablet", "Akıllı Saat"],
    "Giyim": ["Tişört", "Pantolon", "Ceket", "Gömlek", "Kazak"],
    "Market": ["Süt", "Ekmek", "Kahve", "Çikolata", "Meyve"],
    "Kozmetik": ["Parfüm", "Krem", "Şampuan", "Makyaj Seti", "Losyon"]
}

def create_event():
    category = random.choice(list(PRODUCTS.keys()))
    product = random.choice(PRODUCTS[category])
    
    return {
        "user_id": random.randint(10000, 99999),
        "product": product,
        "category": category,
        "location": fake.city(),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event_type": random.choices(["click", "view", "purchase"], weights=[70, 20, 10])[0]
    }

def delivery_report(err, msg):
    """Kafka gönderim sonucunu yakalayan callback fonksiyonu."""
    if err is not None:
        print(f"Mesaj ulaştırılamadı hatası: {err}")
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Event başarıyla Kafka'ya iletildi.")

def main():
    print("Producer başlatılıyor... Kafka'ya bağlanılıyor (localhost:9092)...")
    try:
        producer = Producer({
            'bootstrap.servers': 'localhost:9092'
        })
        print("Bağlantı başarılı! Veri gönderimi başlıyor...")
        
        while True:
            event = create_event()
            
            
            producer.produce(
                'user_events', 
                value=json.dumps(event).encode('utf-8'),
                callback=delivery_report
            )
            producer.poll(0)
            
            time.sleep(random.uniform(0.1, 1.0))
            
    except Exception as e:
        print(f"Hata oluştu: {e}")

if __name__ == "__main__":
    main()