import streamlit as st
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import pandas as pd
from datetime import datetime

# Konfigurasi halaman
st.set_page_config(page_title="GFS Sumatera Selatan Viewer", layout="wide")
st.title("📡 GFS Viewer – Sumatera Bagian Selatan Ekuator")
st.header("Visualisasi Prakiraan Cuaca: Jambi, Bengkulu, Sumsel, Lampung")

@st.cache_data
def load_dataset(run_date, run_hour):
    base_url = f"https://nomads.ncep.noaa.gov/dods/gfs_0p25_1hr/gfs{run_date}/gfs_0p25_1hr_{run_hour}z"
    ds = xr.open_dataset(base_url)
    return ds

# Sidebar: Input pengguna
st.sidebar.title("⚙️ Pengaturan")

today = datetime.utcnow()
run_date = st.sidebar.date_input("Tanggal Run GFS (UTC)", today.date())
run_hour = st.sidebar.selectbox("Jam Run GFS (UTC)", ["00", "06", "12", "18"])
forecast_hour = st.sidebar.slider("Jam ke depan", 0, 240, 0, step=1)

parameter = st.sidebar.selectbox("Parameter Cuaca", [
    "Curah Hujan per jam (pratesfc)",
    "Suhu Permukaan (tmp2m)",
    "Angin Permukaan (ugrd10m & vgrd10m)",
    "Tekanan Permukaan Laut (prmslmsl)"
])

