from time import sleep
from typing import KeysView
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
import casesListas as CL
from datetime import datetime
import psycopg2
import crdncls as cr
import requests
import random
import logging
import payLoads as pl
from selenium.common.exceptions import NoSuchElementException 

# CONFIGURACION DE LOS LOGGINGS
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - Proceso: %(process)s - %(levelname)s - %(message)s')
handler = logging.FileHandler('logAutomatizadorSelenium.log')
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter('%(asctime)s|%(process)s|%(levelname)s|%(message)s'))
logging.getLogger('').addHandler(handler)


# MANEJO DE INSTANCIA
instancia = "instancia2"

# TOKEN
def token():
    heads = cr.token()
    head = {'Authorization': 'Bearer {}'.format(heads)}
    return head

# CONEXIONES A BASE DE DATOS
def traerCredito(identificacion):
    try:
        conexcion = psycopg2.connect(user=cr.user, password=cr.password,
                                    host=cr.host,
                                    port=cr.port, database=cr.database)
        cursor = conexcion.cursor()
        cursor.execute(f"select cr.id  from credito cr inner join cliente cl on cl.id = cr.id_cliente where cl.identificacion = '{identificacion}' order by cr.id  desc limit 1;")
        credito =cursor.fetchall()
    finally:
        cursor.close()
        conexcion.close()
        return credito[0][0]

def whoIsWho(idCredito):
    try:
        conexcion = psycopg2.connect(user=cr.user, password=cr.password, 
                                    host=cr.host, 
                                    port=cr.port, database=cr.database) 
        cursor = conexcion.cursor()
        cursor.execute(f"update proveedor_autovalidacion  set num_intentos = 5  where id_credito = {idCredito};")
        conexcion.commit()
    finally:
        cursor.close()
        conexcion.close()

def enlaceVariable(idCredito):
    try:
        conexcion = psycopg2.connect(user=cr.user, password=cr.password, 
                                    host=cr.host, 
                                    port=cr.port, database=cr.database) 
        cursor = conexcion.cursor()
        cursor.execute(f"select id from enlacevariable e where id_credito = {idCredito};")
        enlaceVariable =cursor.fetchall()
    finally:
        cursor.close()
        conexcion.close()
        return enlaceVariable[0][0]

def otp(idCliente):
    try:
        conexcion = psycopg2.connect(user=cr.user, password=cr.password, 
                                    host=cr.hostApp, 
                                   port=cr.port, database=cr.tokens) 
        cursor = conexcion.cursor()
        cursor.execute(f"select token from otp c where id_cliente = {idCliente} order by fecha_creacion desc limit 1;")
        otp =cursor.fetchall()
    finally:
        cursor.close()
        conexcion.close()
        return otp[0][0]

def cambioEstado(identificacion):
    try:
        print(identificacion)
        conexcion = psycopg2.connect(user=cr.user, password=cr.password, 
                                    host=cr.host, 
                                    port=cr.port, database=cr.database) 
        cursor = conexcion.cursor()
        cursor.execute(f"update credito set estado = 'CANCELADO_POR_INCONSISTENCIAS' where id in (select c.id from credito c inner join cliente c2 on c2.id = c.id_cliente where c2.identificacion = '{identificacion}' and c.estado in ('PENDIENTE_RADICACION','FINALIZADO_FIRMA_DOCUMENTOS', 'FINALIZADO_GENERAR_DOCUMENTO_SEGURO_VIDA','EN_ESPERA_GENERAR_DOCUMENTO_SEGURO_VIDA','FINALIZADO_GENERAR_DOCUMENTO_AUT_DESEMBOLSO','EN_ESPERA_GENERAR_DOCUMENTO_AUT_DESEMBOLSO','FINALIZADO_GENERAR_DOCUMENTO_PERSONA_EXPUESTA','EN_ESPERA_GENERAR_DOCUMENTO_PERSONA_EXPUESTA','FINALIZADO_GENERAR_DOCUMENTO_SOLICITUD_CREDIT','EN_ESPERA_GENERAR_DOCUMENTO_SOLICITUD_CREDIT','FINALIZADO_GENERAR_DOCUMENTO_FIANZA','EN_ESPERA_GENERAR_DOCUMENTO_FIANZA','FINALIZADO_GENERAR_DOCUMENTO_DEBITO_BANCARIO','EN_ESPERA_GENERAR_DOCUMENTO_DEBITO_BANCARIO','EN_ESPERA_GENERAR_DOCUMENTO_SOLICITUD_CREDIT','FINALIZADO_GENERAR_DOCUMENTO_FIANZA','EN_ESPERA_GENERAR_DOCUMENTO_FIANZA','FINALIZADO_GENERAR_DOCUMENTO_DEBITO_BANCARIO','EN_ESPERA_GENERAR_DOCUMENTO_DEBITO_BANCARIO','EN_ESPERA_FIRMA_DOCUMENTOS','EN_REGISTRO_OPERACIONES_INTERNACIONALES','EN_REGISTRO_SEGURO_VIDA','EN_REGISTRO_REFERENCIAS','EN_DECISION_SEGURO_AP','EN_ESPERA_EXCEPCIONES','EN_SIMULACION_FINAL_ASESOR','EN_REGISTRO_DATOS_ADICIONALES_CLIENTE','EN_SELECCION_MEDIO_DESEMBOLSO','CALCULO_ENDEUDAMIENTO_EJECUTADO','EN_PROCESO_CALCULO_ENDEUDAMIENTO','PROSPECCION_EXITOSA','PENDIENTE_PROSPECCION','FINALIZADO_GENERAR_DOCUMENTO_HABEAS_DATA','EN_ESPERA_GENERAR_DOCUMENTO_HABEAS_DATA','EN_ESPERA_AUTORIZACION_OTP','INICIADO_DIGICREDITO'))")
        conexcion.commit()
    finally:
        cursor.close()
        conexcion.close()

def idSimulacion(idCredito):
    try:
        conexcion = psycopg2.connect(user=cr.user, password=cr.password, 
                                    host=cr.hostApp, 
                                    port=cr.port, database=cr.tokens) 
        cursor = conexcion.cursor()
        cursor.execute(f"select id from simulacion s where id_credito = {idCredito} order by id desc  ;")
        otp =cursor.fetchall()
    finally:
        cursor.close()
        conexcion.close()
        return otp[0][0]



# ENDPOINTS
def traerCliente(id, head):
    try:
        url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/clientes/CC/{id}')
        response = requests.get(url, headers=head)
    finally:
        return response.json()['id']

