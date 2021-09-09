# LABORATORIO 1 BARRAGÁN, SEDANO, ZUÑIGA

import Functions as fn
# --------------- TRATAMIENTO DE LOS DATOS -------------------
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.expand_frame_repr', False)

k = 1000000
c = 0.00125

abspath = path.abspath('files')

files = fn.f_files(abspath)

data_files = fn.f_datafiles(files)

dates = fn.f_dates(files)

tickers = fn.f_tickers(files, data_files)

# --------------- INVERSIÓN PASIVA -------------------

data_close = fn.f_down_data(tickers)
data_close.head(5)

sort_dates = fn.f_sortdates(data_close, dates)

prices = fn.f_prices(data_close, sort_dates)

act_delete = ['KOFL', 'KOFUBL', 'MXN', 'USD', 'NMKA', 'BSMXB', 'SITESB.1']
posdata = fn.f_posdata(act_delete, data_files, files, prices, k, c)
posdata

cash = (1-posdata['Peso (%)'].sum())*k
cash

comision_sum = posdata['Comisiones'].sum()
comision_sum

passive_inv = {'Dates': ['2018-01-30'], 'Capital': [k]}
passive_inv = fn.f_passive_inv(sort_dates, posdata, prices, cash, passive_inv)

df_passive = fn.f_passive(passive_inv)
df_passive

# PRE PAN
df_passive_a = df_passive.loc[0:25]
df_passive_a

# DUR PAN
inv_passive_pos = {'Dates': ['2020-02-28'], 'Capital': [k]}
inv_passive_pos = fn.f_passive_inv(sort_dates[25:39], posdata, prices[25:39], cash, inv_passive_pos)
df_passive_b = fn.f_passive(inv_passive_pos)
df_passive_b

# --------------- INVERSIÓN ACTIVA -------------------

# Obtener tickers
tickers = posdata.iloc[:,0]
tickers = tickers.to_list()

# Descargar datos
data_close = fn.f_down_data(tickers)
sort_dates = fn.f_sortdates(data_close, dates)
prices = fn.f_prices(data_close, sort_dates)

# Portafolios creados para obtener el de mejor rendimiento
portfolios = fn.portfolios(prices)

# Seleccionar el portafolio con mayor sharpe
max_sharpe = portfolios.iloc[portfolios['Sharpe'].idxmax()]
max_sharpe = max_sharpe.to_list()
pesos1 = max_sharpe[3:]

# Obtener precios despues de pandemia
prices_post1 = prices.loc[prices.index >= "2020-02-28",:]
lista = prices_post1.index.values
capital = 1000000 - cash
#  Cambios porcentuales en pandemia
prices_post = prices.pct_change()
prices_post = prices_post[prices_post.index > "2020-02-28"]
lista2 = prices_post.index.values

# Se obtiene el portafolio a utilizar con los datos antes de pandemia
portfolio_1 = fn.portfolio_1(tickers, prices_post1, prices, posdata, pesos1, c, capital)
portfolio_1

# Restar comisiones
cash = cash - portfolio_1["Comisiones"].sum()
cash

# Crear columna de prices en post pandemia
prices_post1 = pd.DataFrame(prices_post.iloc[0,:])
prices_post1.columns = ["Porcentaje"]
prices_down = prices_post1[prices_post1.Porcentaje <= -.05 ]
down = list(prices_post.index.values)
prices_up = prices_post1[prices_post1.Porcentaje >= .05 ]
up = list(prices_up.index.values)

for i in range(13):
    word = pd.DataFrame(prices_post.iloc[i,:])
    word.columns = ["Porcentaje"]
    prices_down = word[word.Porcentaje <= -.05 ]
    down = list(word.index.values)
    prices_up = word[word.Porcentaje >= .05 ]
    up = list(word.index.values)

new_portfolio = fn.new_port(prices_post, tickers, prices, portfolio_1, c)
new_portfolio

