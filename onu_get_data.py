import time
import csv
import os
import requests
from datetime import datetime, timedelta
import pytz # Librería para zonas horarias
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURACIÓN ---
URL_BASE = os.getenv("ROUTER_URL", "tu_url_router")  # URL del router, p.ej. http://
USER = os.getenv("ROUTER_USER", "tu_usuario")
PASS = os.getenv("ROUTER_PASS", "tu_pass")
URL_API = os.getenv("URL_API", "tu_url_api")
API_KEY = os.getenv("API_KEY", "tu_api_key")
ZONA_HORARIA = pytz.timezone("Europe/Madrid") # Madrid, París, Roma...

def get_full_stats():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-pipe")
    
    service = Service(executable_path="/usr/bin/chromedriver")
    driver = None
    # service = Service(executable_path="/usr/bin/chromedriver")
    # driver = webdriver.Chrome(service=service, options=options)
    
    # Obtener hora actual en la zona horaria configurada
    ahora = datetime.now(ZONA_HORARIA)
    data = {
        "Fecha": ahora.strftime('%Y-%m-%d %H:%M:%S'), "Model": "N/A", "SN": "N/A",
        "State": "N/A", "Rx": "0", "Tx": "0", "Volt": "0", "Bias": "0", "Temp": "0"
    }

    try:
        print(f"\n[{data['Fecha']}] Iniciando consulta programada...")
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 15)

        # 1. LOGIN
        driver.get(URL_BASE)
        wait.until(EC.presence_of_element_located((By.ID, "Frm_Username"))).send_keys(USER)
        driver.find_element(By.ID, "Frm_Password").send_keys(PASS)
        driver.execute_script("document.getElementById('LoginId').click();")
        
        # 2. NAVEGACIÓN (Ajustada a lo que nos funcionó)
        time.sleep(5)
        driver.switch_to.default_content()
        driver.execute_script("AjaxPageGet('/?_type=menuView&_tag=ponopticalinfo', '1');")
        time.sleep(5) 

        # 3. EXTRACCIÓN
        ids_router = {
            "State": "RegStatus", "Rx": "RxPower", "Tx": "TxPower", 
            "Volt": "Volt", "Bias": "Current", "Temp": "Temp"
        }

        found = False
        for ctx in ["main", 0, 1]:
            try:
                driver.switch_to.default_content()
                if ctx != "main": driver.switch_to.frame(ctx)
                
                rx_val = driver.find_element(By.ID, "RxPower").text or driver.find_element(By.ID, "RxPower").get_attribute("value")
                if rx_val:
                    for key, id_html in ids_router.items():
                        try:
                            el = driver.find_element(By.ID, id_html)
                            val = el.text or el.get_attribute("value") or "0"
                            data[key] = val.replace("dBm","").replace("mV","").replace("mA","").replace("°C","").strip()
                        except: pass
                    found = True
                    break
            except: continue


        # ids_device = {
        #     "Model": "ModelName",
        #     "SN": "SerialNumber"
        # }

        # print("   Navegando a Management & Diagnosis para Modelo y SN...")
        # Usamos el ID que encontraste: mgrAndDiag
        btn_diag = wait.until(EC.element_to_be_clickable((By.ID, "mgrAndDiag")))
        driver.execute_script("arguments[0].click();", btn_diag)
        
        # Forzamos la carga de la página de estado del sistema (statusMgr)
        driver.execute_script("AjaxPageGet('/?_type=menuView&_tag=statusMgr', '1');")
        time.sleep(5)

        # Extraemos Modelo y SN
        for ctx in ["main", 0, 1]:
            try:
                driver.switch_to.default_content()
                if ctx != "main": driver.switch_to.frame(ctx)
                
                # Buscamos por los IDs que me pasaste
                model_el = driver.find_element(By.ID, "ModelName")
                sn_el = driver.find_element(By.ID, "SerialNumber")
                
                # Usamos .get_attribute("title") porque en tu HTML el dato real está ahí
                data["Model"] = model_el.get_attribute("title") or model_el.text
                data["SN"] = sn_el.get_attribute("title") or sn_el.text
                # print(f"   Identificado: {data['Model']} - {data['SN']}")
                break
            except: continue

        return data if found else None

    except Exception as e:
        print(f"Error: {str(e)[:50]}")
        return None
    finally:
        if driver: driver.quit()

def esperar_hasta_proximo_intervalo(minutos=15):
    """Calcula el tiempo de espera hasta el próximo múltiplo de 'minutos'"""
    ahora = datetime.now(ZONA_HORARIA)
    
    # Calcular cuántos minutos faltan para el próximo múltiplo
    minutos_restantes = minutos - (ahora.minute % minutos)
    proxima_ejecucion = ahora.replace(second=0, microsecond=0) + timedelta(minutes=minutos_restantes)
    
    espera = (proxima_ejecucion - ahora).total_seconds()
    
    # Si la espera es muy corta (p.ej. 1s), saltar al siguiente para evitar bucles infinitos
    if espera < 10:
        proxima_ejecucion += timedelta(minutes=minutos)
        espera = (proxima_ejecucion - ahora).total_seconds()
        
    print(f"Próxima ejecución programada para: {proxima_ejecucion.strftime('%H:%M:%S')}")
    time.sleep(espera)

def enviar_a_cloud(datos):
    
    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(URL_API, json=datos, headers=headers, timeout=10)
        if response.status_code == 201:
            print("   Enviado al cloud correctamente (Protegido).")
        elif response.status_code == 403:
            print("   Error: API KEY rechazada por el servidor.")
        else:
            print(f"   Error en cloud: {response.status_code}")
    except Exception as e:
        print(f"   Fallo al conectar con el cloud: {e}")

if __name__ == "__main__":
    print(f"Monitor iniciado. Sincronizando con zona horaria: {ZONA_HORARIA}")
    while True:
        # Primero esperamos al siguiente múltiplo de 15 (14:00, 14:15...)
        esperar_hasta_proximo_intervalo(15)
        
        # Ejecutamos el script
        res = get_full_stats()

        if res:
            enviar_a_cloud(res)
            print(f"OK: Datos subidos a 'corucosmos.com' a las {res['Fecha']}")
        else:
            print("Error: No se pudieron obtener datos en este intervalo.")
        
        # if res:
        #     csv_path = "/app/data/log_onu.csv"
        #     file_exists = os.path.isfile(csv_path)
        #     with open(csv_path, "a", newline='') as f:
        #         writer = csv.DictWriter(f, fieldnames=res.keys())
        #         if not file_exists: writer.writeheader()
        #         writer.writerow(res)
        #     print(f"OK: Datos guardados a las {res['Fecha']}")