def destinoCredito(variable, head):
    try:
        url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/mshd/sqs/guardarActualizarDestinoCredito')
        data = pl.destinoCredito
        data['cadena'] = variable
        logging.info(f'Destino credito:{data}')
        response = requests.post(url, headers=head, json=data)
    finally:
        print("Destino credito ok")
        return response.text

def validarOtp(variable, otp, head):
    try:
        url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/mshd/sqs/validarotp')
        data = pl.validarOtp
        data['cadena'] = variable
        data['otp'] = otp
        data['canalContacto']['otp'] = otp
        logging.info(data)
        response = requests.post(url, headers=head, json=data)
    except Exception as err:
        raise err
    finally:
        return response.text

def validarIdentidad(cedula, idCredito, head):
    try:
        code = random.randrange(111111,999999)
        url =(f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/ado/WHO_IS_WHO/{code}/{cedula}/{idCredito}/WEB/validate')
        response = requests.get(url, headers=head)
        return response.status_code
    except Exception as err:
        raise err

def completarCliente(idSimulacion, head, dt):
    try:
        url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/simulaciones/{idSimulacion}/clientes')
        data = pl.compleCliente(dt)
        data['idSimulacion'] = str(idSimulacion)
        logging.info(f"Datos para completar cliente: {data}")
        files = {
            'archivoIdentificacion1': ('id_frente.png', open(r'.\imgns\id_frente.png', 'rb'), 'image/png'),
            'archivoIdentificacion2': ('id_atras.png', open(r'.\imgns\id_atras.png', 'rb'), 'image/png')}
        response = requests.post(url, headers=head, data=data, files=files)
        while response.status_code != 200:
            logging.info(f"Reintentando completar cliente, razon: {response.text}")
            response = requests.post(url, headers=head, data=data, files=files)
        logging.info('***COMPLETAR CLIENTE FINALIZADO***')
        return response.text
    except Exception as err:
        raise err

# EJECUTAR SELENIUM
def abrirNavegador():
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    driver.implicitly_wait(2)
    driver.maximize_window()
    driver.get("https://digicredito-dev2.excelcredit.co/login")
    wait = WebDriverWait(driver, 10)
    return driver

# LOGING
def logear(driver):
    driver.find_element(By.ID, 'login-button').click()
    driver.find_element(By.ID, 'username').send_keys("jtellez@excelcredit.co")
    driver.find_element(By.ID, 'password').send_keys("Suaita01")
    driver.find_element(By.NAME, 'login').click()
    sleep(7)
    driver.get("https://digicredito-dev2.excelcredit.co/admin/simulator")
    sleep(7)

def simuladorUno(driver, datos):
    # SELECCION DE OFICINA
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div/div/input').send_keys(datos["oficina"])
    driver.find_element(By.XPATH, '//*[@id="search-field"]/div/div/div[1]').click()
    sleep(8)

    # SIMULADOR 1
    fecha = datos['fechaNacimiento']
    fecha_dt = datetime.strptime(fecha, r'%Y-%m-%d')
    fecha_str = fecha_dt.strftime(r'%d/%m/%Y')
    # identificacion
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[1]/div[2]/input').send_keys(datos['identificacion'])
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[2]/div[1]/div/div[2]/div').click()
    sleep(5)
    # genero
    genero = datos['genero']
    if genero == "M":
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[2]/div[1]/div/div[1]/div').click()
    elif genero == "F":
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[2]/div[1]/div/div[2]/div').click()
    # departamaento y ciudad de expedicion
    driver.find_element(By.ID, 'departamento').send_keys(datos['nDepartamento'])
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[2]/div[2]/div/div/div').click()
    sleep(3)
    driver.find_element(By.ID, 'ciudad').send_keys(datos['nCiudad'])
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[2]/div[3]/div/div/div').click()
    # fecha de nacimiento
    driver.find_element(By.ID, 'fechaNacimiento').send_keys(fecha_str)
    # nivel de escolaridad
    nEducacion = datos['nivelEducacion']
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[3]/div[3]/div').click()
    sleep(2)
    if nEducacion == "NINGUNO":
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[3]/div[3]/div/div[2]/div[1]').click()
    elif nEducacion == "BACHILLERATO":
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[3]/div[3]/div/div[2]/div[2]').click()
    elif nEducacion == "TECNICO":
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[3]/div[3]/div/div[2]/div[3]').click()
    elif nEducacion == "TECNOLOGO":
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[3]/div[3]/div/div[2]/div[4]').click()
    elif nEducacion == "UNIVERSITARIO":
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[3]/div[3]/div/div[2]/div[5]').click()
    elif nEducacion == "POSGRADO": 
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[3]/div[3]/div/div[2]/div[6]').click()
    else:
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[3]/div[3]/div/div[2]/div[4]').click()
    sleep(3)
    # pagaduria
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[4]/div[1]/div/input').clear()
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[4]/div[1]/div/input').send_keys(datos['pagaduria'])
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[4]/div[1]/div/div/div').click()
    sleep(3)
    # actividad
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[4]/div[2]/div').click()
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[4]/div[2]/div/div[2]/div[1]').click()
    sleep(3)
    # tipo de pension/contrato
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[4]/div[3]/div').click()
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[4]/div[3]/div/div[2]/div[1]').click()
    # estrato
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[5]/div[1]/div/div[1]').click()
    estrato = datos['nomEstrato']
    if estrato == "Estrato 1":
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[5]/div[1]/div/div[2]/div[1]').click()
    elif estrato == "Estrato 2":
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[5]/div[1]/div/div[2]/div[2]').click()
    elif estrato == "Estrato 3":
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[5]/div[1]/div/div[2]/div[3]').click()
    elif estrato == "Estrato 4":
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[5]/div[1]/div/div[2]/div[4]').click()
    elif estrato == "Estrato 5":
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[5]/div[1]/div/div[2]/div[5]').click()
    elif estrato == "Estrato 6":
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[5]/div[1]/div/div[2]/div[6]').click()
    sleep(3)
    # total activos
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[5]/div[2]/input[1]').send_keys(datos['totalActivos'])
    # total ingresos
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[5]/div[3]/input[1]').send_keys(datos['totalIngresos'])
    # descuentos de nomina
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[6]/div[1]/input[1]').send_keys(datos['descuentosNomina'])
    # descuentos ley
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[6]/div[2]/input[1]').send_keys(datos['descuentosLey'])
    # confirmar datos
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[6]/div[3]/div/div[1]').click()
    sleep(2)
    # linea de credito
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[6]/div[3]/div/div[2]/div[3]').click()
    nombrecaptura = datetime.now().strftime(r'%d-%m-%Y_%H-%M-%S')
    driver.save_screenshot(f".\capturapant\Simulador1{nombrecaptura}.png")
    # calcular
    driver.find_element(By.ID, 'calculate').click()
    sleep(11)
    # monto
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[3]/div[1]/div[1]/div[1]/input[1]').clear()
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[3]/div[1]/div[1]/div[1]/input[1]').send_keys(datos['montoSolicitado'])
    sleep(3)
    # plazo
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[3]/div[1]/div[2]/div[1]/input[1]').clear()
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[3]/div[1]/div[2]/div[1]/input[1]').clear()
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[3]/div[1]/div[2]/div[1]/input[1]').send_keys(datos['plazo'])
    sleep(5)
    
# continuar
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[7]/button').click()
    sleep(10)
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[7]/button').click()

    # DATOS DE CLIENTE
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[4]/div/div/div[1]').click()
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[4]/div/div/div[2]/div[1]').click()
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[5]/div/input').click()
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[6]/div/button[1]').click()
    sleep(30)
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/div[5]/div/div[3]/button').click()
    sleep(5)

# REALIZANDO HABEAS DATA Y VALIDADOR DE IDENTIDAD
def habeasIdentidad(datos):
    head =token()
    ident=datos['identificacion']
    ident = int(ident)
    #print(type(ident))
    #print(ident)
    idCredito = traerCredito(identificacion=ident)
    print(idCredito)
    enVariable = enlaceVariable(idCredito=idCredito)
    print(enVariable)
    whoIsWho(idCredito=idCredito)
    idCliente = traerCliente(id=ident, head=head)
    print(idCliente)
    otps =otp(idCliente=idCliente)
    print(otps)
    head =token()
    destinoCredito(variable=enVariable, head=head)
    validarOtp(variable=enVariable, otp=otps, head=head)
    validarIdentidad(cedula=ident, idCredito=idCredito, head=head)
    sleep(5)


# CONFIGURACION DE LOS LOGGINGS
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - Proceso: %(process)s - %(levelname)s - %(message)s')
handler = logging.FileHandler('logAutomatizadorSelenium.log')
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter('%(asctime)s|%(process)s|%(levelname)s|%(message)s'))
logging.getLogger('').addHandler(handler)


