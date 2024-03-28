import requests
import crdncls as cr
import payLoads as pl
import casesListas as cl
import psycopg2
import random
import multiprocessing as MP
import time
import logging
from time import sleep

# CONFIGURACION DE LOS LOGGINGS
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - Proceso: %(process)s - %(levelname)s - %(message)s')
handler = logging.FileHandler('logAutomatizador.log')
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter('%(asctime)s|%(process)s|%(levelname)s|%(message)s'))
logging.getLogger('').addHandler(handler)

"""./digicredito/imgns/id_front.png"""

""" SE VA A TRABAJAR LOS EP Y LOS PAYLOADS EN ARCHIVOS APARTE, CON ESTO MANTENEMOS
UNA UNIFORMIDAD EN EL CODIGO SE VAN A USAR NOMBRES DE VARIABLES Y FUNCIONES BIEN DEFINIDOS
PARA NO TENER PROBLEMAS DE IDENTIFICACION DEL PROCESO AL CUAL PERTENECEN"""

instancia = "instancia2"

# TOKEN
def token():
    # cr.token()
    # heads = open("./noms.txt", "r")
    # head = {'Authorization': 'Bearer {}'.format(heads.read())}
    heads = cr.token()
    head = {'Authorization': 'Bearer {}'.format(heads)}
    return head

# CONEXIONES A BASE DE DATOS

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
    
def cancelarCredito(idCredito):
    try:
        conexcion = psycopg2.connect(user=cr.user, password=cr.password, 
                                    host=cr.host, 
                                    port=cr.port, database=cr.database) 
        cursor = conexcion.cursor()
        cursor.execute(f"update credito  set estado = 'CANCELADO_POR_INCONSISTENCIAS' where id = {idCredito};")
        conexcion.commit()
    finally:
        cursor.close()
        conexcion.close()

def cambiarEstado(idCredito):
    try:
        conexcion = psycopg2.connect(user=cr.user, password=cr.password, 
                                    host=cr.host, 
                                    port=cr.port, database=cr.database) 
        cursor = conexcion.cursor()
        cursor.execute(f"update credito  set estado = 'EN_PROCESO_CALCULO_ENDEUDAMIENTO' where id = {idCredito};")
        conexcion.commit()
    finally:
        cursor.close()
        conexcion.close()

def obtenerCiudadExpedicion(identidad):
    try:
        conexcion = psycopg2.connect(user=cr.user, password=cr.password, 
                                    host=cr.host, 
                                    port=cr.port, database=cr.database) 
        cursor = conexcion.cursor()
        cursor.execute(f"select c.id_ciudad_expedicion_identificacion from cliente c where c.identificacion ='{identidad}';")
        idExpedicion =cursor.fetchall()
        logging.info(f'LA CIUDAD DE EXPEDICION DEL DOCUMENTO ES:{idExpedicion}')
    finally:
        cursor.close()
        conexcion.close()

# def capitalizacionCxC(idCredito):
#     try:
#         conexcion = psycopg2.connect(user=cr.user, password=cr.password, 
#                                     host=cr.host, 
#                                     port=cr.port, database=cr.database) 
#         cursor = conexcion.cursor()
#         cursor.execute(f"select * from capitalizacion_cxc cc  where id_credito = {idCredito};")
#         capitalizacion =cursor.fetchall()
#         ncuota = capitalizacion[2]
#         logging.info(f"LA DATA GRADRADA EN CAPITALIZACION CxC ES LA SIGUIENTE: NUMERO DE CUOTA {ncuota},")
#     finally:
#         cursor.close()
        # conexcion.close()

# ENDPOINTS

def simulador(data, head):
    url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/simulacion')
    response = requests.post(url, headers=head, json=data)
    response.raise_for_status()
    logging.debug(f'Se genera el credito: {response.text}')
    lineaCredito = response.json()['idLineaCredito']
    idSim = response.json()['idSimulacion']
    tasa = response.json()['tasa']
    plazo = response.json()['plazo']
    grupo = response.json()['productPricing']['productGroupId']
    return (idSim, lineaCredito, tasa, plazo, grupo)

