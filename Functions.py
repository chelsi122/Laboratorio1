# LABORATORIO 1 BARRAGÁN, SEDANO, ZUÑIGA

import pandas as pd
from os import listdir, path
from os.path import isfile, join
import yfinance as yf
import numpy as np

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.expand_frame_repr', False)

# --------------- TRATAMIENTO DE LOS DATOS -------------------
def f_files(path):
    '''
    Obtener la lista de los nombres de los archivos para su tratamiento
    '''
    files = [f[8:-4] for f in listdir(path) if isfile(join(path, f))]
    files = ['NAFTRAC_' + i.strftime('%Y%m%d') for i in sorted(pd.to_datetime(files))]
    return files

def f_datafiles(files):
    '''
    Se crea un diccionario que guarda la información proveniente de los datos descrgados
    con anterioridad.
    '''

    data_files = {}
    for i in files:
        # Lee cada archivo
        data = pd.read_csv('files/' + i + '.csv', skiprows=2, header=None)
        # Listado de los nombres por columnas
        data.columns = list(data.iloc[0, :])
        # Elimina NaN's
        data = data.loc[:, pd.notnull(data.columns)]
        data = data.iloc[1:-1].reset_index(drop=True, inplace=False)
        # Eliminar , y *
        data['Precio'] = [i.replace(',', '') for i in data['Precio']]
        data['Ticker'] = [i.replace('*', '') for i in data['Ticker']]
        # Pone columnas en el orden que se necesita
        data = data.astype({'Ticker': str, 'Nombre': str, 'Peso (%)': float, 'Precio': float})
        # Peso en formato de porcentaje
        data['Peso(%)'] = data['Peso (%)'] / 100
        data_files[i] = data

    return data_files

def f_dates(files):
    '''
    Función que regresa las fechas de los archivos  de los activos de ETF.
    '''
    dates = [j.strftime('%Y-%m-%d') for j in sorted([pd.to_datetime(i[8:]).date() for i in files])]
    return dates


def f_tickers(files, data_files):
    '''
    Modifica los nombres de los activos para poder encontrarlos en la BMV,
    y elimina los activos no necesarios para el análisis.
    '''
    tickers = []
    for i in files:
        tickers_a = list(data_files[i]['Ticker'])
        [tickers.append(i + '.MX') for i in tickers_a]
    tickers = np.unique(tickers).tolist()

    # Actualiza el nombre de los tickers que ya no tienen el mismo nombre
    tickers = [i.replace('GFREGIOO.MX', 'RA.MX') for i in tickers]
    tickers = [i.replace('MEXCHEM.MX', 'ORBIA.MX') for i in tickers]
    tickers = [i.replace('LIVEPOLC.1.MX', 'LIVEPOLC-1.MX') for i in tickers]
    tickers = [i.replace('SITESB.1', 'SITESB-1') for i in tickers]

    # Eliminación de activos no necesarios
    [tickers.remove(i) for i in
     ['KOFL.MX', 'KOFUBL.MX', 'USD.MX', 'BSMXB.MX', 'NMKA.MX', 'MXN.MX']]

    return tickers


def f_down_data(tickers):
    '''
    Función que regresa los precios de los activos de Yahoo Finance,
    conforme a las fechas ingresadas.
    '''

    # Descarga de datos
    data = yf.download(tickers, start="2018-01-30", actions=False,
                       group_by="close", interval='1d', auto_adjust=False, prepost=False, threads=True)

    # DataFrame con los precios de cierre de cada activo
    data_close = pd.DataFrame({i: data[i]['Close'] for i in tickers})

    return data_close

def f_sortdates(data_close, dates):
    '''
    Función que prdena las fechas cronológicamente
    '''
    sort_dates = sorted(list(set(data_close.index.astype(str).tolist()) & set(dates)))
    return sort_dates


def f_prices(data_close, sort_dates):
    '''
    Función que regresa los precios con las fechas que se necesitan dentro del análisis
    así como con sus respectivos precios descargados.
    '''
    prices = data_close.iloc[[int(np.where(data_close.index.astype(str) == i)[0]) for i in sort_dates]]
    prices = prices.reindex(sorted(prices.columns), axis=1)
    return prices