# MANEJO DE INSTANCIA
instancia = "instancia2"

# TOKEN
def token():
    heads = cr.token()
    head = {'Authorization': 'Bearer {}'.format(heads)}
    return head

# CONEXIONES A BASE DE DATOS
def traerCredito(identificacion):
    try:
        conexcion = psycopg2.connect(user=cr.user, password=cr.password,
                                    host=cr.host,
                                    port=cr.port, database=cr.database)
        cursor = conexcion.cursor()
        cursor.execute(f"select cr.id  from credito cr inner join cliente cl on cl.id = cr.id_cliente where cl.identificacion = '{identificacion}' order by cr.id  desc limit 1;")
        credito =cursor.fetchall()
    finally:
        cursor.close()
        conexcion.close()
        return credito[0][0]

def whoIsWho(idCredito):
    try:
        conexcion = psycopg2.connect(user=cr.user, password=cr.password, 
                                    host=cr.host, 
                                    port=cr.port, database=cr.database) 
        cursor = conexcion.cursor()
        cursor.execute(f"update proveedor_autovalidacion  set num_intentos = 5  where id_credito = {idCredito};")
        conexcion.commit()
    finally:
        cursor.close()
        conexcion.close()

def enlaceVariable(idCredito):
    try:
        conexcion = psycopg2.connect(user=cr.user, password=cr.password, 
                                    host=cr.host, 
                                    port=cr.port, database=cr.database) 
        cursor = conexcion.cursor()
        cursor.execute(f"select id from enlacevariable e where id_credito = {idCredito};")
        enlaceVariable =cursor.fetchall()
    finally:
        cursor.close()
        conexcion.close()
        return enlaceVariable[0][0]

def otp(idCliente):
    try:
        conexcion = psycopg2.connect(user=cr.user, password=cr.password, 
                                    host=cr.hostApp, 
                                    port=cr.port, database=cr.tokens) 
        cursor = conexcion.cursor()
        cursor.execute(f"select token from otp c where id_cliente = {idCliente} order by fecha_creacion desc limit 1;")
        otp =cursor.fetchall()
    finally:
        cursor.close()
        conexcion.close()
        return otp[0][0]
    
def cambioEstado(identificacion):
    try:
        print(identificacion)
        conexcion = psycopg2.connect(user=cr.user, password=cr.password, 
                                    host=cr.host, 
                                    port=cr.port, database=cr.database) 
        cursor = conexcion.cursor()
        cursor.execute(f"update credito set estado = 'CANCELADO_POR_INCONSISTENCIAS' where id in (select c.id from credito c inner join cliente c2 on c2.id = c.id_cliente where c2.identificacion = '{identificacion}' and c.estado in ('PENDIENTE_RADICACION','FINALIZADO_FIRMA_DOCUMENTOS', 'FINALIZADO_GENERAR_DOCUMENTO_SEGURO_VIDA','EN_ESPERA_GENERAR_DOCUMENTO_SEGURO_VIDA','FINALIZADO_GENERAR_DOCUMENTO_AUT_DESEMBOLSO','EN_ESPERA_GENERAR_DOCUMENTO_AUT_DESEMBOLSO','FINALIZADO_GENERAR_DOCUMENTO_PERSONA_EXPUESTA','EN_ESPERA_GENERAR_DOCUMENTO_PERSONA_EXPUESTA','FINALIZADO_GENERAR_DOCUMENTO_SOLICITUD_CREDIT','EN_ESPERA_GENERAR_DOCUMENTO_SOLICITUD_CREDIT','FINALIZADO_GENERAR_DOCUMENTO_FIANZA','EN_ESPERA_GENERAR_DOCUMENTO_FIANZA','FINALIZADO_GENERAR_DOCUMENTO_DEBITO_BANCARIO','EN_ESPERA_GENERAR_DOCUMENTO_DEBITO_BANCARIO','EN_ESPERA_GENERAR_DOCUMENTO_SOLICITUD_CREDIT','FINALIZADO_GENERAR_DOCUMENTO_FIANZA','EN_ESPERA_GENERAR_DOCUMENTO_FIANZA','FINALIZADO_GENERAR_DOCUMENTO_DEBITO_BANCARIO','EN_ESPERA_GENERAR_DOCUMENTO_DEBITO_BANCARIO','EN_ESPERA_FIRMA_DOCUMENTOS','EN_REGISTRO_OPERACIONES_INTERNACIONALES','EN_REGISTRO_SEGURO_VIDA','EN_REGISTRO_REFERENCIAS','EN_DECISION_SEGURO_AP','EN_ESPERA_EXCEPCIONES','EN_SIMULACION_FINAL_ASESOR','EN_REGISTRO_DATOS_ADICIONALES_CLIENTE','EN_SELECCION_MEDIO_DESEMBOLSO','CALCULO_ENDEUDAMIENTO_EJECUTADO','EN_PROCESO_CALCULO_ENDEUDAMIENTO','PROSPECCION_EXITOSA','PENDIENTE_PROSPECCION','FINALIZADO_GENERAR_DOCUMENTO_HABEAS_DATA','EN_ESPERA_GENERAR_DOCUMENTO_HABEAS_DATA','EN_ESPERA_AUTORIZACION_OTP','INICIADO_DIGICREDITO'))")
        conexcion.commit()
    finally:
        cursor.close()
        conexcion.close()