titulos_ant = []
new_cash = cash
valor_portafolio = []
all_data = pd.DataFrame()
acciones_venta = []
acciones_compra = []
comisiones_venta = []
comisiones_compra = []
for i in range(13):
    # Obtencion de rebalanceos
    word = pd.DataFrame(prices_post.iloc[i, :])
    word.columns = ["Porcentaje"]
    prices_down = word[word.Porcentaje <= -.05]
    down = list(prices_down.index.values)
    prices_up = word[word.Porcentaje >= .05]
    up = list(prices_up.index.values)
    # Creación de nuevos portafolios
    new_titulos = []
    new_portfolio = pd.DataFrame()
    new_portfolio["Ticker"] = tickers
    new_portfolio = new_portfolio.set_index("Ticker")
    new_portfolio["Precio"] = prices.iloc[26 + i, :].to_list()  # Periodo de pandemia empieza en iloc 26

    if i == 0:
        new_portfolio["Titulos anteriores"] = portfolio_1.loc[:, "Titulos"].to_list()
    else:
        new_portfolio["Titulos anteriores"] = titulos_ant.to_list()

    # Venta de activos con descuento de precios
    for ticker in tickers:
        if ticker in down:
            n_titulos = new_portfolio.loc[ticker, "Titulos anteriores"] * .975
        else:
            n_titulos = new_portfolio.loc[ticker, "Titulos anteriores"]
        new_titulos.append(n_titulos)
    new_portfolio["Nuevos Titulos"] = np.floor(new_titulos)
    new_portfolio["Valor Venta"] = np.round(
        (new_portfolio["Titulos anteriores"] - new_portfolio["Nuevos Titulos"]) * new_portfolio["Precio"], 2)
    acciones_venta.append(new_portfolio["Valor Venta"].sum())
    new_portfolio["Comisiones venta"] = new_portfolio["Valor Venta"] * c
    comisiones_venta.append(new_portfolio["Comisiones venta"].sum())
    # Manejo de efectivo despues de venta
    new_cash = new_cash + new_portfolio["Valor Venta"].sum() - new_portfolio["Comisiones venta"].sum()

    # Compra de activos con aumento de precio
    valor_compra = []
    cash_buy = new_cash
    for ticker in tickers:
        if cash_buy >= 0 and ticker in up:
            n_titulos = new_portfolio.loc[ticker, "Titulos anteriores"] * 1.025
            new_portfolio.loc[ticker, "Nuevos Titulos"] = np.floor(n_titulos)
            compra = np.round(
                (new_portfolio.loc[ticker, "Titulos anteriores"] - new_portfolio.loc[ticker, "Nuevos Titulos"]) *
                new_portfolio.loc[ticker, "Precio"], 2) * -1
            if compra > cash_buy:
                compra = 0
        else:
            compra = 0
        valor_compra.append(compra)
        cash_buy = cash_buy - compra

    new_portfolio["Valor Compra"] = valor_compra
    acciones_compra.append(new_portfolio["Valor Compra"].sum())
    titulos_ant = new_portfolio["Nuevos Titulos"]
    new_portfolio["Comisiones Compra"] = new_portfolio["Valor Compra"] * -c
    comisiones_compra.append(new_portfolio["Comisiones Compra"].sum() * -1)
    new_portfolio["Nuevo Valor"] = new_portfolio["Nuevos Titulos"] * new_portfolio["Precio"]

    # Manejo de efectivo despues de compra
    new_cash = new_cash - new_portfolio["Valor Compra"].sum() + new_portfolio["Comisiones Compra"].sum()
    valor_portafolio.append(new_cash + new_portfolio["Nuevo Valor"].sum())

# Se obtiene el DataFrame propio de la inversión activa
df_activa = fn.df_activa(prices_post1, valor_portafolio, lista)
df_activa

# Se obtiene el DataFrame propio de las operaciones,
# indicando los títulos comprados, vendidos y las comisiones correspondientes

df_operaciones = fn.df_operaciones(lista2, acciones_compra, acciones_venta, comisiones_compra, comisiones_venta)
df_operaciones

# Se obtiene el DataFrame correspondiente a las medidas de desempeño
medidas = pd.DataFrame()
rend_m_m = [((df_activa["rendimiento"]*12).mean()-.0429),((df_passive_b["Rendimiento"]*12).mean()-.0429)]
rend_m_a = [df_activa["rendimiento_acumulado"][13],df_passive_b["Rendimiento Acumulado"][14]]
medidas["tipo de inversion"] = ["activa","pasiva"]
medidas["rend_m_m"] = rend_m_m
medidas["rend_m_a"] = rend_m_a
medidas.set_index("tipo de inversion")