# --------------- INVERSIÓN PASIVA -------------------
def f_posdata(act_delete, data_files, files, prices, k, c):
    '''
    Esta función elimina los activos que no son necesarios y les da el formato a los activos que
    se necesitan para encontrarlos en la BMV.

    Crea un DataFrame con una columna donde aparece el capital necesario a invertir, los
    titulos que se alcanzan a comprar, se agrega la postura y las comisiones que nos cobrarían.
    '''
    posdata = data_files[files[0]].copy().sort_values('Ticker')[['Ticker', 'Peso (%)']]

    i_activos = list(posdata[posdata['Ticker'].isin(act_delete)].index)
    posdata.drop(i_activos, inplace=True)
    posdata.reset_index(inplace=True, drop=True)
    posdata['Ticker'] = posdata['Ticker'] + '.MX'

    # Actualiza el nombre de los Tickers que ya no tienen el mismo nombre
    posdata['Ticker'] = posdata['Ticker'].replace('LIVEPOLC.1.MX', 'LIVEPOLC-1.MX')
    posdata['Ticker'] = posdata['Ticker'].replace('MEXCHEM.MX', 'ORBIA.MX')
    posdata['Ticker'] = posdata['Ticker'].replace('GFREGIOO.MX', 'RA.MX')
    posdata['Ticker'] = posdata['Ticker'].replace('SITESB.1', 'SITESB-1')

    # Obtiene el histórico correspondiente
    posdata['Precios'] = (np.array([prices.iloc[0, prices.columns.to_list().index(i)] for i in posdata['Ticker']]))
    posdata['Peso (%)'] = posdata['Peso (%)'] / 100
    posdata['Titulos'] = np.floor((k * posdata['Peso (%)']) / (posdata['Precios'] + (posdata['Precios'] * c)))
    posdata['Capital'] = np.round(posdata['Titulos'] * (posdata['Precios'] + (posdata['Precios'] * c)), 2)
    posdata['Postura'] = np.round(posdata['Precios'] * posdata['Titulos'], 2)
    posdata['Comisiones'] = np.round(posdata['Precios'] * c * posdata['Titulos'], 2)

    return posdata


def f_passive_inv(sort_dates, posdata, prices, cash, passive_inv):
    '''
    Regresa el capital que tenemos invertir en los meses de análisis.
    '''
    for i in range(len(sort_dates)):
        # Volvemos a sobreponer los datos para poder sacar otra vez el cash
        posdata['Precios'] = (
            np.array([prices.iloc[i, prices.columns.to_list().index(j)] for j in posdata['Ticker']]))
        posdata['Postura'] = np.round(posdata['Precios'] * posdata['Titulos'], 2)
        passive_inv['Capital'].append(np.round(posdata['Postura'].sum(), 2) + cash)
        passive_inv['Dates'].append(sort_dates[i])

    return passive_inv


def f_passive(passive_inv):
    """
    Calcula el rendimiento y el rendimiento acumulado de nuestra inversión en los periodos de análisis.
    """
    df_passive = pd.DataFrame(
        {"Dates": passive_inv['Dates'], "Capital": passive_inv['Capital'], "Rendimiento": 0,
         "Rendimiento Acumulado": 0})
    for i in range(1, len(df_passive)):
        df_passive.loc[i, "Rendimiento"] = (df_passive.loc[i, 'Capital'] - df_passive.loc[i - 1, 'Capital']) / \
                                          df_passive.loc[i - 1, 'Capital']
        df_passive.loc[i, "Rendimiento Acumulado"] = df_passive.loc[i, 'Rendimiento'] + df_passive.loc[
            i - 1, 'Rendimiento Acumulado']

    return df_passive

def portfolios(prices):
    """
    Función que regresa el portafolio óptimo para la inversión,
    obteniendo el radio de Sharpe
    """
    # Obtener rendimientos logaritmicos mensuales utilizando propiedad de divison de log
    prices_pre = np.log(prices).diff()
    # Establecer periodo prepandemia
    prices1 = prices_pre.loc[prices_pre.index <= "2020-02-28", :]
    matriz_cov = prices1.cov() * np.sqrt(12)
    # Definir el numero de portafolios para realizar la frontera eficiente
    p_ret = []
    p_vol = []
    p_weights = []
    p_sharpe = []
    num_assets = len(prices.columns)
    num_portfolios = 100
    indv_returns = prices1.mean()

    for portfolio in range(num_portfolios):
        weights = np.random.random(num_assets)
        weights = weights / np.sum(weights)
        p_weights.append(weights)
        returns = np.dot(weights, indv_returns * 12) - .0425
        p_ret.append(returns)

        variance = weights.T @ matriz_cov @ weights
        stand_dev = np.sqrt(variance)
        p_vol.append(stand_dev)

        sharpe_r = returns / stand_dev
        p_sharpe.append(sharpe_r)

    data = {'Returns': p_ret, 'Volatility': p_vol, 'Sharpe': p_sharpe}

    for counter, symbol in enumerate(prices1.columns.tolist()):
        data[symbol + ' weight'] = [w[counter] for w in p_weights]
    portfolios = pd.DataFrame(data)

    return portfolios