def idSimulacion(idCredito):
    try:
        conexcion = psycopg2.connect(user=cr.user, password=cr.password, 
                                    host=cr.hostApp, 
                                    port=cr.port, database=cr.tokens) 
        cursor = conexcion.cursor()
        cursor.execute(f"select id from simulacion s where id_credito = {idCredito} order by id desc  ;")
        otp =cursor.fetchall()
    finally:
        cursor.close()
        conexcion.close()
        return otp[0][0]

# ENDPOINTS
def traerCliente(id, head):
    try:
        url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/clientes/CC/{id}')
        response = requests.get(url, headers=head)
    finally:
        return response.json()['id']

def destinoCredito(variable, head):
    try:
        url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/mshd/sqs/guardarActualizarDestinoCredito')
        data = pl.destinoCredito
        data['cadena'] = variable
        logging.info(f'Destino credito:{data}')
        response = requests.post(url, headers=head, json=data)
    finally:
        print("Destino credito ok")
        return response.text

def validarOtp(variable, otp, head):
    try:
        url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/mshd/sqs/validarotp')
        data = pl.validarOtp
        data['cadena'] = variable
        data['otp'] = otp
        data['canalContacto']['otp'] = otp
        logging.info(data)
        response = requests.post(url, headers=head, json=data)
    except Exception as err:
        raise err
    finally:
        return response.text

