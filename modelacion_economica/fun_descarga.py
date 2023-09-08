
import pandas as pd
import numpy as np
import requests
import json
import warnings
from numpy import nan

"""
---------------------------------------
Funciones contenidas en este archivo:

1. descargar_banxico(serie,fecha_inicio,fecha_fin,token=token_1,es_oportuno=False)
2. descargar_imf(serie,fecha_inicio,fecha_fin,paises='All')
    2.1. busqueda_glosario_imf(palabra_clave)
3. descargar_inegi(serie,fecha_inicio,fecha_fin,TOKEN=token_11)


"""

"""
---------------------------------------
FUNCIÓN PARA DESCARGAR DATOS DE BANXICO
---------------------------------------
---------------------------------------
"""
#El token nuevo se puede generar en la siguiente liga: https://www.banxico.org.mx/SieAPIRest/service/v1/token
token_1='82908162e488cf6a1e53620862cd2d9fa1181ba5a78882ffeb5d29320a19a145'

def descargar_banxico(serie,fecha_inicio,fecha_fin,token=token_1,es_oportuno=False):
    #Donde: 
    # serie: el identificador o identificadores que tiene Banxico para cada serie de tiempo en su sistema de información
    #       las series se pueden consultar en la siguiente liga: https://www.banxico.org.mx/SieAPIRest/service/v1/doc/catalogoSeries
    # fecha_inicio: fecha aaaa-mm-dd en la que se quiere iniciar la consulta
    # fecha_fin: fecha aaaa-mm-dd en la que se quiere concluir la consulta
    # token: el token generado por la API de Banxico para acceder

    if es_oportuno==True:
        url='https://www.banxico.org.mx/SieAPIRest/service/v1/series/'+serie+'/datos/oportuno?token='+token
    else:
        url='https://www.banxico.org.mx/SieAPIRest/service/v1/series/'+serie+'/datos/'+fecha_inicio+'/'+fecha_fin+'?token='+token
    headers = {'Token':token}
    response = requests.get(url,headers=headers)
    status=response.status_code
    raw_data = response.json()
    T=np.shape(serie.split(","))[0]
    info={'fecha':pd.DataFrame(raw_data['bmx']['series'][0]['datos'])['fecha']}

    for i in range(T):
        titulo=raw_data['bmx']['series'][i]['titulo']
        
        data=raw_data['bmx']['series'][i]['datos']
        
        df=pd.DataFrame(data)
        df['dato'] = df['dato'].apply(lambda x:float(x))
        info[titulo]=df['dato']
    info=pd.DataFrame(info)
    info.set_index('fecha',inplace=True)

    return info

"""
------------------------------------
FUNCIÓN PARA DESCARGAR DATOS DEL FMI
------------------------------------
------------------------------------
"""

def descargar_imf(serie,fecha_inicio,fecha_fin,paises='All'):
    """
    Esta función busca el indicador "serie" en la API del Fondo Monetario internacional

    Donde:
    - serie: identificador del FMI para el indicador
            Para conocer los identificadores del FMI, favor de consultar la siguiente liga: 'https://www.imf.org/external/datamapper/api/v1/indicators'
            o bien usar la función glosario_imf() aquí contenida
    - fecha inicio: año de inicio de la consulta en formato aaaa
    - fecha fin: año de fin de la consulta en formato aaaa

    """
    fecha_inicio=int(fecha_inicio)
    fecha_fin=int(fecha_fin)
    periodos=list(range(fecha_inicio,fecha_fin+1,1))
    periodos=str(periodos).strip("[]").replace(" ","")
    url1='https://www.imf.org/external/datamapper/api/v1/'+serie+'?periods='+periodos
    response = requests.get(url1)
    status=response.status_code
    raw_data = response.json()
    titulo=raw_data['values'].keys()
    valores=raw_data['values'][serie]
    return pd.DataFrame(valores)

def busqueda_glosario_imf(palabra_clave):
    """
    Esta función busca en el catálogo del FMI los indicadores relacionados con la palabra clave y sus respectivos identificadores
    
    Donde:
    - palabra_clave: la palabra a buscar en el catálogo de indicadores del FMI.

    """
    url_indic='https://www.imf.org/external/datamapper/api/v1/indicators'
    response = requests.get(url_indic)
    status=response.status_code
    raw = response.json()
    T=2
    glosario={}
    for i in raw['indicators'].keys():
        titulos=i
        desc1=raw['indicators'][i]['label']
        glosario.update({i:desc1})
    glosario={key: value.lower() for key, value in glosario.items() if value is not None}
    busqueda={}
    for key,val in glosario.items():
        if palabra_clave.lower() in val:
            busqueda.update({key:val})
    return busqueda
"""
--------------------------------------
FUNCIÓN PARA DESCARGAR DATOS DEL INEGI
--------------------------------------
--------------------------------------
"""

"""
Estas primeras funciones son preliminares que alimentan la función de descarga, provistas por el INEGI desde su página
"""

token_11='8f108d9b-a840-3d04-f180-25d11dd88a7a'

