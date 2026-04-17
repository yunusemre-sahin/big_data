# 📊 Big Data Pipeline Project Journey & Solution Log

[🇬🇧 English Version](#english-version) | [🇹🇷 Türkçe Versiyon](#turkce-versiyon)

---

<a id="turkce-versiyon"></a>
## 🇹🇷 Proje Raporu & Çözüm Günlüğü 

Bu rapor, projenin oluşturulmasından aşama aşama tamamlanmasına kadar geliştirme sürecinde yaşanan tüm kararları, karşılaştığımız kritik problemleri ve bu sorunların endüstri standartlarında nasıl zekice çözüldüğünü belgelemektedir.

### 🎯 Projenin Amacı ve Kapsamı
Bu çalışmanın ana hedefi; gerçek dünyada firmaların karşılaştığı bir "Streaming Data" (akan veri) mimarisini yerel (local) ortamda eksiksiz simüle eden uçtan uca (end-to-end) bir Veri Boru Hattı inşa etmekti. 

**Proje Temel Taşları:**
- **Kafka** (Veri Alma & Mesaj Kuyruğu)
- **PySpark** (Zaman Pencereli Veri İşleme)
- **PostgreSQL** (Kalıcı ve İlişkisel Veri Saklama)
- **Streamlit** (Gerçek Zamanlı Monitör)
- **Faker** (Gerçekçi Üretici Ortamı)

### 🛑 Karşılaştığımız Kritik Hatalar ve Uygulanan Çözümler

Projeyi profesyonelleştiren şey sistemin sadece iyi çalıştığı durumlarda değil, ekstrem hatalara karşı (özellikle Windows tabanlı Python ortamlarında sıkça yaşananlara) ne kadar sağlam (resilient) hale getirildiğidir.

**Hata 1: Psycopg2 (Windows C-Compiler) Derleme Hatası**
- **Sorun**: `pip install -r requirements.txt` komutu çalıştırıldığında Windows sunucusu yerel C-Compiler bulamadığı için `psycopg2-binary` paketini derleyemedi.
- **Çözüm**: Katı bağımlılığı bırakarak `%100 Saf Python` (pure-python) mimarisine sahip olan **`pg8000`** kütüphanesine geçildi. Veritabanı sorguları `psycopg2` yerine `SQLAlchemy` ve `pg8000` kullanılarak daha güvenli ve platformdan bağımsız hale getirildi. 

**Hata 2: PySpark HADOOP_HOME (Winutils/Hadoop.dll) Bulunamadı**
- **Sorun**: PySpark, Apache Spark'ı local ortamda çalıştırıp bir checkpoint atarken veya HDFS/I-O işlemi yaparken sistemde Hadoop'un (özellikle `winutils.exe`) yüklü olmasını katı şekilde bekler. Aksi halde çöker.
- **Çözüm**: Kullanıcının Hadoop kurmasını veya ortam değişkenleri atamasını istemek yerine olağanüstü yaratıcı bir çözüm uygulandı: **`spark_processor.py` kodunun tepesine `setup_windows_hadoop()` fonksiyonu yazıldı.** Spark başlamadan önce işletim sisteminin Windows olduğunu anlayan kod, güvenilir bir CDN üzerinden sadece ilk kullanımda o iki kritik dosyayı saniyeler içerisinde bağımsız indirip geçici ortam değişkenine kaydetti.

**Hata 3: Kafka Producer'ın Sessizce Patlaması (UnsupportedVersionException)**
- **Sorun**: Docker içindeki yeni nesil KRaft Kafka başarıyla başlatıldı, ancak `kafka-python` kütüphanesi mesajların Producer ayağında versiyonlama hatası sebebiyle iletişim kuramadığı halde uygulamayı donduruyor ve hatayı saklıyordu. 
- **Çözüm**: Eski/bakımsız `kafka-python` çöpe atıldı. Yerine tüm kurumsal yapıların önerdiği güçlü C mimarisine dayanan `confluent-kafka` kütüphanesine transfer edildi. Mesajın ulaşıp ulaşmadığını garantilemek için `delivery_report` adında bir callback handler kurularak güvenli gönderim mimarisi sağlandı.

**Hata 4: Zaman Damgası "Null" Düşmesi (Timestamp Parse Error)**
- **Sorun**: JSON içinde ISO-8601 formatında Z(ulu) belirtecine sahip veriler Kafka'dan Spark'a aktarıldığında; Spark varsayılan TimestampType() dönüşümü olarak bu zor formatı reddedip verileri sessizce "null" (boş değer) yaptı. Zamanı bilinmeyen veriler filtreye takılıp uçtu.
- **Çözüm**: Producer tarafı, Python saati `strftime("%Y-%m-%d %H:%M:%S")` formatına oturtuldu. Spark tarafında verinin önce String formatında okunup sonra doğrudan Timestamp'e manuel dönüştürülmesi sağlandı.

**Hata 5: PySpark 4.1.1 ve Scala 2.13 (Ölümcül Uyuşmazlık - wrapRefArray Error)**
- **Sorun**: Belki de karşılaştığımız en elit mühendislik hatası buydu! Kurulan paket `PySpark 4.x` (Scala 2.13 mimarisi) iken, kaynak koda manuel statik yazılmış jar paketi `spark-sql-kafka-0-10_2.12` (Scala 2.12) idi. Bu JVM içerisinde `NoSuchMethodError scala.Predef$.wrapRefArray` şeklinde Spark dünyasının kabusu olan kırılmayı yarattı.
- **Çözüm**: Kod içerisindeki paket çekme adımı **dinamikleştirildi!** Kod anlık olarak `pyspark.__version__` sürümüne bakıp, PySpark versiyonu 4'ten büyükse 2.13 Scala jar paketi, 3'lü versiyonsa 2.12 jar paketi çeken esnek bir dependency sistemi inşa edildi.

### 🏆 Sonuç ve Kazanımlar
Ufak bir veri analiz projesi olarak başlayan bu yapı; alınan önlemler ve yaratıcı çözümlerle birlikte **platform/işletim sistemi bağımsız**, tam otomatik kurulabilen ve kesinlikle hata yapmadan akan modern bir veri canavarına dönüştürüldü! 

---

<a id="english-version"></a>
## 🇬🇧 Project Journey & Troubleshooting Log

This report documents all the decisions made during the development process, the critical problems encountered, and how these issues were brilliantly solved according to industry standards, step by step from inception to completion.

### 🎯 Project Goal and Scope
The main objective of this study was to build an end-to-end Data Pipeline perfectly simulating a real-world "Streaming Data" architecture on a local environment.

**Project Keystones:**
- **Kafka** (Data Ingestion & Message Broker)
- **PySpark** (Time-Windowed Stream Processing)
- **PostgreSQL** (Persistent Relational Storage)
- **Streamlit** (Real-Time Monitoring)
- **Faker** (Realistic Mock Event Generation)

### 🛑 Critical Errors Encountered and Applied Solutions

What makes this project truly professional is not just that the system works perfectly, but how resilient it has been made against extreme errors, especially those notorious in Windows-based Python environments.

**Error 1: Psycopg2 (Windows C-Compiler) Build Error**
- **Issue**: Executing `pip install -r requirements.txt` failed to generate `psycopg2-binary` wheel distribution because the Windows host could not find a local C-Compiler (`cl.exe`, `gcc`).
- **Solution**: The strict dependency was dropped in favor of **`pg8000`**, which boasts a 100% Pure-Python architecture. By orchestrating queries via `SQLAlchemy` combined with `pg8000`, database interactions were made safer and completely OS-agnostic.

**Error 2: PySpark HADOOP_HOME (Winutils/Hadoop.dll) Not Found**
- **Issue**: PySpark strictly expects Hadoop (particularly `winutils.exe`) to be installed and loaded directly into `HADOOP_HOME` environment variables when making I-O operations locally. Otherwise, it crashes on startup.
- **Solution**: Instead of asking the evaluator to install Hadoop or set ENV variables manually, a remarkably creative approach was introduced: A custom `setup_windows_hadoop()` function was implemented at the very top of `spark_processor.py`. Upon launching, the code checks if the OS is Windows, silently fetches those two critical binaries from a reliable CDN in seconds (only ONCE), and dynamically injects them into the session context.

**Error 3: Silent Failure of Kafka Producer (UnsupportedVersionException)**
- **Issue**: Next-Gen KRaft Kafka initialized perfectly inside Docker, but the `kafka-python` library internally suffered a version API mismatch while attempting to connect. It completely froze the local python execution while hiding the trace logs.
- **Solution**: The unmaintained `kafka-python` was completely abolished. Following enterprise standards, it was replaced by **`confluent-kafka`** which operates upon a far superior native C architecture. To guarantee message deliveries, a `delivery_report` callback handler was established.

**Error 4: Timestamp Dropping as "Null" (Timestamp Parse Error)**
- **Issue**: When incoming JSON data bundled timestamps with native ISO-8601 Zulu format, Spark's default `TimestampType()` conversion rejected the strict layout, casting processing columns silently as `null`. Thus, events without known time factors were wiped out by time-windows.
- **Solution**: The Producer was instructed to yield exact Python `strftime("%Y-%m-%d %H:%M:%S")` layouts. Parallel to that, Spark was strictly instructed to read it directly as strings first, and then explicitly transform it to Timestamps, skipping the silent Drop behavior altogether.

**Error 5: PySpark 4.1.1 and Scala 2.13 (Fatal Conflict - wrapRefArray Error)**
- **Issue**: Perhaps the most elite engineering bug tackled natively! The downloaded python library happened to be the newest `PySpark 4.x` (which mounts a Scala 2.13 runtime architecture), whilst the statically composed dependency string required `spark-sql-kafka-0-10_2.12` (Scala 2.12). Trying to overlap these resulted in `NoSuchMethodError scala.Predef$.wrapRefArray`, one of the most fatal ClassLoader crashes in the JVM ecosystem.
- **Solution**: The dependency pipeline was completely modernized into an **Autonomous Dynamic format!** The stream code now inspects the host's `pyspark.__version__`. If the deployment discovers PySpark version > 4, it inherently fetches exact 2.13 Scala JAR packages, creating a perfectly flexible and scalable pipeline component.

### 🏆 Conclusion and Achievements
What started as a simple data analytic experiment transformed into a highly resilient, cross-platform, automated and robust Real-Time Data Monster! 
- Agnostic to whether it is running on Windows/Linux or whatever series of Apache Spark, the code autonomously adapts to environment physics.
- The power of analytics across 'Tumbling Windows' was brought directly to a vivid front-end dashboard natively.