def validarIdentidad(cedula, idCredito, head):
    try:
        code = random.randrange(111111,999999)
        url =(f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/ado/WHO_IS_WHO/{code}/{cedula}/{idCredito}/WEB/validate')
        response = requests.get(url, headers=head)
        return response.status_code
    except Exception as err:
        raise err

def completarCliente(idSimulacion, head, dt):
    try:
        url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/simulaciones/{idSimulacion}/clientes')
        data = pl.compleCliente(dt)
        data['idSimulacion'] = str(idSimulacion)
        logging.info(f"Datos para completar cliente: {data}")
        files = {
            'archivoIdentificacion1': ('id_frente.png', open(r'.\imgns\id_frente.png', 'rb'), 'image/png'),
            'archivoIdentificacion2': ('id_atras.png', open(r'.\imgns\id_atras.png', 'rb'), 'image/png')}
        response = requests.post(url, headers=head, data=data, files=files)
        while response.status_code != 200:
            logging.info(f"Reintentando completar cliente, razon: {response.text}")
            response = requests.post(url, headers=head, data=data, files=files)
        logging.info('***COMPLETAR CLIENTE FINALIZADO***')
        return response.text
    except Exception as err:
        raise err

# EJECUTAR SELENIUM
def abrirNavegador():
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    driver.implicitly_wait(2)
    driver.maximize_window()
    driver.get("https://digicredito-dev2.excelcredit.co/login")
    wait = WebDriverWait(driver, 10)
    return driver

# LOGING
def logear(driver):
    driver.find_element(By.ID, 'login-button').click()
    driver.find_element(By.ID, 'username').send_keys("jtellez@excelcredit.co")
    driver.find_element(By.ID, 'password').send_keys("Suaita01")
    driver.find_element(By.NAME, 'login').click()
    sleep(7)
    driver.get("https://digicredito-dev2.excelcredit.co/admin/simulator")
    sleep(7)

def simuladorUno(driver, datos):
    # SELECCION DE OFICINA
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div/div/input').send_keys(datos["oficina"])
    driver.find_element(By.XPATH, '//*[@id="search-field"]/div/div/div[1]').click()
    sleep(8)

    # SIMULADOR 1
    fecha = datos['fechaNacimiento']
    fecha_dt = datetime.strptime(fecha, r'%Y-%m-%d')
    fecha_str = fecha_dt.strftime(r'%d/%m/%Y')
    # identificacion
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[1]/div[2]/input').send_keys(datos['identificacion'])
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[2]/div[1]/div/div[2]/div').click()
    sleep(5)
    # genero
    genero = datos['genero']
    if genero == "M":
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[2]/div[1]/div/div[1]/div').click()
    elif genero == "F":
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[2]/div[1]/div/div[2]/div').click()
    # departamaento y ciudad de expedicion
    driver.find_element(By.ID, 'departamento').send_keys(datos['nDepartamento'])
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[2]/div[2]/div/div/div').click()
    sleep(3)
    driver.find_element(By.ID, 'ciudad').send_keys(datos['nCiudad'])
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[2]/div[3]/div/div/div').click()
    # fecha de nacimiento
    driver.find_element(By.ID, 'fechaNacimiento').send_keys(fecha_str)
    # nivel de escolaridad
    nEducacion = datos['nivelEducacion']
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[3]/div[3]/div').click()
    sleep(2)
    if nEducacion == "NINGUNO":
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[3]/div[3]/div/div[2]/div[1]').click()
    elif nEducacion == "BACHILLERATO":
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[3]/div[3]/div/div[2]/div[2]').click()
    elif nEducacion == "TECNICO":
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[3]/div[3]/div/div[2]/div[3]').click()
    elif nEducacion == "TECNOLOGO":
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[3]/div[3]/div/div[2]/div[4]').click()
    elif nEducacion == "UNIVERSITARIO":
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[3]/div[3]/div/div[2]/div[5]').click()
    elif nEducacion == "POSGRADO": 
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[3]/div[3]/div/div[2]/div[6]').click()
    else:
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[3]/div[3]/div/div[2]/div[4]').click()
    sleep(3)
    # pagaduria
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[4]/div[1]/div/input').clear()
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[4]/div[1]/div/input').send_keys(datos['pagaduria'])
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[4]/div[1]/div/div/div').click()
    sleep(3)
    # actividad
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[4]/div[2]/div').click()
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[4]/div[2]/div/div[2]/div[1]').click()
    sleep(3)
    # tipo de pension/contrato
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[4]/div[3]/div').click()
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[4]/div[3]/div/div[2]/div[1]').click()
    # estrato
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[5]/div[1]/div/div[1]').click()
    estrato = datos['nomEstrato']
    if estrato == "Estrato 1":
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[5]/div[1]/div/div[2]/div[1]').click()
    elif estrato == "Estrato 2":
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[5]/div[1]/div/div[2]/div[2]').click()
    elif estrato == "Estrato 3":
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[5]/div[1]/div/div[2]/div[3]').click()
    elif estrato == "Estrato 4":
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[5]/div[1]/div/div[2]/div[4]').click()
    elif estrato == "Estrato 5":
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[5]/div[1]/div/div[2]/div[5]').click()
    elif estrato == "Estrato 6":
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[5]/div[1]/div/div[2]/div[6]').click()
    sleep(3)
    # total activos
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[5]/div[2]/input[1]').send_keys(datos['totalActivos'])
    # total ingresos
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[5]/div[3]/input[1]').send_keys(datos['totalIngresos'])
    # descuentos de nomina
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[6]/div[1]/input[1]').send_keys(datos['descuentosNomina'])
    # descuentos ley
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[6]/div[2]/input[1]').send_keys(datos['descuentosLey'])
    # confirmar datos
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[6]/div[3]/div/div[1]').click()
    sleep(2)
    # linea de credito
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[6]/div[3]/div/div[2]/div[3]').click()
    nombrecaptura = datetime.now().strftime(r'%d-%m-%Y_%H-%M-%S')
    driver.save_screenshot(f".\capturapant\Simulador1{nombrecaptura}.png")
    # calcular
    driver.find_element(By.ID, 'calculate').click()
    sleep(11)
    # monto
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[3]/div[1]/div[1]/div[1]/input[1]').clear()
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[3]/div[1]/div[1]/div[1]/input[1]').send_keys(datos['montoSolicitado'])
    sleep(3)
    # plazo
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[3]/div[1]/div[2]/div[1]/input[1]').clear()
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[3]/div[1]/div[2]/div[1]/input[1]').clear()
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[3]/div[1]/div[2]/div[1]/input[1]').send_keys(datos['plazo'])
    sleep(5)
    
# continuar
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[7]/button').click()
    sleep(10)
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[7]/button').click()

    # DATOS DE CLIENTE
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[4]/div/div/div[1]').click()
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[4]/div/div/div[2]/div[1]').click()
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[5]/div/input').click()
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[6]/div/button[1]').click()
    sleep(30)
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/div[5]/div/div[3]/button').click()
    sleep(5)
    
  

# REALIZANDO HABEAS DATA Y VALIDADOR DE IDENTIDAD
def habeasIdentidad(datos):
    head =token()
    ident=datos['identificacion']
    ident = int(ident)
    print(type(ident))
    print(ident)
    idCredito = traerCredito(identificacion=ident)
    print(idCredito)
    enVariable = enlaceVariable(idCredito=idCredito)
    print(enVariable)
    whoIsWho(idCredito=idCredito)
    idCliente = traerCliente(id=ident, head=head)
    print(idCliente)
    otps =otp(idCliente=idCliente)
    print(otps)
    head =token()
    destinoCredito(variable=enVariable, head=head)
    validarOtp(variable=enVariable, otp=otps, head=head)
    idSim = idSimulacion(idCredito=idCredito)
    validarIdentidad(cedula=ident, idCredito=idCredito, head=head)
    completarCliente(idSimulacion=idSim, head=head, dt=datos)
    sleep(5)

# RETOMAR CREDITO
def retomarCredito(driver, datos):
    driver.get("https://digicredito-dev2.excelcredit.co/admin/dashboard")
    sleep(10)
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div[1]/div[2]/div[1]/input').send_keys(datos['identificacion'])
    sleep(10)
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div[1]/div[3]/div/div[2]/div[1]/div[3]/div/span[2]/button').click()
    sleep(10)



def clic_hasta_elemento(driver, boton_a_clickear, elemento_a_esperar, max_intentos=50):
    try:
        # Establecer un tiempo de espera máximo en segundos
        wait = WebDriverWait(driver, max_intentos)

        # Ciclo for para hacer clic en el botón hasta que se encuentre el elemento esperado
        for _ in range(max_intentos):
            try:
                # Hacer clic en el botón
                boton = wait.until(EC.element_to_be_clickable((By.XPATH, boton_a_clickear)))
                boton.click()

                # Esperar a que aparezca el elemento deseado
                wait.until(EC.presence_of_element_located((By.XPATH, elemento_a_esperar)))

                # Si el elemento deseado aparece, se sale del ciclo
                break
            except:
                # Si hay una excepción (por ejemplo, el botón no está disponible), se imprime un mensaje y se sigue con el ciclo
                print("El botón no está disponible o el elemento esperado no se encontró.")

    finally:
        # No cerramos el navegador aquí ya que el objeto driver es gestionado externamente

# Ejemplo de uso de la función


     clic_hasta_elemento(driver, '/html/body/div/main/div[2]/div[2]/div[1]/div[2]/div/div[3]/div[1]/div[1]/svg[1]', '/html/body/div/main/div[2]/div[2]/div[1]/div[2]/div/div[4]/button')






    
# DATOS COMPLEMENTARIOS -> EN_REGISTRO_DATOS_ADICIONALES_CLIENTE 
def datos_complementarios(driver, datos):
    try:
        # PAIS DE NACIMIENTO
        #driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[1]/div').click()
        #sleep(2)
        #driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[1]/div/div[2]/div[1]').click()
        #sleep(2)

        # CIUDAD DE NACIMIENTO
        input_element = driver.find_element(By.ID, 'lugarNacimiento2')
        input_element.clear() 
        input_element.send_keys(datos['nCiudad']) 
        sleep(2)

        # GRUPO ÉTNICO
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[3]/div[3]/div').click()
        sleep(2)
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[3]/div[3]/div/div[2]/div[6]').click()
        sleep(2)

        # DEPARTAMENTO DE RESIDENCIA
        dato_completo = datos['departamento'] 
        dato_sin_iniciales = dato_completo[3:] 
        campo_departamento = driver.find_element(By.ID, 'departamento')
        campo_departamento.send_keys(dato_sin_iniciales)
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[4]/div[1]/div/div/div').click()
        sleep(2)

        # CIUDAD O MUNICIPIO DE RESIDENCIA
        dato_completo = datos['nCiudad'] 
        dato_sin_iniciales = dato_completo[3:] 
        campo_departamento = driver.find_element(By.ID, 'ciudad')
        campo_departamento.send_keys(dato_sin_iniciales)
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[4]/div[2]/div/div/div').click()
        sleep(2)

        # DIRECCIÓN DE RESIDENCIA
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[5]/div[1]/input').click()
        sleep(2)
        driver.find_element(By.ID, 'calleModal').send_keys("CARRERA")
        sleep(2)
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/div/div[1]/div[2]/div[1]/div[1]/div/div/div/div[2]').click()
        sleep(2)
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/div/div[1]/div[2]/div[1]/div[2]/input').send_keys("10")
        sleep(2)
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/div/div[1]/div[2]/div[2]/div[2]/input').send_keys("27")
        sleep(2)
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/div/div[1]/div[2]/div[2]/div[5]/input').send_keys("11")
        sleep(2)
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/div/div[1]/div[3]/button').click()
        sleep(2)

        # BARRIO
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[5]/div[2]/input').send_keys("CENTRO")
        sleep(2)

        # GENERO

                # Obtener el género del objeto EP
        genero_ep = datos['genero'] 
        try:
            if genero_ep.upper() == 'M':
                driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[7]/div/div/div[1]/div').click()
            elif genero_ep.upper() == 'F':
                driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[7]/div/div/div[2]/div').click()
            else:
                print("Género no válido. Debe ser 'M' o 'F'.")
        except Exception as e:
            print("Error en la línea:", e)

        # NUMERO DE HIJOS
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[8]/div[1]/input').send_keys("1")
        sleep(2)

        # PERSONAS A CARGO
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[8]/div[2]/input').send_keys("1")
        sleep(2)

        # PROFESIÓN
        input_element = driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[9]/div[1]/input')
        input_element.clear() 
        input_element.send_keys("PENSIONADO") 
        sleep(2)

        # ESTADO CIVIL
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[9]/div[2]/div').click()
        sleep(2)
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[9]/div[2]/div/div[2]/div[1]').click()

        sleep(5)

        # CONTINUAR SIGUIENTE ESTADO
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[11]/button').click()
        sleep(10)
    except Exception as e:
        print("Error en datos_complementarios:", e)

#datos_complementarios(driver, datos)



# DATOS LABORALES O PENSIONALES -> SIMULACION_FINAL_ASESOR

def datos_laborales_o_pensionales(driver, datos):
    try:
        try:
            # Intenta encontrar y completar el campo NIT de afiliación
            input_element = driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div/input')
            input_element.clear() 
            input_element.send_keys("906522914100") 
            sleep(2)
        except:
            # Si el campo NIT de afiliación no está presente, sigue con el proceso normal
            pass

        # Completa el campo de fecha de ingreso o inicio de pensión
        hoy = datetime.now()
        fechaIngreso = hoy.strftime("%d-%m-%Y")
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[4]/div/div/input').send_keys(fechaIngreso)
        sleep(2)

        # TIPO DE DOCUMENTO
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[7]/div/div').click()
        sleep(2)
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[7]/div/div/div[2]/div').click()
        sleep(2)

        # CARGAR IMAGEN
        upload_file = "D:\\Usuarios\\aprendiz.desarrollo1\\Desktop\\digicredito V2\\imgns\\2.png"  # Ruta de tu archivo de imagen
        file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        file_input.send_keys(upload_file)
        driver.find_element(By.XPATH, "/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[8]/div/label/div").click()
        sleep(2)

        # AVANZAR AL SIGUIENTE ESTADO
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[9]/button[2]').click()
        sleep(10)
    except Exception as e:
        print("Error en datos_laborales_o_pensionales:", e)

#datos_laborales_o_pensionales(driver, datos)



#DATOS PARA EL CREDITO

def datos_para_el_credito(driver, datos):
        #TOTAL INGRESOS MENSUALES
    input_element = driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[3]/div[1]/input[1]')
    input_element.clear() 
    input_element.send_keys("50000000") 
    sleep(4)
        # CONTINUAR SIGUIENTE ESTADO
    driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[8]/button[2]').click()
    sleep(10)

#datos_para_el_credito(driver, datos)

#RESULTADOS CALCULO CREDITO 

def resultados_calculo_credito(driver, datos):
    try:

       # Desplegar las opciones de la lista
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/form/div[2]/div/div').click()
        sleep(5)

        # Obtener todos los elementos de la lista desplegable
        opciones_tasa = driver.find_elements(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/form/div[2]/div/div/div[2]')

        # Verificar si se encontraron opciones
        if opciones_tasa:
            # Seleccionar una tasa al azar
            tasa_seleccionada = random.choice(opciones_tasa)

            # Hacer clic en la tasa seleccionada
            tasa_seleccionada.click()
        else:
            print("No se encontraron opciones en la lista desplegable.")
    
        # TASA %
        #driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/form/div[2]/div/div').click()
        #sleep(5)
        #driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/form/div[2]/div/div/div[2]/div[1]').click()
        #sleep(5)

        # BOTON "CALCULAR"
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div/button').click()
        sleep(5)

        # BOTON CONTINUAR DE ESTADO
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/div[3]/div[2]/button').click()
        sleep(5)

        # BOTON MODAL
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/div[4]/div/div[3]/button').click()
        sleep(10)
    except Exception as e:
        print("Error en resultados_calculo_credito:", e)
#resultados_calculo_credito(driver, datos)


        # INFORMACIÓN BÁSICA SOLICITANTE -> ENDEUDAMIENTO GLOBAL

def informacion_basica_solicitante(driver):
    try:


        # TIPO DE VIVIENDA
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div').click()
        sleep(2)
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div/div[2]/div[1]').click()
        sleep(2)

        # CLASE DE VIVIENDA
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[1]/div').click()
        sleep(2)
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[1]/div/div[2]/div[1]').click()
        sleep(2)

        # POSICIÓN EN EL HOGAR
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[2]/div').click()
        sleep(2)
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/div[2]/div/div[2]/div[1]').click()
        sleep(2)

        # NÍVEL DE ESCOLARIDAD
        #driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[3]/div[2]/div').click()
        #sleep(5)
        #driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[3]/div[2]/div/div[2]/div[4]').click()
        #sleep(5)

        # BOTON CONTINUAR 
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[4]/button').click()
        sleep(10)
    except Exception as e:
        print("Error en la línea:", e)

# Llamada a la función
#informacion_basica_solicitante(driver)


#INFORMACION FINANCIERA -> ENDEUDAMIENTO GLOBAL 

def informacion_financiera(driver, datos):
    try:
        # TOTAL DESCUENTOS DE LEY
        input_element = driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div/input[1]')
        input_element.send_keys(datos['descuentosLey']) 
        sleep(2)

        # TOTAL OTROS DESCUENTOS DE NÓMINA
        input_element = driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[3]/div/input[1]')
        input_element.send_keys(datos['descuentosNomina']) 
        sleep(2)

        # TIPO DOCUMENTO
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[6]/div/div').click()
        sleep(2)
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[6]/div/div/div[2]/div[1]').click()
        sleep(4)

        # DESPRENDIBLE DE NÓMINA U OTRO
        upload_file = "D:\\Usuarios\\aprendiz.desarrollo1\\Desktop\\digicredito V2\\imgns\\2.png"  # Ruta de tu archivo de imagen
        file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        file_input.send_keys(upload_file)
        driver.find_element(By.XPATH, "/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[7]/div/label/div").click()
        sleep(5)

        # BOTON CONTINUAR ESTADO
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[8]/button[2]').click()
        sleep(10)
    except Exception as e:
        print("Error en informacion_financiera:", e)

#informacion_financiera(driver, datos)



#MODALIDAD DE DESEMBOLSO -> EN SELECCION MEDIO DESEMBOLSO 

def modalidad_desembolso(driver):
    try:
       #MODALIDAD DE DESEMBOLSO -> EN SELECCION MEDIO DESEMBOLSO 

            #TIPO DE CUENTA 
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[3]/div[1]/div[1]/div').click()
        sleep(2)

            #ENTIDAD FINANCIERA
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[3]/div[2]/div[1]/div').click()
        sleep(2)
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[3]/div[2]/div[1]/div/div[2]/div[18]').click()
        sleep(2)

            #NÚMERO DE CUENTA    
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[3]/div[2]/div[2]/input').send_keys("12345678912345")
        sleep(2)

            #DEPARTAMENTO DE LA CUENTA DE AHORROS O CTE.
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[3]/div[3]/div[1]/div/input').send_keys("Amazonas")
        sleep(2)
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[3]/div[3]/div[1]/div/div/div').click()
        sleep(2)

            #CIUDAD DE LA CUENTA DE AHORROS O CTE.
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[3]/div[3]/div[2]/div/input').send_keys("Leticia")
        sleep(1)
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[3]/div[3]/div[2]/div/div/div').click()
        sleep(2)

            #BOTON CONTINUAR ESTADO
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[4]/button').click()
        sleep(10)

    except Exception as e:
        print("Error en informacion_financiera:", e)

#modalidad_desembolso(driver)

# #Seguros AP
def realizar_acciones(driver):
    try:
        # Hacer clic en el botón
        button_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div/main/div[2]/div[2]/div[2]/div/div[3]/button'))
        )
        button_element.click()
        sleep(5)

        # Cerrar el spam
        span_element_ap = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="exception-page"]/div[2]/div[2]/div/div/div[3]/span'))
        )
        span_element_ap.click()
        sleep(5)

        # Aceptar seguros ape
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div[2]/div/div[3]/button[1]').click()
    except Exception as e:
        print(f"No se pudieron realizar las acciones. Error: {e}")

