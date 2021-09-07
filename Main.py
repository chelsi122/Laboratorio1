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