class INEGI_BI:
    def __init__(self, token):
        self.__token = token 
        self.__url_base = 'https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/'
        self.__url_indicador =  self.__url_base + 'INDICATOR/'
        self._indicadores = list() 
        self._bi = list() 
        self._columnas = list() 
        self.__clave_entidad = None

    def __call_api_request(self, url_api):
        requests_result = requests.get(url_api, headers={"User-Agent":self.__token})
        try:
            assert requests_result.status_code == 200, 'Favor de revisar sus parametros o token asignado, ya que no se encontró información.'
            data_serie = json.loads(requests_result.text)
            return data_serie
        except requests.exceptions.Timeout:
            warnings.warn('El tiempo de consulta se ha agotado. Favor de intentar mas tarde.')
        except requests.exceptions.TooManyRedirects:
                warnings.warn('Fallo inesperado. Favor de intentar mas tarde.')
        except requests.exceptions.RequestException as e:
                warnings.warn('Error. favor de reportar a: .')
            #raise SystemExit(e)

    def __busca_bi(self, indicador):
        if len(indicador) < 10: 
            return 'BIE'
        else: 
            return 'BISE'

    def __datos_json_api(self, indicador, bi):
        bi = self.__busca_bi(indicador)
        url_api = '{}{}/es/{}/false/{}/2.0/{}?type=json'.format(self.__url_indicador, indicador,  self.__clave_entidad, bi, str(self.__token))
        datos = self.__call_api_request(url_api)
        return datos['Series'][0], bi

    def __json_a_df(self, datos, bi):
        serie = datos.pop('OBSERVATIONS')

        obs_totales = len(serie)
        dic = {'periodo':[serie[i]['TIME_PERIOD'] for i in range(obs_totales)],
                'valor':[float(serie[i]['OBS_VALUE']) if serie[i]['OBS_VALUE'] is not None else nan for i in range(obs_totales)]}
        df = pd.DataFrame.from_dict(dic)
        
        frecuencia = datos['FREQ']
        #factor, period = self.__frecuancias_dict[bi].get(frecuencia)
        df.set_index(df.periodo,inplace=True, drop=True)
        df = df.drop(['periodo'],axis=1)  
        datos['BI'] = bi
        meta = pd.DataFrame.from_dict(datos, orient='index', columns=['valor'])
        return df, meta

    def __definir_cve_ent(self, entidad):
        cve_base = '0700'
        if entidad == '00': 
            self.__clave_entidad = cve_base
            return
        if len(entidad[2:5]) == 0: 
            self.__clave_entidad = '{}00{}'.format(cve_base, entidad[:2])
        else: 
            self.__clave_entidad = '{}00{}0{}'.format(cve_base, entidad[:2], entidad[2:5])
            
    def _consulta(self, inicio, fin, bi, metadatos):
        if isinstance(self._indicadores, str): self._indicadores = [self._indicadores]
        if isinstance(self._bi, str): self._bi = [self._bi]
        if isinstance(self._columnas, str): self._columnas = [self._indicadores]
        
        lista_df = list()
        meta_dfs = list()
        
        for i in range(len(self._indicadores)):
            indicador = self._indicadores[i]
            data, bi = self. __datos_json_api(indicador, bi)
            df, meta = self.__json_a_df(data, bi)
            if bi == 'BIE': 
                df = df[::-1]
            lista_df.append(df)
            meta_dfs.append(meta)
        df = pd.concat(lista_df,axis=1)
        meta = pd.concat(meta_dfs, axis=1)

        try: 
            df.columns = self._columnas
            meta.columns = self._columnas
        except: 
            warnings.warn('Los nombres no coinciden con el número de indicadores')
            df.columns = self._indicadores
            meta.columns = self._indicadores

        if metadatos is False: 
            return df[inicio:fin] 
        else: 
            return df[inicio:fin], meta

    def obtener_datos(self, indicadores: 'str|list', clave_area: str = '00', inicio: str = None, 
                        fin: str = None, bi: str = None, metadatos: bool = False):
        self._indicadores = indicadores
        self._columnas = indicadores
        #if nombres is not None: 
        #self._columnas = nombres
        self.__definir_cve_ent(clave_area)
        return self._consulta(inicio, fin, bi, metadatos)

    # Metadatos
    def _consultar_catalogo(self, clave, id, bi):
        url_api = '{}{}/{}/es/{}/2.0/{}/?type=json'.format(self.__url_base, clave, id, bi, self.__token)
        request_api = requests.get(url_api)
        datos = json.loads(request_api.text)
        return pd.DataFrame(datos['CODE'])

    def catalogo_indicadores(self, bi: str, indicador: str = None):
        if indicador is None: indicador = 'null'
        return self._consultar_catalogo('CL_INDICATOR', indicador, bi)

    def consulta_metadatos(self, metadatos: 'DataFrame|dict'):
        if isinstance(metadatos, dict): metadatos = pd.DataFrame.from_dict(dict)
        n_df = metadatos.copy(deep=True)
        for col in metadatos.columns:
            bi = metadatos.loc['BI',col]
            for idx in metadatos.index: 
                if idx in ['LASTUPDATE','BI']: continue
                id = metadatos.loc[idx,col]
                if id is None or len(id) == 0: continue
                if idx == 'INDICADOR': 
                    clave = 'CL_INDICATOR'
                else: 
                    clave = 'CL_{}'.format(idx)
                try:
                    desc = self._consultar_catalogo(clave, id, bi)
                    n_df.loc[idx,col] = desc.iloc[0,1]
                except: 
                    n_df.loc[idx,col] = 'La información no existe'
        return n_df

def descargar_inegi(serie,fecha_inicio,fecha_fin,TOKEN=token_11):
    """
    Función para descargar las series del INEGI, una por una

    Donde:

    - serie: identificador que le da INEGI a la serie
    - fecha inicio: fecha aaaa/mm en la que se quiere iniciar la consulta
    - fecha fin: fecha aaaa/mm en la que se quiere concluir la consulta
    """
    API_INEGI_BI= INEGI_BI(TOKEN)
    datos,metadatos1 = API_INEGI_BI.obtener_datos(indicadores = "735879",
    clave_area = '0700',
    inicio = fecha_inicio, 
    fin = fecha_fin,
    metadatos = True)
    nombre = API_INEGI_BI.consulta_metadatos(metadatos1).values[0][0]
    return datos.set_axis([nombre],axis=1)