# Suponiendo que `driver` ya está inicializado previamente
#realizar_acciones(driver)


#En registro datos adicionales cliente - REFERENCIA - primera pantalla
def completar_formulario(driver, datos):
    try:
        # Hacer clic en un elemento del formulario
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]').click()
        

        # Borrar campos
        campos = [
            '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[1]/div[1]/input',
            '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[1]/div[2]/input',
            '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[2]/div[1]/input',
            '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[2]/div[2]/input',
            '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[3]/div[2]/div/input'
        ]

        for campo_xpath in campos:
            campo = driver.find_element(By.XPATH, campo_xpath)
            campo.clear()
        sleep(5)

        # Ingresar datos en varios campos de texto
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[1]/div[2]/input').send_keys(datos['nombre2'])
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[1]/div[1]/input').send_keys(datos['nombre1'])
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[2]/div[1]/input').send_keys(datos['apellido1'])
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[2]/div[2]/input').send_keys(datos['apellido2'])
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[3]/div[2]/div/input').send_keys(datos['celular'])

        #Relacion 1 vista
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[3]/div[1]/div').click()
        #amigo
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[3]/div[1]/div/div[2]/div[2]').click()
        sleep(5)

        # Boton siguiente 
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/button').click()
        sleep(5)

        # Socio
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]').click()

        # Borrar el contenido de un campo de texto
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]').click()

        campos = [
            '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[1]/div[1]/input',
            '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[1]/div[2]/input',
            '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[2]/div[1]/input',
            '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[2]/div[2]/input',
            '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[3]/div[2]/div/input'
        ]

        for campo_xpath in campos:
            campo = driver.find_element(By.XPATH, campo_xpath)
            campo.clear()
        sleep(5)

        # Ingresar contenido 
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[1]/div[1]/input').send_keys(datos['nombre2'])
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[1]/div[1]/input').send_keys(datos['nombre1'])
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[2]/div[1]/input').send_keys(datos['apellido1'])
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[2]/div[2]/input').send_keys(datos['apellido2'])
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[3]/div[2]/div/input').send_keys(datos['celular'])

        # Relacion 1 vista
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[3]/div[1]/div').click()
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[3]/div[1]/div/div[2]/div[3]').click()
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/button[2]').click()
        sleep(5)
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/div[2]/div/div[3]/button').click()
        sleep(10)
        
        #Relacion 1 vista
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[3]/div[1]/div').click()
        #amigo
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[3]/div[1]/div/div[2]/div[2]').click()
        sleep(5)
        # Compañero
        # driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[3]/div[1]/div/div[2]/div[3]').click()
        # sleep(5)
        # Conocido
        # driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[3]/div[1]/div/div[2]/div[4]').click()
        # sleep(5)
        # Otro
        # driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[3]/div[1]/div/div[2]/div[5]').click()
        #Socio
        # driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]').click()


        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/button').click()
        sleep(5)


    except NoSuchElementException as e:
        print("Error: Elemento no encontrado. Detalles:", e)
        # Aquí puedes agregar cualquier otra lógica que desees para manejar el error