if st.sidebar.button("🔎 Tampilkan Visualisasi"):
    try:
        ds = load_dataset(run_date.strftime("%Y%m%d"), run_hour)
        st.success("✅ Dataset berhasil dimuat.")
    except Exception as e:
        st.error(f"❌ Gagal memuat data: {e}")
        st.stop()

    is_contour = False
    is_vector = False

    if "pratesfc" in parameter and "pratesfc" in ds:
        var = ds["pratesfc"][forecast_hour, :, :] * 3600
        label = "Curah Hujan (mm/jam)"
        cmap = "Blues"
        vmin, vmax = 0, 50
    elif "tmp2m" in parameter and "tmp2m" in ds:
        var = ds["tmp2m"][forecast_hour, :, :] - 273.15
        label = "Suhu (°C)"
        cmap = "coolwarm"
        vmin, vmax = -5, 35
    elif "ugrd10m" in parameter and "ugrd10m" in ds and "vgrd10m" in ds:
        u = ds["ugrd10m"][forecast_hour, :, :]
        v = ds["vgrd10m"][forecast_hour, :, :]
        speed = ((u**2 + v**2)**0.5) * 1.94384  # knot
        var = speed
        label = "Kecepatan Angin (knot)"
        cmap = plt.cm.get_cmap("YlGnBu", 10)
        vmin, vmax = 0, 30
        is_vector = True
    elif "prmsl" in parameter and "prmslmsl" in ds:
        var = ds["prmslmsl"][forecast_hour, :, :] / 100
        label = "Tekanan Permukaan Laut (hPa)"
        cmap = "cool"
        vmin, vmax = 990, 1025
        is_contour = True
    else:
        st.warning("❗ Parameter tidak dikenali atau tidak tersedia.")
        st.stop()

    # 🔍 Filter wilayah: Sumatera Selatan Ekuator
    var = var.sel(lat=slice(-6.0, 0.5), lon=slice(101.0, 106.5))
    if is_vector:
        u = u.sel(lat=slice(-6.0, 0.5), lon=slice(101.0, 106.5))
        v = v.sel(lat=slice(-6.0, 0.5), lon=slice(101.0, 106.5))

    # 🎨 Buat figure
    fig = plt.figure(figsize=(10, 7))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent([101.0, 106.5, -6.0, 0.5], crs=ccrs.PlateCarree())

    # 🕒 Valid time
    valid_time = ds.time[forecast_hour].values
    valid_dt = pd.to_datetime(str(valid_time))
    valid_str = valid_dt.strftime("%HUTC %a %d %b %Y")
    tstr = f"t+{forecast_hour:03d}"

    ax.set_title(f"{label} Valid {valid_str}", loc="left", fontsize=10, fontweight="bold")
    ax.set_title(f"GFS {tstr}", loc="right", fontsize=10, fontweight="bold")

    # 🗺️ Grid dan fitur
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    gl.top_labels = gl.right_labels = False
    ax.coastlines(resolution='10m', linewidth=0.8)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.add_feature(cfeature.LAND, facecolor='lightgray')

    if is_contour:
        cs = ax.contour(var.lon, var.lat, var.values, levels=15, colors='black', linewidths=0.8, transform=ccrs.PlateCarree())
        ax.clabel(cs, fmt="%d", colors='black', fontsize=8)
    else:
        im = ax.pcolormesh(var.lon, var.lat, var.values, cmap=cmap, vmin=vmin, vmax=vmax, transform=ccrs.PlateCarree())
        cbar = plt.colorbar(im, ax=ax, orientation='vertical', pad=0.02)
        cbar.set_label(label)
        if is_vector:
            ax.quiver(var.lon[::5], var.lat[::5], u.values[::5, ::5], v.values[::5, ::5], transform=ccrs.PlateCarree(),
                      scale=700, width=0.002, color='black')

    # 📍 Marker lokasi kota & kabupaten
    locations = [
        # Jambi
        {"nama": "Kota Jambi", "lat": -1.6100, "lon": 103.6100},
        {"nama": "Muaro Jambi", "lat": -1.6102, "lon": 103.8826},
        {"nama": "Bungo", "lat": -1.3333, "lon": 101.8833},
        # Bengkulu
        {"nama": "Kota Bengkulu", "lat": -3.8004, "lon": 102.2655},
        {"nama": "Rejang Lebong", "lat": -3.4706, "lon": 102.5696},
        {"nama": "Seluma", "lat": -4.0371, "lon": 102.5271},
        # Sumatera Selatan
        {"nama": "Palembang", "lat": -2.9909, "lon": 104.7566},
        {"nama": "Lahat", "lat": -3.8000, "lon": 103.5333},
        {"nama": "Pagar Alam", "lat": -4.0214, "lon": 103.2454},
        {"nama": "OKU", "lat": -4.0261, "lon": 104.1661},
        {"nama": "PALI", "lat": -3.1780, "lon": 103.7444},
        # Lampung
        {"nama": "Bandar Lampung", "lat": -5.3971, "lon": 105.2668},
        {"nama": "Metro", "lat": -5.1135, "lon": 105.3068},
        {"nama": "Lampung Selatan", "lat": -5.5623, "lon": 105.5470}
    ]

    for loc in locations:
        ax.plot(loc["lon"], loc["lat"], marker='o', color='red', markersize=4,
                transform=ccrs.PlateCarree())
        ax.text(loc["lon"] + 0.1, loc["lat"] + 0.1, loc["nama"],
                fontsize=7, transform=ccrs.PlateCarree(), color='black',
                bbox=dict(facecolor='white', alpha=0.6, edgecolor='none'))

    # 🏛️ Label provinsi besar
    provinsi = [
        {"nama": "Jambi", "lat": -1.7, "lon": 103.7},
        {"nama": "Bengkulu", "lat": -3.9, "lon": 102.3},
        {"nama": "Sumatera Selatan", "lat": -3.1, "lon": 104.1},
        {"nama": "Lampung", "lat": -5.2, "lon": 105.2},
    ]
    for p in provinsi:
        ax.text(p["lon"], p["lat"], p["nama"], fontsize=11, fontweight='bold',
                transform=ccrs.PlateCarree(), color='blue')

    # Tampilkan ke Streamlit
    st.pyplot(fig)

    st.markdown(f"""
    **🕒 Valid Time:** {valid_str}  
    **📈 Forecast Hour:** {forecast_hour}  
    **📡 Data Source:** [NOAA NOMADS GFS 0.25°](https://nomads.ncep.noaa.gov)
    """)
