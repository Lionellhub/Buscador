import requests
import re
import os

URL = "https://es.cam4.com/?page=2"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def limpiar_url(url):
    """Convierte \\u002F en / y otros caracteres escapados"""
    if not url:
        return url
    url = url.replace('\\u002F', '/')
    url = url.replace('\\u003A', ':')
    url = url.replace('\\u003D', '=')
    url = url.replace('\\u0026', '&')
    url = url.replace('\\u003F', '?')
    return url

def extraer_streams_del_html():
    print(f"🔍 Analizando {URL}...")
    respuesta = requests.get(URL, headers=headers)
    
    if respuesta.status_code != 200:
        print(f"❌ Error: Código {respuesta.status_code}")
        return []
    
    html = respuesta.text
    streams_encontrados = []
    
    # 1. Buscar patrón específico: "src":"https:\u002F...
    patron_json = re.compile(r'"src":"(https?:\\u002F\\u002F[^"]+\.m3u8[^"]*)"', re.IGNORECASE)
    coincidencias = patron_json.findall(html)
    
    print(f"📡 Buscando URLs con patrón \\u002F...")
    for url_escapada in coincidencias:
        url_limpia = limpiar_url(url_escapada)
        
        nombre = "Radio Puerto Rico"
        
        patron_nombre = re.compile(r'"username":"([^"]+)"[^}]*"src":"' + re.escape(url_escapada), re.IGNORECASE)
        match_nombre = patron_nombre.search(html)
        if match_nombre:
            nombre = match_nombre.group(1)
        
        streams_encontrados.append((nombre, url_limpia))
        print(f"  ✓ Encontrada: {nombre}")
    
    # 2. Búsqueda alternativa
    patron_m3u8 = re.compile(r'(https?:[^"\']+\.m3u8[^"\']*)', re.IGNORECASE)
    todas_m3u8 = patron_m3u8.findall(html)
    
    for url_raw in todas_m3u8:
        url_limpia = limpiar_url(url_raw)
        if url_limpia not in [u[1] for u in streams_encontrados]:
            streams_encontrados.append(("Radio detectada", url_limpia))
            print(f"  ✓ Encontrada (alternativo)")
    
    # 3. Buscar dentro de scripts si no encontró nada
    if not streams_encontrados:
        print("🔍 Buscando dentro de scripts...")
        patron_script = re.compile(r'<script[^>]*>([^<]+)</script>', re.DOTALL)
        scripts = patron_script.findall(html)
        
        for script in scripts:
            if 'BroadcastPreview' in script or 'm3u8' in script:
                urls = re.findall(r'(https?:\\u002F\\u002F[^"\'\\]+\.m3u8[^"\'\\]*)', script)
                for url_escapada in urls:
                    url_limpia = limpiar_url(url_escapada)
                    streams_encontrados.append(("Radio encontrada", url_limpia))
                    print(f"  ✓ Encontrada en script")
    
    # Eliminar duplicados
    unicos = []
    vistos = set()
    for nombre, url in streams_encontrados:
        if url not in vistos:
            vistos.add(url)
            unicos.append((nombre, url))
    
    return unicos

def crear_m3u(lista_streams):
    archivo_final = 'radios_pr.m3u'
    archivo_temp = 'radios_pr_temp.m3u'

    if not lista_streams:
        print("\n⚠️ No se encontraron streams.")
        print("🛑 Se mantiene el archivo anterior (no se sobrescribe).")
        return

    # (Opcional) Seguridad extra: mínimo de streams
    if len(lista_streams) < 3:
        print("⚠️ Muy pocos streams encontrados. Posible error.")
        print("🛑 No se reemplaza el archivo anterior.")
        return

    # Crear archivo temporal
    with open(archivo_temp, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        for nombre, url in lista_streams:
            f.write(f'#EXTINF:-1,{nombre}\n')
            f.write(f'{url}\n')
    
    # Validar que el archivo no esté vacío
    if os.path.exists(archivo_temp) and os.path.getsize(archivo_temp) > 20:
        os.replace(archivo_temp, archivo_final)
        print(f"\n✅ Archivo actualizado con {len(lista_streams)} streams.")
    else:
        print("⚠️ Archivo vacío. No se reemplaza el anterior.")
        if os.path.exists(archivo_temp):
            os.remove(archivo_temp)

if __name__ == "__main__":
    print("=" * 60)
    print("📻 Scraper de Emisoras de Puerto Rico - v3")
    print("=" * 60)
    
    streams = extraer_streams_del_html()
    crear_m3u(streams)