# Ejecucion
#completar_formulario(driver, datos)
sleep(5)

#En registro datos adicionales cliente - REFERENCIA - segunda pantalla
def completar_formulario_referencia(driver, datos):
    try:
        # Desplegar formulario
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]').click()

        # Borrar el contenido de un campo de texto
        campos = [
            '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[1]/div[1]/input',
            '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[1]/div[2]/input',
            '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[2]/div[1]/input',
            '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[2]/div[2]/input',
            '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[3]/div[2]/div/input'
        ]

        for campo_xpath in campos:
            campo = driver.find_element(By.XPATH, campo_xpath)
            campo.clear()
        sleep(5)

        # Llenar campos datos relacionados
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[1]/div[1]/input').send_keys(datos['nombre2'])
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[1]/div[1]/input').send_keys(datos['nombre1'])
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[2]/div[1]/input').send_keys(datos['apellido1'])
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[2]/div[2]/input').send_keys(datos['apellido2'])
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[3]/div[2]/div/input').send_keys(datos['celular'])

        # Seleccionar opción en lista de relación
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[3]/div[1]/div').click()
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[3]/div[1]/div/div[2]/div[3]').click()
        
        #Boton siguiente 
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/button[2]').click()
        sleep(5)
        
        # Hacer clic en spam
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/div[2]/div/div[3]/button').click()
        sleep(10)

    except NoSuchElementException as e:
        print("Error: Elemento no encontrado. Detalles:", e)
    except Exception as e:
        print("Error desconocido:", e)

