import requests
import re
import json

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
    
    # 1. Buscar patrón específico que encontraste: "src":"https:\u002F...
    patron_json = re.compile(r'"src":"(https?:\\u002F\\u002F[^"]+\.m3u8[^"]*)"', re.IGNORECASE)
    coincidencias = patron_json.findall(html)
    
    print(f"📡 Buscando URLs con patrón \\u002F...")
    for url_escapada in coincidencias:
        url_limpia = limpiar_url(url_escapada)
        
        # Intentar extraer el nombre de la emisora del contexto cercano
        nombre = "Radio Puerto Rico"
        
        # Buscar el nombre de la emisora en líneas cercanas a la URL
        # Buscar patrones como "title":"Nombre de la radio"
        patron_nombre = re.compile(r'"title":"([^"]+)"[^}]*"src":"' + re.escape(url_escapada), re.IGNORECASE)
        match_nombre = patron_nombre.search(html)
        if match_nombre:
            nombre = match_nombre.group(1)
        
        streams_encontrados.append((nombre, url_limpia))
        print(f"  ✓ Encontrada: {nombre}")
        print(f"    URL: {url_limpia[:100]}...")
    
    # 2. Búsqueda alternativa: buscar cualquier m3u8 en el HTML
    patron_m3u8 = re.compile(r'(https?:[^"\']+\.m3u8[^"\']*)', re.IGNORECASE)
    todas_m3u8 = patron_m3u8.findall(html)
    
    for url_raw in todas_m3u8:
        url_limpia = limpiar_url(url_raw)
        if url_limpia not in [u[1] for u in streams_encontrados]:
            streams_encontrados.append(("Radio detectada", url_limpia))
            print(f"  ✓ Encontrada (método alternativo): {url_limpia[:100]}...")
    
    # 3. Si no encontró nada, buscar dentro de scripts específicos
    if not streams_encontrados:
        print("🔍 Buscando dentro de scripts...")
        # Buscar cualquier script que contenga "BroadcastPreview"
        patron_script = re.compile(r'<script[^>]*>([^<]+)</script>', re.DOTALL)
        scripts = patron_script.findall(html)
        
        for script in scripts:
            if 'BroadcastPreview' in script or 'm3u8' in script:
                # Extraer todas las URLs m3u8 dentro del script
                urls = re.findall(r'(https?:\\u002F\\u002F[^"\'\\]+\.m3u8[^"\'\\]*)', script)
                for url_escapada in urls:
                    url_limpia = limpiar_url(url_escapada)
                    streams_encontrados.append(("Radio encontrada", url_limpia))
                    print(f"  ✓ Encontrada en script: {url_limpia[:100]}...")
    
    # Eliminar duplicados
    unicos = []
    vistos = set()
    for nombre, url in streams_encontrados:
        if url not in vistos:
            vistos.add(url)
            unicos.append((nombre, url))
    
    return unicos

def crear_m3u(lista_streams):
    if not lista_streams:
        print("\n❌ No se encontraron streams.")
        print("\n💡 Sugerencia manual:")
        print("   1. Abre la página web")
        print("   2. Presiona F12 → pestaña Network (Red)")
        print("   3. Haz clic en una radio que suene")
        print("   4. Busca archivos .m3u8 y copia la URL")
        print("   5. Crea manualmente el archivo M3U")
        
        # Crear archivo con instrucciones
        with open('radios_pr.m3u', 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
            f.write('#EXTINF:-1,EJEMPLO - Reemplazar con URL real\n')
            f.write('# Las URLs deben tener formato normal (barras /, no \\u002F)\n')
        return
    
    with open('radios_pr.m3u', 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        for nombre, url in lista_streams:
            f.write(f'#EXTINF:-1,{nombre}\n')
            f.write(f'{url}\n')
    
    print(f"\n✅ ¡Éxito! Se creó 'radios_pr.m3u' con {len(lista_streams)} streams.")
    print("\n📻 Lista de streams encontrados:")
    for i, (nombre, url) in enumerate(lista_streams[:10]):  # Mostrar primeros 10
        print(f"  {i+1}. {nombre}")
        print(f"     {url[:80]}...")

if __name__ == "__main__":
    print("=" * 60)
    print("📻 Scraper de Emisoras de Puerto Rico - v2")
    print("=" * 60)
    streams = extraer_streams_del_html()
    crear_m3u(streams)
