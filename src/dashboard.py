import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import time
import altair as alt

st.set_page_config(
    page_title="Gerçek Zamanlı Veri Akışı",
    page_icon="⚡",
    layout="wide"
)

DB_HOST = "localhost"
DB_NAME = "pipeline_db"
DB_USER = "admin"
DB_PASS = "adminpassword"
DB_PORT = "5432"

@st.cache_resource
def init_connection():
    """Veritabanı bağlantısı oluşturur ve önbelleğe (cache) alır."""

    engine_url = f"postgresql+pg8000://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(engine_url)

def get_data():

    try:
        engine = init_connection()
        query = """
            -- En son (maksimum) pencere başlangıç zamanını bulalım
            WITH LatestWindow AS (
                SELECT MAX(window_start) as latest_start 
                FROM category_clicks
            )
            -- Şimdi o zaman dilimine ait olan en güncel kayıtları getirelim
            -- Spark resultları append ettiği için, birden fazla aynı batch olabilir
            -- O yüzden max(click_count) ile tekilleştirebiliriz.
            SELECT 
                c.category, 
                MAX(c.click_count) as click_count,
                c.window_start
            FROM category_clicks c
            JOIN LatestWindow l ON c.window_start = l.latest_start
            GROUP BY c.category, c.window_start
            ORDER BY click_count DESC;
        """
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        
        return pd.DataFrame(columns=['category', 'click_count', 'window_start'])


st.title("⚡ Streaming Dashboard: Son 5 Dakika")
st.markdown("Apache Kafka ve PySpark kullanılarak canlı akan veri, anlık işlenip PostgreSQL'e yazdırılıyor. "
            "Aşağıdaki grafik en son **5 dakikalık penceredeki** en çok tıklanan kategorileri göstermektedir.")

placeholder = st.empty()

while True:
    df = get_data()
    
    with placeholder.container():
        if df.empty:
            st.warning("Veriler henüz gelmedi... Kafka producer ve Spark processor'un çalıştığından emin olun.")
        else:
            latest_time = pd.to_datetime(df['window_start'].iloc[0]).strftime("%H:%M:%S")
            st.info(f"Son Güncelleme Penceresi: **{latest_time}** (Her 3 saniyede 1 güncellenir)")
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.subheader("Tablo Görünümü")
                st.dataframe(
                    df[['category', 'click_count']],
                    column_config={
                        "category": "Kategori",
                        "click_count": "Tıklanma Sayısı"
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                
                top_category = df.iloc[0]['category']
                top_clicks = df.iloc[0]['click_count']
                st.metric(label="🏆 En Popüler Kategori", value=top_category, delta=f"{top_clicks} Tık")
                
            with col2:
                st.subheader("Görselleştirme")
                
                chart = alt.Chart(df).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
                    x=alt.X('category', sort='-y', title='Kategori'),
                    y=alt.Y('click_count', title='Tıklanma Sayısı'),
                    color=alt.Color('category', legend=None, scale=alt.Scale(scheme='set2')),
                    tooltip=['category', 'click_count']
                ).properties(
                    height=350
                ).configure_axis(
                    labelFontSize=12,
                    titleFontSize=14
                )
                st.altair_chart(chart, use_container_width=True)

    
    time.sleep(3)