# Ejecucion:
#completar_formulario_referencia(driver, datos)


sleep(2)
#Seguros de vida 
#primera pantalla llenar campos 
def completar_formulario_cliente(driver, datos):
    try:
        # Ingresar nombre y apellido
        driver.find_element(By.ID, 'nombres_apellidos0').send_keys(datos['nombre1'] + ' ' + datos['apellido1'])
        
        # Ingresar documento de identificación
        driver.find_element(By.ID, 'documento0').send_keys(datos['identificacion'])
        
        # Ingresar departamento
        dato_completo = datos['departamento'] 
        dato_sin_iniciales = dato_completo[3:] 
        campo_departamento = driver.find_element(By.ID, 'departamento0')
        campo_departamento.send_keys(dato_sin_iniciales)
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div[1]/div[2]/form/div[1]/div[4]/div[2]/div/input').click()

        # Seleccionar género
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div[1]/div[2]/form/div[1]/div[5]/div[1]/div/input').click()
        sleep(5)

        # Ingresar número de celular
        driver.find_element(By.ID, 'celular0').send_keys(datos['celular'])

        # Ingresar tasa
        driver.find_element(By.ID, 'tasa0').send_keys('100')
        sleep(5)

        # Seleccionar opción
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div[1]/div[2]/form/div[1]/div[4]/div[2]/div/div').click()
        sleep(5)
        
        #CIUDAD O MUNICIPIO DE RESIDENCIA
        dato_completo = datos['ciudad'] 
        dato_sin_iniciales = dato_completo[3:] 
        campo_departamento = driver.find_element(By.ID, 'ciudad0')
        campo_departamento.send_keys(dato_sin_iniciales)
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div[1]/div[2]/form/div[1]/div[5]/div[1]/div/input').click()
        sleep(10)
        
        #boton siguiente
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div[1]/div[2]/form/div[2]/button').click()
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div[3]/div/div[3]/button').click()
        sleep(10)
       
    except NoSuchElementException as e:
        print("Error: Elemento no encontrado. Detalles:", e)
    except Exception as e:
        print("Error desconocido:", e)

# ejecutable:
#completar_formulario_cliente(driver, datos)


# #OPERACIONES INTERNACIONALES
def click_elementos_y_esperar(driver):
    try:
        # Hacer clic en el primer elemento y esperar
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[6]/div/div/div[2]/div').click()
        sleep(5)

        # Hacer clic en el segundo elemento y esperar
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[7]/button').click()
        sleep(5)

        # Hacer clic en el tercer elemento y esperar
        driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/div/div/div[3]/button').click()
        sleep(5)

    except Exception as e:
        print("Ocurrió un error:", e)
#click_elementos_y_esperar(driver)

"""
#FIRMA FINAL DOCUMENTO
# Esperar a que el elemento sea clickeable
sleep(5)
elemento_descargar = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/div[4]/div/div[3]/button'))
)
# Hacer clic en el elemento
elemento_descargar.click()
sleep(5)

#Descargar documentos 
# driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div').click()


#Boton siguiente 
elemento_otro = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/div[3]/button'))
)
# Hacer clic en el otro elemento
elemento_otro.click()




#modulo 3
driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[1]/div').click()
driver.find_element(By.ID, 'option1').click()
driver.find_element(By.ID, 'descripcion').send_keys("ADICCIONAL")

#SUBIR ARCHIVO 
upload_file = "D:\\Usuarios\\aprendiz.desarrollo2\\Documents\\automatisacion\\imgns\\2.png"  # Ruta de tu archivo de imagen
file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
file_input.send_keys(upload_file)
driver.find_element(By.XPATH, '//*[@id="input-file"]/label/div').click()
driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/form/div[2]/button[2]').click()

##validacion de eliminacion boton si 
driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div[2]/div/div[2]/div[2]/div[2]/div[2]/div/div[2]/div[4]/div/div/div/div').click()
sleep(30)
"""

# MAIN
while True:
    try:
        datos = CL.dataSimulador()
        print(datos)
        cambioEstado(identificacion = datos['identificacion'])
        driver =abrirNavegador()
        logear(driver=driver)
        simuladorUno(driver=driver, datos=datos)
        habeasIdentidad(datos=datos)
        retomarCredito(driver=driver, datos=datos)
        datos_complementarios(driver=driver, datos=datos)
        datos_laborales_o_pensionales(driver=driver, datos=datos)
        datos_para_el_credito(driver=driver, datos=datos)
        resultados_calculo_credito(driver=driver, datos=datos)
        informacion_basica_solicitante(driver=driver)
        informacion_financiera(driver=driver, datos=datos)
        modalidad_desembolso(driver=driver)
        realizar_acciones(driver=driver)
        completar_formulario(driver=driver, datos=datos)
        completar_formulario_referencia(driver=driver, datos=datos)
        completar_formulario_cliente(driver=driver, datos=datos)
        click_elementos_y_esperar(driver=driver)
    finally:
        continue