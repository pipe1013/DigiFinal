from keycloak import KeycloakOpenID



def token():
    keycloak_openid = KeycloakOpenID(server_url="https://development.excelcredit.co/auth/",
                                     client_id="cli_ms_abacus",
                                     realm_name="rei_excelcredit",
                                     client_secret_key="39cc4388-9712-4a59-9a70-c1d088220379")

    token = keycloak_openid.token("jtellez@excelcredit.co", "Suaita01")
    tkn = token['access_token']
    
    with open("./noms.txt", "w", encoding="utf-8") as f:
        f.write(tkn)
        f.close()
    return tkn

def tokenStaging():
    keycloak_openid = KeycloakOpenID(server_url="https://test.koa.co/auth/",
                                     client_id="cli_ms_abacus",
                                     realm_name="rei_koa",
                                     client_secret_key="4f4089e6-bdd8-476a-ae2f-419a200909c5")

    token = keycloak_openid.token("hmosquera@excelcredit.co", "Pru3b@s5*")
    tkn = token['access_token']
    
    with open("./noms.txt", "w", encoding="utf-8") as f:
        f.write(tkn)
        f.close()
    return tkn

# DATOS DE STAGING
hostStaging = "libranzas-staging.chimul6agbmw.us-east-1.rds.amazonaws.com"
hostAppStaging = "libranzas-microservicios-stage.chimul6agbmw.us-east-1.rds.amazonaws.com"
portStaging = "5432"
databaseStaging = "libranzas"
tokensStaging = "token"

# DATOS DE INSTANCIA
user="hmosquera" 
password="Hm0squ3r@&EC2013"
host="libranzas-preproduccion.chimul6agbmw.us-east-1.rds.amazonaws.com"
hostApp="libranzas-aplicaciones.chimul6agbmw.us-east-1.rds.amazonaws.com"
port="5432"
database="libranzas_instancia2"
tokens="token_instancia2"
cifin = "cifin_instancia2"


# token()