def portfolio_1(tickers, prices_post1, prices, posdata, pesos1, c, capital):
    # Creacion del portafolio inicial
    portfolio_1 = pd.DataFrame()
    portfolio_1["Ticker"] = tickers
    portfolio_1['Precios'] = (
        np.array([prices_post1.iloc[0, prices.columns.to_list().index(i)] for i in posdata['Ticker']]))
    portfolio_1["Peso"] = pesos1
    portfolio_1['Postura'] = np.round(capital * portfolio_1["Peso"], 2)
    portfolio_1['Titulos'] = np.floor((portfolio_1["Postura"] / portfolio_1["Precios"]))
    portfolio_1['Comisiones'] = np.round(portfolio_1['Precios'] * c * portfolio_1['Titulos'], 2)
    portfolio_1 = portfolio_1.set_index("Ticker")
    return portfolio_1

def new_port(prices_post, tickers, prices, portfolio_1, c):
    titulos_ant = []
    for i in range(2):
        word = pd.DataFrame(prices_post.iloc[i, :])
        word.columns = ["Porcentaje"]
        prices_down = word[word.Porcentaje <= -.05]
        down = list(word.index.values)
        prices_up = word[word.Porcentaje >= .05]
        up = list(word.index.values)

        new_titulos = []
        new_portfolio = pd.DataFrame()
        new_portfolio["Ticker"] = tickers
        new_portfolio = new_portfolio.set_index("Ticker")
        new_portfolio["Precio"] = prices.iloc[26 + i, :].to_list()  # Periodo de pandemia empieza en iloc 26

        if i == 0:
            new_portfolio["Titulos anteriores"] = portfolio_1.loc[:, "Titulos"].to_list()
        else:
            new_portfolio["Titulos anteriores"] = titulos_ant.to_list()
        for ticker in tickers:
            if ticker in down:
                n_titulos = new_portfolio.loc[ticker, "Titulos anteriores"] * .975
            else:
                n_titulos = new_portfolio.loc[ticker, "Titulos anteriores"]
            new_titulos.append(n_titulos)

        new_portfolio["Nuevos Titulos"] = np.floor(new_titulos)
        titulos_ant = new_portfolio["Nuevos Titulos"]
        new_portfolio["Nuevo Valor"] = new_portfolio["Nuevos Titulos"] * new_portfolio["Precio"]
        new_portfolio["Valor Venta"] = np.round(
            (new_portfolio["Titulos anteriores"] - new_portfolio["Nuevos Titulos"]) * new_portfolio["Precio"], 2)
        new_portfolio["Comisiones venta"] = new_portfolio["Valor Venta"] * c
    return new_portfolio

def df_activa(prices_post1, valor_portafolio, lista):
    # Verificación de avance
    df_activa = pd.DataFrame()
    df_activa["timestamp"] = lista
    valor_portafolio.insert(0, 1000000)
    df_activa["capital"] = valor_portafolio
    df_activa["rendimiento"] = df_activa.capital.diff() / df_activa.capital
    df_activa["rendimiento_acumulado"] = df_activa["rendimiento"].cumsum()
    return df_activa

def df_operaciones(lista2, acciones_compra, acciones_venta, comisiones_compra, comisiones_venta):
    # Verificacion de avance
    df_operaciones = pd.DataFrame()
    df_operaciones["timestamp"] = lista2
    df_operaciones["titulos comprados / total operacion"] = acciones_compra
    df_operaciones["titulos vendidos / total operacion"] = acciones_venta
    df_operaciones["comisiones compra"] = comisiones_compra
    df_operaciones["comisiones venta"] = comisiones_venta
    df_operaciones["comisiones mes"] = df_operaciones["comisiones compra"] + df_operaciones["comisiones venta"]
    df_operaciones["comisiones acumuladas"] = df_operaciones["comisiones mes"].cumsum()
    return df_operaciones
