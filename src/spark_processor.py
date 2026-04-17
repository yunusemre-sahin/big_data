import os
import urllib.request
import platform

def setup_windows_hadoop():
    """Windows sistemlerde PySpark için gereken Hadoop (winutils) araçlarını otomatik kurar."""
    if platform.system() == "Windows":
        hadoop_home = os.path.join(os.getcwd(), "hadoop_env")
        bin_dir = os.path.join(hadoop_home, "bin")
        os.makedirs(bin_dir, exist_ok=True)
        
        winutils = os.path.join(bin_dir, "winutils.exe")
        hadoop_dll = os.path.join(bin_dir, "hadoop.dll")
        
        base_url = "https://raw.githubusercontent.com/cdarlint/winutils/master/hadoop-3.3.6/bin/"
        
        try:
            if not os.path.exists(winutils):
                print("Windows için winutils.exe indiriliyor... Lütfen bekleyin. (Sadece ilk çalışmada)")
                urllib.request.urlretrieve(base_url + "winutils.exe", winutils)
            if not os.path.exists(hadoop_dll):
                print("Windows için hadoop.dll indiriliyor...")
                urllib.request.urlretrieve(base_url + "hadoop.dll", hadoop_dll)
            
            os.environ["HADOOP_HOME"] = hadoop_home
            os.environ["PATH"] += os.pathsep + bin_dir
        except Exception as e:
            print(f"Hadoop indirme hatası, Spark local modda hata verebilir: {e}")

setup_windows_hadoop()

from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, window
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType

DB_URL = "jdbc:postgresql://localhost:5432/pipeline_db"
DB_PROPERTIES = {
    "user": "admin",
    "password": "adminpassword",
    "driver": "org.postgresql.Driver"
}

def write_to_postgres(df, epoch_id):
    """
    Mikro-batch verilerini PostgreSQL'e yazar.
    Her batch geldiğinde hesaplanan sonucu veritabanına ekleriz (append).
    """
    
    df.show(truncate=False)
    
    df_to_save = df.select(
        col("window.start").alias("window_start"),
        col("window.end").alias("window_end"),
        col("category"),
        col("click_count")
    )

    try:
        df_to_save.write.jdbc(
            url=DB_URL,
            table="category_clicks",
            mode="append",
            properties=DB_PROPERTIES
        )
    except Exception as e:
        print(f"PostgreSQL yazma hatası: {e}")

def main():
    import pyspark
    
    spark_version = pyspark.__version__
    scala_version = "2.13" if int(spark_version.split(".")[0]) >= 4 else "2.12"
    
    packages = (
        f"org.apache.spark:spark-sql-kafka-0-10_{scala_version}:{spark_version},"
        f"org.postgresql:postgresql:42.6.0"
    )

    spark = SparkSession.builder \
        .appName("KafkaStreamingToPostgres") \
        .config("spark.jars.packages", packages) \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    kafka_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "localhost:9092") \
        .option("subscribe", "user_events") \
        .option("startingOffsets", "latest") \
        .load()

    schema = StructType([
        StructField("user_id", IntegerType(), True),
        StructField("product", StringType(), True),
        StructField("category", StringType(), True),
        StructField("location", StringType(), True),
        StructField("timestamp", StringType(), True),
        StructField("event_type", StringType(), True)
    ])

    events_df = kafka_df.selectExpr("CAST(value AS STRING)") \
        .select(from_json(col("value"), schema).alias("data")) \
        .select("data.*") \
        .withColumn("timestamp", col("timestamp").cast("timestamp"))

    clicks_df = events_df.filter(col("event_type") == "click")

    windowed_clicks = clicks_df \
        .withWatermark("timestamp", "2 minutes") \
        .groupBy(
            window(col("timestamp"), "5 minutes"),
            col("category")
        ) \
        .count() \
        .withColumnRenamed("count", "click_count")

    query = windowed_clicks.writeStream \
        .outputMode("update") \
        .foreachBatch(write_to_postgres) \
        .trigger(processingTime="2 seconds") \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()
