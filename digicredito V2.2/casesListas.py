import requests
import crdncls as cr
import random
import psycopg2
import datetime
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - Proceso: %(process)s - %(levelname)s - %(message)s')

cr.token
heads = open("./noms.txt", "r")
head = {'Authorization': 'Bearer {}'.format(heads.read())}

""" SE CREA EL CODIGO EN BLOQUES ENFOCANDOSE EN EL FACIL MANTENIMIENTO Y EN LA MODULARIDAD, 
EN CASO DE QUE LOS EP TENGAN UN CAMBIO O SEAN REMOVIDOS NO AFECTE EL RESTO DEL CODIGO DE 
ESTA FORMA SE PUEDE ENCONTRAR FACILMENTE EL ERROR"""

load = {
        "genero": "", 
        "departamento": "", 
        "nivel_educativo": "", 
        "id_pagaduria": 0, 
        "fecha_nacimiento": "", 
        "tipo_contrato": "", 
        "nombre_pagaduria": "", 
        "total_activos": "", 
        "descuentos_nomina": ""
        }

def dataSimulador():
    instancia = 'instancia2'
    heads = cr.token()
    head = {'Authorization': 'Bearer {}'.format(heads)}

    #DATA OBJETO
    data = {}

    # DATOS DEL CLIENTE
    conexcion = psycopg2.connect(user=cr.user, password=cr.password, 
                                host=cr.hostApp, 
                                port=cr.port, database=cr.cifin) 
    cursor = conexcion.cursor()
    cursor.execute('select "IdentificationNumber" from "HistoryCifin" order by "CreationDate" desc limit 1000;')
    cedula = cursor.fetchall()
    cursor.close()
    conexcion.close()
    # cedulas =[13057386, 4450156, 14249984, 73154449, 36146670, 12978372,  4861654,  27002500, 57403081, 40771708, 39528882, 14440686, 10156597, 5590875]
    # cedulas =[]
    # for i in cedula:
    #     if i is not cedulas:
    #         cedulas.append(i)
    # random.shuffle(cedulas)

    ced = random.choice(cedula)
    # ced = 24310670
    conexcion = psycopg2.connect(user=cr.user, password=cr.password, 
                                host=cr.host, 
                                port=cr.port, database=cr.database) 
    cursor = conexcion.cursor()
    cursor.execute(f"select primer_nombre, segundo_nombre, primer_apellido, segundo_apellido, identificacion, email, telefono_celular  from cliente where identificacion = '{ced[0]}';")
    # cursor.execute(f"select primer_nombre, segundo_nombre, primer_apellido, segundo_apellido, identificacion, email, telefono_celular  from cliente where identificacion = '{ced}';")
    cliente = cursor.fetchall()
    cursor.close()
    conexcion.close()
    

    data["nombre1"] = cliente[0][0]
    data["nombre2"] = cliente[0][1]
    data["apellido1"] = cliente[0][2]
    data["apellido2"] = cliente[0][3]
    identificacion = cliente[0][4]
    data["identificacion"] = identificacion
    data["email"] = cliente[0][5]
    data["celular"] = cliente[0][6]

    # OFICINA E ID DE OFICINA
    url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/asesores/2895/regiones/oficinas')
    response = requests.get(url, headers=head)
    res = random.randrange(0 , len(response.json()))
    data["oficina"] = response.json()[res]['nombre']
    idOffice = response.json()[res]['id']
    data["idOficina"] = idOffice

    # DEPARTAMENTO
    iDepartamento = "CO>Indefinido"
    while iDepartamento == "CO>Indefinido":
        url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/departamentos')
        response = requests.get(url, headers=head)
        res = random.randrange(0 , len(response.json()))
        departamento = response.json()[res]['nombre']
        iDepartamento = response.json()[res]['id']
        data["nDepartamento"] = departamento
        data["departamento"] = iDepartamento

    #CIUDAD DE EXPEDICION
    url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/departamentos/{iDepartamento}/ciudades')
    response = requests.get(url, headers=head)
    res = random.randrange(0 , len(response.json()))
    data["nCiudad"] = response.json()[res]['nombre']
    data["ciudad"] = response.json()[res]['id'] 

    #PAGADURIA
    dataRet = retanqueo(iden = identificacion)
    if dataRet[0]['tieneRetanqueo'] == True:
        data["tieneRetanqueo"] = True
        pagaduria = dataRet[1]["pagaduria"]
        data["pagaduria"] = pagaduria
        idPagaduria = dataRet[1]["idPagaduria"]
        data["idPagaduria"] = idPagaduria
        dataRet.pop(0)
        creditoPadres = []
        saldoRecojer = 0
        for i in dataRet:
            creditoPadre = i["creditoPadre"]
            saldoAldia = i["saldoAlDia"]
            creditoPadres.append(creditoPadre)
            saldoRecojer = saldoRecojer + saldoAldia
        data["creditosPadres"] = creditoPadres
        data["saldoRecojer"] = saldoRecojer
    else:
        url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/pagadurias')
        response = requests.get(url, headers=head)
        res = random.randrange(0 , len(response.json()))
        data["tieneRetanqueo"] = False
        pagaduria = response.json()[res]['nombre']
        data["pagaduria"] = pagaduria
        idPagaduria = response.json()[res]['id']
        data["idPagaduria"] = idPagaduria

    # ACTIVIDAD ECONOMICA
    url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/actividadeseconomicas/{idPagaduria}/pagaduria')
    response = requests.get(url, headers=head)
    res = random.randrange(len(response.json()))
    actEconomica = response.json()[res]['id']
    data["actividadEconomica"] = actEconomica

    # TIPO DE CONTRATO
    url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/clients/type-contract/{actEconomica}')
    response = requests.get(url, headers=head)
    res = random.randrange(0 , len(response.json()))
    tipoContrato = response.json()[res]['nombre']
    data["tipoContrato"] = tipoContrato

    # MONTO SOLICITADO, PLAZO, TOTAL INGRESOS, TIENE COMPRA DESCUENTOS DE NOMINA Y DESCUENTOS DE LEY
    montoSolicitado = random.randrange(2500000, 10000000, 10000)
    data["montoSolicitado"] = montoSolicitado
    tieneCompra = random.choice([True,False])
    data["conCompra"] = tieneCompra
    if tieneCompra == True:
        compra = random.randrange(10000 , montoSolicitado-500000, 1000)
        data["compraCartera"] = compra
    elif data["tieneRetanqueo"] == True:
        data["montoSolicitado"] =  montoSolicitado + saldoRecojer
    elif data["tieneRetanqueo"] and tieneCompra == True:     
        data["montoSolicitado"] = montoSolicitado + compra + saldoRecojer
    plazo = random.randrange(12 , 144)
    data["plazo"] = plazo
    totalIgresos = random.randrange(4500000 , 8000000, 10000)
    data["totalIngresos"] = totalIgresos
    descNomina = random.randrange(10000 , 500000, 1000)
    data["descuentosNomina"] = descNomina
    descLey  = random.randrange(34000 , 500000, 1000)
    data["descuentosLey"] = descLey

    # NIVEL DE EDUCACION 
    url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/clients/education-levels')
    response = requests.get(url, headers=head)
    res = random.randrange(0 , len(response.json()))
    nivEducacion = response.json()[res]['idLegado']
    idNivelEducacion = response.json()[res]['id']
    data["idNivelEducacion"] = idNivelEducacion
    data["nivelEducacion"] = nivEducacion

    # ESTRATO
    url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/clients/stratums')
    response = requests.get(url, headers=head)
    res = random.randrange(0 , len(response.json()))
    idStrato = response.json()[res]['id']
    strato = response.json()[res]['idLegado']
    nomEstrato = response.json()[res]['nombre']
    data["idStrato"] = idStrato
    data["nomEstrato"] = nomEstrato
    data["estrato"] = strato

    # TIPO DE VIVIENDA
    tipoVivienda = ["PROPIA", "ARRIENDO", "PROPIA"]
    res = random.randrange(len(tipoVivienda))
    data["tipoVivienda"] = tipoVivienda[res]

    # TOTAL DE ACTIVOS
    totalActivos = random.randrange(0, 20000000, 1000)
    data["totalActivos"] = totalActivos

    # GENERO
    genero = random.randrange(0, 1)
    if genero == 0:
        gen = "M"
    else:
        gen = "F"
    data["genero"] = gen

    # FECHA DE NACIMIENTO
    hoy = datetime.datetime.now()
    # cambiar  a 83 para realizar pruebas de pagaduria vs edad
    fechaInicio = hoy - datetime.timedelta(days=365*60)
    fechaFin = hoy - datetime.timedelta(days=365*23)
    fechaNacimiento = fechaInicio + datetime.timedelta(days=random.randint(0, (fechaFin - fechaInicio).days))
    fechaExpedicion = fechaNacimiento + datetime.timedelta(days=365*20)
    fechaIngreso = hoy - datetime.timedelta(days=365)
    data["fechaNacimiento"] = fechaNacimiento.strftime("%Y-%m-%d")
    data["fechaExpedicion"] = fechaExpedicion.strftime("%Y-%m-%d")
    data["fechaIngreso"] = fechaIngreso.strftime("%Y-%m-%d")

    # CLASE DE VIVIENDA
    url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/clients/residence-types')
    response = requests.get(url, headers=head)
    res = random.randrange(0 , len(response.json()))
    tipoRecidencia = response.json()[res]['id']
    data["tipoRecidencia"] = tipoRecidencia

    # POSICION EN EL HOGAR
    url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/clients/relationships-head-home')
    response = requests.get(url, headers=head)
    res = random.randrange(0 , len(response.json()))
    posicionHogar = response.json()[res]['id']
    data["posicionHogar"] = posicionHogar

    # ENTIDAD BANCARIA
    url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/bank-entities')
    response = requests.get(url, headers=head)
    res = random.randrange(0 , len(response.json()))
    banco = response.json()[res]
    data["banco"] = banco

    # PLAN SEGURO OPCIONAL
    url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/seguroap/paquetes')
    response = requests.get(url, headers=head)
    res = random.randrange(0 , len(response.json()))
    plan = response.json()['planes'][res]['id']
    data["plan"] = plan

    # TASAS VERSIONAMIENTO
    url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/consult-rates/{idPagaduria}/{iDepartamento}')
    response = requests.get(url, headers=head)
    res = random.randrange(0 , len(response.json()))
    tasa = response.json()[res]['id']
    data["tasa"] = tasa

    # SI ES PRICING LA OFICINA PUEDA GENERAL LOS DATOS REQUERIDOS PARA EL CASO DE PRUEBA
    url =(f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/is-office-model-pricing/{idOffice}')
    response = requests.get(url, headers=head)
    isPricing = response.json()
    data["isPricing"] = isPricing
    if isPricing == True:
            load['genero'] = gen
            load['departamento'] = departamento
            load['nivel_educativo'] = nivEducacion
            load['id_pagaduria'] = idPagaduria
            load['fecha_nacimiento'] = fechaNacimiento.strftime("%Y-%m-%d")
            load['tipo_contrato'] = tipoContrato
            load['nombre_pagaduria'] = pagaduria
            load['total_activos'] = totalActivos
            load['descuentos_nomina'] = descNomina
            url = (f'https://development.excelcredit.co/{instancia}/api/excelcredit/onboardingservices/get-product-model-pricing')
            responses = requests.post(url, headers=head, json=load)
            dataPricing = responses.json()[0]
            data["dataPricing"] = dataPricing
    return data


def retanqueo(iden):
    heads = cr.token()
    head = {f'Authorization': 'Bearer {}'.format(heads)}
    listaRetanqueo = []
    # DATOS DEL CLIENTE PARA BUSCAR UN RETANQUEO
    conexcion = psycopg2.connect(user=cr.user, password=cr.password, 
                                host=cr.host, 
                                port=cr.port, database=cr.database) 
    cursor = conexcion.cursor() 
    cursor.execute(f"select cf.id_pagaduria FROM (SELECT * FROM obtener_creditos_fondeados(current_date)) cf INNER join cliente cl ON cl.id = cf.id_cliente where cf.id_fondeador  not IN (0) and cl.identificacion = '{iden}';")
    idpag = cursor.fetchall()
    if idpag == []:
        logging.info(f"{iden}, NO TIENE CREDITOS A RETANQUEAR")
        listaRetanqueo.append({"tieneRetanqueo": False})
    else:
        pag = idpag[0][0]
        body = {"tipoIdentificacion": "CC","identificacion": iden}
        url = (f'https://development.excelcredit.co/instancia2/api/excelcredit/onboardingservices/clientes/creditos-activos/{pag}')
        response = requests.post(url, headers=head, json=body)
        dis = len(response.json())
        if dis == 0:
            logging.info(f"{iden}, NO TIENE CREDITOS A RETANQUEAR")
            listaRetanqueo.append({"tieneRetanqueo": False})
        else:
            logging.info(f"{iden}, TIENE CREDITOS A RETANQUEAR")

            retanq = []
            listaRetanqueo.append({"tieneRetanqueo": True})
            for i in response.json():
                idCredito = i['id']
                idPagaduria = i['idPagaduria']
                pagaduria = i['pagaduria']['nombre']
                saldoAlDia = i['saldoAlDia']
                listaRetanqueo.append({"creditoPadre": idCredito, "idPagaduria": idPagaduria, "pagaduria": pagaduria, "saldoAlDia": saldoAlDia})
    return(listaRetanqueo)
            
# print(retanqueo(iden=36489132))
# print(dataSimulador())

# while True:
#     logging.info(dataSimulador())
#     print("GENERACION DE DATA COMPLETADA")