def retomarCredito(idSimulacion, head):
    try:
        url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/simulacion/{idSimulacion}')
        response = requests.get(url, headers=head)
    finally:
        return response.json()["idCredito"]

def traerCliente(identidad, head):
    try:
        url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/clientes/CC/{identidad}')
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
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise err
    finally:
        return response.text

def validarIdentidad(cedula, idCredito, head):
    try:
        code = random.randrange(111111,999999)
        url =(f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/ado/WHO_IS_WHO/{code}/{cedula}/{idCredito}/WEB/validate')
        response = requests.get(url, headers=head)
        response.raise_for_status()
        return response.status_code
    except requests.exceptions.HTTPError as err:
        raise err

def completarCliente(idSimulacion, head, dt):
    try:
        url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/simulaciones/{idSimulacion}/clientes')
        data = pl.compleCliente(dt)
        data['idSimulacion'] = str(idSimulacion)
        logging.info(f"Datos para completar cliente: {data}")
        files = {
            'archivoIdentificacion1': ('id_frente.png', open(r'D:\Usuarios\analista.pruebas5\Desktop\Pruebas\digicredito\imgns\id_frente.png', 'rb'), 'image/png'),
            'archivoIdentificacion2': ('id_atras.png', open(r'D:\Usuarios\analista.pruebas5\Desktop\Pruebas\digicredito\imgns\id_atras.png', 'rb'), 'image/png')}
        response = requests.post(url, headers=head, data=data, files=files)
        while response.status_code != 200:
            logging.info(f"Reintentando completar cliente, razon: {response.text}")
            response = requests.post(url, headers=head, data=data, files=files)
        response.raise_for_status()
        return response.text
    except requests.exceptions.HTTPError as err:
        raise err

def notifyCompletion(idCredito,head):
    try:
        url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/prospecting/credits/{idCredito}/WEB/notify-completion')
        response = requests.post(url, headers=head)
        logging.info(response.text)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        cambiarEstado(idCredito=idCredito)
        raise err
    finally:
        return response.text


def finantialObigations(idCredito, head):
    try:
        url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/credits/{idCredito}/financial-obligations')
        response = requests.get(url, headers=head)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        raise err

def globalDebt(head, dt, idCredito):
    with open(r'D:\Usuarios\analista.pruebas5\Desktop\Pruebas\digicredito\imgns\Desprendible de nomina dummie.png', 'rb') as f:
        documento = f.read()
        f.close()
        filessoporte ={'archivo': ('Desprendible de nomina dummie.png', documento, 'image/png')}
    url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/global-debt')
    data = pl.endeudamientoGlobal(dt)
    data['save'] = 'false'
    data['idCredito'] = str(idCredito)
    logging.info(f'Datos de endeudamiento global: {data}')
    response = requests.post(url, headers=head, data=data, files=filessoporte)
    logging.info(response.json())
    valor = response.json()['ingresosFaltantesAproximados']
    data['save'] = 'true'
    if valor != 0:
        try:
            logging.info(f"Ingresos faltantes aproximados: {valor}")
            data['ingresosAdicionales'] = str(int(valor))
            filessoporte['archivoIngresosAdicionales'] = ('Desprendible de nomina dummie.png', documento, 'image/png')
            logging.info(data)
            response = requests.post(url, headers=head, data=data, files=filessoporte)
        finally:
            return response.json()
    else:
        try:
            logging.info(f"No se requieren ingresos adicionales")
            logging.info(data)
            response = requests.post(url, headers=head, data=data, files=filessoporte)
        finally:
            return response.json()
        

def medioDesembolso(head, idCredito, dt):
    try:
        url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/credits/{idCredito}/WEB/disbursement-mean')
        data = pl.medioDeDesembolso(dt)
        data['idCredito'] = idCredito
        logging.info(f'Data de medio de desembolso: {data}')
        response = requests.post(url, headers=head, json=data)
    finally:
        return response.text

def basicData(idCredito, head, dt):
    try:
        url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/credits/{idCredito}/basic-data')
        data = pl.basData(dt)
        data['idCredito'] = idCredito
        logging.info(f'Data de basic data: {data}')
        response = requests.put(url, headers=head, json=data)
    finally:
        return response.status_code

def additionalData(idCredito, head, dt):
    try:
        url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/credits/{idCredito}/additional-data')
        data = pl.addData(dt)
        data['idCredito'] = idCredito
        logging.info(f'Data de additional data: {data}')
        response = requests.put(url, headers=head, json=data)
    finally:
        return response.status_code

def workData (idCredito, head, dt):
    try:
        with open(r'D:\Usuarios\analista.pruebas5\Desktop\Pruebas\digicredito\imgns\Desprendible de nomina dummie.png', 'rb') as f:
            documento = f.read()
            f.close()
            files = {'certificacionLaboral': ('Desprendible de nomina dummie.png', documento, 'image/png')}
        url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/credits/{idCredito}/WEB/work-data')
        data = pl.wrkData(dt)
        data['idCredito'] = str(idCredito)
        logging.info(f'Data de work data: {data}')
        response = requests.put(url, headers=head, data=data, files=files)
        print(response.text)
    finally:
        return response.status_code

def simuladorDos (head, dt, linea):
    try:
        url= (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/simulacion/simular')
        data = pl.dataSim2(dt)
        data['idLineaCredito'] = linea
        logging.info(f'Data de simulador dos: {data}')
        response = requests.post(url, headers=head, json=data)
    finally:
        return response.text

def dataparaSimulador2():
    url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/get-product-model-pricing/false')

def finalizarSimulacion(idCredito, head, dt, linea):
    try:
        url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/credits/{idCredito}/WEB/simulation-data')
        data = pl.finalSimulacion(dt)
        data['idCredito'] = idCredito
        data['idLineaCredito'] = linea
        logging.info(f'Data de finalizar simulacion: {data}')
        response = requests.put(url, headers=head, json=data)
        response.raise_for_status()
    finally:
        return response.text

def skipExceptions(idCredito, head):
    try:
        url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/exception-stage/skip/credits/{idCredito}')
        data = {"idCredito": idCredito}
        logging.info(f'Data de skip exceptions: {data}')
        response = requests.patch(url, headers=head, json=data)
        response.raise_for_status()
    finally:
        return response.text
    
def cambioReferencias (idCredito, head):
    url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/credits/{idCredito}/state/EN_REGISTRO_REFERENCIAS')
    data = {"idCredito": idCredito}
    response = requests.patch(url, headers=head, json=data)
    return response.text


def seguroAp(idCredito, idCliente, head, dt):
    try:
        url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/seguroap/seguro/{idCredito}')
        data = pl.apChoise(dt)
        data['id_cliente'] = idCliente
        data['idCredito'] = idCredito
        logging.info(f'Data de seguro ap: {data}')
        response = requests.post(url, headers=head, json=data)
        # response.raise_for_status()
    finally:
        return response.text

def referencias(idCredito, head):
    try:
        url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/create-references')
        data = pl.referencias
        data[0]['idCredito'] = idCredito
        data[1]['idCredito'] = idCredito
        logging.info(f'Data de referencias: {data}')
        response = requests.put(url, headers=head, json=data)
        # response.raise_for_status()
    finally:
        return response.text

def seguroVida(idCredito, head):
    url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/create-beneficiaries')
    data = pl.beneficiarios
    data[0]['idCredito'] = idCredito
    logging.info(f'Data de seguro vida: {data}')
    response = requests.put(url, headers=head, json=data)
    print(response.text)
    return response.status_code

def crearPeps(idCredito, head):
    url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/create-pep')
    data = pl.peps
    data['idCredito'] = idCredito
    logging.info(f'Data de crear peps: {data}')
    ressponse = requests.put(url, headers=head, json=data)
    return ressponse.text

def grabarIo(idCredito, head):
    url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/save-international-operations')
    data = pl.oi
    data['idCredito'] = idCredito
    logging.info(f'Data de grabar io: {data}')
    response = requests.put(url, headers=head, json=data)
    return response.text

def comenzarFirmas(idCredito, idCliente, head):
    try:
        url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/creditos/{idCredito}/firma-documentos/aceptar')
        data = {"idCliente": idCliente,
                "idCredito": idCredito,
                "token": ""}
        logging.info(f'Data de comenzar firmas: {data}')
        response = requests.patch(url, headers=head, json=data)
        response.raise_for_status()
        return response.text
    except requests.exceptions.HTTPError as err:
        raise err

def finalizarCredito(idCredito, head):
    url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/credits/{idCredito}/WEB/establish')
    data = {"idCredito": idCredito,
            "subCanal": "WEB"}
    logging.info(f'Data de finalizar credito: {data}')
    response = requests.post(url, headers=head, json=data)
    return response.text
    

def main():
    try:
        logging.info("CICLO INICIADO")
        head = token()
        data = cl.dataSimulador()
        datas = pl.dataSimulador(data=data)
        logging.info(f"DATOS USADOS PARA LA SIMULACION: {datas}")
        sleep(1)
        head = token()
        respuestaSimulador = simulador(data=datas, head=head)
        idSimulacion = respuestaSimulador[0]
        sleep(1)
        logging.info(f"idSimulacion: {idSimulacion}")
        idCredito = retomarCredito(idSimulacion=idSimulacion, head=head)
        logging.info(f"IDCREDITO: {idCredito}")
        identidad = datas["cliente"]["identificacion"]
        logging.info(f"IDENTIDAD: {identidad}")
        idCliente = traerCliente(identidad=identidad, head=head)
        logging.info(f"IDCLIENTE: {idCliente}")
        # capitalizacionCxC(idCredito=idCredito)
        obtenerCiudadExpedicion(identidad=identidad)
        sleep(4)
        logging.info("OBTENIANDO ENLACE VARIABLE")
        eVariable = enlaceVariable(idCredito=idCredito)
        logging.info(f"eVariable: {eVariable}")
        logging.info("OBTENIENDO OTP")
        otps = otp(idCliente=idCliente)
        logging.info(f"otps: {otps}")
        logging.info("ENVIANDO DATOS A DESTINO CREDITO")
        logging.debug(destinoCredito(variable=eVariable, head=head))
        logging.info("ENVIANDO DATOS A VALIDAR OTP")
        logging.debug(validarOtp(variable=eVariable, otp=otps, head=head))
        sleep(random.randint(5, 10))
        logging.info("VALIDANDO IDENTIDAD CON WHO IS WHO")
        whoIsWho(idCredito=idCredito)
        logging.info("EJECUTANDO PROSPECCION")
        logging.debug(validarIdentidad(cedula=identidad, idCredito=idCredito, head=head))
        obtenerCiudadExpedicion(identidad=identidad)
        sleep(20)
        logging.info("COMPLETANDO CLIENTE")
        logging.debug(completarCliente(idSimulacion=idSimulacion, head=head, dt=data))
        obtenerCiudadExpedicion(identidad=identidad)
        sleep(20)
        logging.info("FINALIZANDO PROSPECCION")
        logging.debug(notifyCompletion(idCredito=idCredito, head=head))
        # sleep(10)
        # logging.info("EJECUTANDO DATOS ADICIONALES CLIENTE")
        # logging.debug(basicData(idCredito=idCredito, head=head, dt=data))
        # sleep(1)
        # logging.debug(additionalData(idCredito=idCredito, head=head, dt=data))
        # sleep(1)
        # logging.debug(workData(idCredito=idCredito, head=head, dt=data))
        # obtenerCiudadExpedicion(identidad=identidad)
        # sleep(1)
        # logging.info("EJECUTANDO SIMULADOR 2")
        # logging.debug(simuladorDos(head=head, dt=data, linea=respuestaSimulador[1]))
        # sleep(2)
        # logging.debug(finalizarSimulacion(idCredito=idCredito, head=head, dt=data, linea=respuestaSimulador[1]))
        # logging.debug(skipExceptions(idCredito=idCredito, head=head))
        # obtenerCiudadExpedicion(identidad=identidad)
        # sleep(1)
        # logging.info("CONSULTANDO OBLIGACIONES FINANCIERAS")
        # sleep(1)
        # logging.debug(finantialObigations(idCredito=idCredito, head=head))
        # obtenerCiudadExpedicion(identidad=identidad)
        # logging.info("EJECUTANDO ENDEUDAMIENTO GLOBAL")
        # logging.debug(globalDebt(head=head, dt=data, idCredito=idCredito))
        # obtenerCiudadExpedicion(identidad=identidad)
        # logging.info("EJECUTANDO MEDIO DE DESEMBOLSO")
        # logging.debug(medioDesembolso(head=head, idCredito=idCredito, dt=data))
        # obtenerCiudadExpedicion(identidad=identidad)
        # sleep(1)
        # 
        # logging.info("EJECUTANDO DESICION SEGURO AP")
        # logging.debug(cambioReferencias(idCredito=idCredito, head=head))
        # logging.debug(seguroAp(idCredito=idCredito, idCliente=idCliente, head=head, dt=data))
        # obtenerCiudadExpedicion(identidad=identidad)
        # logging.info("EJECUTANDO REGISTRO DE REFERENCIAS")
        # logging.debug(referencias(idCredito=idCredito, head=head))
        # obtenerCiudadExpedicion(identidad=identidad)
        # logging.info("EJECUTANDO SEGURO DE VIDA")
        # logging.debug(seguroVida(idCredito=idCredito, head=head))
        # obtenerCiudadExpedicion(identidad=identidad)
        # logging.info("EJECUTANDO PEPS Y OPERACIONES INTERNACIONALES")
        # logging.debug(crearPeps(idCredito=idCredito, head=head))
        # logging.debug(grabarIo(idCredito=idCredito, head=head))
        # obtenerCiudadExpedicion(identidad=identidad)
        # logging.info("EJECUTANDO FINALIZACION CREDITO")
        # logging.debug(comenzarFirmas(idCliente=idCliente, idCredito=idCredito, head=head))
        # logging.debug(finalizarCredito(idCredito=idCredito, head=head))
        # obtenerCiudadExpedicion(identidad=identidad)
    except requests.exceptions.HTTPError as e:
        logging.error(f"Error en la respuesta por motivo: {e}")
        cancelarCredito(idCredito=idCredito)
        logging.error(f"Credito {idCredito} cancelado con estado 'CANCELADO_POR_INCONSISTENCIAS'.")
    except Exception as e:
        logging.error(f"Error en el ciclo por motivo: {e}")
        cancelarCredito(idCredito=idCredito)
        logging.error(f"Credito {idCredito} cancelado con estado 'CANCELADO_POR_INCONSISTENCIAS'.")
    finally:
        logging.info("CICLO TERMINADO")

if __name__ == '__main__':
    main()



    # while True:
    #     try:
    #         procesos = []
    #         for i in range(1):
    #             proceso = MP.Process(target=main)
    #             procesos.append(proceso)
    #             proceso.start()
    #         for proceso in procesos:
    #             proceso.join()
    #     except Exception as e:
    #         logging.error(f"Error en el en el ciclo: {e}")
    #         sleep(random.randint(1, 6))
    #     finally:
    #         sleep(random.randint(1, 6))
    #         continue


    # while True:
    #     try:
    #         sleep(random.randint(2, 5))
    #         main()
    #         sleep(random.randint(5, 10))
    #     except Exception as e:
    #         logging.error(f"Error en el en el ciclo: {e}")
    #     finally:
    #         continue

    # procesos = []
    # pro = 1
    # while True:
    #     try:
    #         for i in range(pro):
    #             proceso = MP.Process(target=main)
    #             procesos.append(proceso)
    #             proceso.start()
    #             logging.info(f"Procesos ejecutandose: {pro}")
    #             # pro += 1
    #         for proceso in procesos:
    #             proceso.join()
    #     except ValueError as e:
    #         logging.error(f"Error en el ciclo: {e}")
    #         time.sleep(5)
    #         continue

