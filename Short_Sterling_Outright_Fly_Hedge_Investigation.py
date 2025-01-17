import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import  DateFormatter, WeekdayLocator, HourLocator, \
     DayLocator, MONDAY
import datetime
import functools
import pprint
from trades import trades

# Global Parameter
ButterflyName = "h5h6"
OutrightName = "u5"
HedgeRatio = 57
EntryStd = 3
StopStd = 5
BookStd = 2
HedgeRatioFrom = 55
HedgeRatioTo = 59
    
##path = "L_History.xlsx"
path = "L_Daily.xlsx" # for daily data
xls = pd.ExcelFile(path)
data = {}
for sheet_name in xls.sheet_names:
    print sheet_name
    data[sheet_name] = xls.parse(sheet_name,
                                 skiprows=[0],
                                 parse_dates=True,
                                 date_parser=functools.partial(datetime.datetime.strptime, format = "%m/%d/%Y"))
##    data[sheet_name].columns = ['DateTime', 'Open', 'High', 'Low', 'Close', 'Volume']
    data[sheet_name].columns = ['DateTime', 'Close']
outrights = xls.sheet_names[0:12]
flies = xls.sheet_names[12:]

ButterflyData = data['BL-'+ButterflyName.upper()+' Comdty']
OutrightData = data['L '+OutrightName.upper()+' Comdty']

rolling_window = 20
trade_recorder = {}
m = pd.merge(OutrightData, ButterflyData, on = "DateTime", suffixes = ('_'+OutrightName, '_'+ButterflyName))
for i in range(HedgeRatioFrom, HedgeRatioTo,1):
    index = 'hr_'+i.__str__()
    trade_recorder[index] = trades()
    m[index] = m['Close_'+OutrightName] + i*m['Close_'+ButterflyName]
    m[index+'_mean'] = pd.rolling_mean(m[index], rolling_window)
    m[index+'_std']  = pd.rolling_var (m[index], rolling_window)
    for rn in range(1,len(m)):
        if (m.iloc[rn-1][index] > m.iloc[rn-1][index+'_mean'] + EntryStd*m.iloc[rn-1][index+'_std']) and\
           (m.iloc[rn][index] < m.iloc[rn-1][index+'_mean'] + EntryStd*m.iloc[rn-1][index+'_std']) and\
           (trade_recorder[index].position == 0):
            trade_recorder[index].add(m.iloc[rn]['DateTime'],
                                      m.iloc[rn-1][index+'_mean'] + EntryStd*m.iloc[rn-1][index+'_std'],
                                      -1,
                                      "EnterShort")
        if m.iloc[rn-1][index] < m.iloc[rn-1][index+'_mean'] - EntryStd*m.iloc[rn-1][index+'_std'] and\
           m.iloc[rn][index] > m.iloc[rn-1][index+'_mean'] - EntryStd*m.iloc[rn-1][index+'_std'] and\
           trade_recorder[index].position == 0:
            trade_recorder[index].add(m.iloc[rn]['DateTime'],
                                      m.iloc[rn-1][index+'_mean'] - EntryStd*m.iloc[rn-1][index+'_std'],
                                      1,
                                      "EnterLong")
        if trade_recorder[index].position > 0 and\
           m.iloc[rn][index] > m.iloc[rn-1][index+'_mean'] + BookStd*m.iloc[rn-1][index+'_std']:
            trade_recorder[index].add(m.iloc[rn]['DateTime'],
                                      m.iloc[rn][index],
                                      -1,
                                      "ExitLong")
        if trade_recorder[index].position < 0 and\
           m.iloc[rn][index] < m.iloc[rn-1][index+'_mean'] - BookStd*m.iloc[rn-1][index+'_std']:
            trade_recorder[index].add(m.iloc[rn]['DateTime'],
                                      m.iloc[rn][index],
                                      1,
                                      "ExitShort")
        if trade_recorder[index].position > 0 and\
           m.iloc[rn][index] < m.iloc[rn-1][index+'_mean'] - StopStd*m.iloc[rn-1][index+'_std']:
            trade_recorder[index].add(m.iloc[rn]['DateTime'],
                                      m.iloc[rn][index],
                                      -1,
                                      "StopLong")
        if trade_recorder[index].position < 0 and\
           m.iloc[rn][index] > m.iloc[rn-1][index+'_mean'] + StopStd*m.iloc[rn-1][index+'_std']:
            trade_recorder[index].add(m.iloc[rn]['DateTime'],
                                      m.iloc[rn][index],
                                      1,
                                      "StopShort")
    if trade_recorder[index].position <> 0:
            trade_recorder[index].add(m.iloc[len(m)-1]['DateTime'],
                              m.iloc[len(m)-1][index],
                              -trade_recorder[index].position,
                                      "CloseOnEnd")
    print index + ", " + trade_recorder[index].pnl().__str__()
        
            
def plot(outright_index, fly_index, hedged_index):
    date = m["DateTime"].tolist()
    outright_prices = m[outright_index].values.tolist()
    fly_prices = m[fly_index].values.tolist()
    hedged_prices = m[hedged_index].values.tolist()
    upper_band = (m[hedged_index+"_mean"]+EntryStd*m[hedged_index+"_std"]).values.tolist()
    lower_band = (m[hedged_index+"_mean"]-EntryStd*m[hedged_index+"_std"]).values.tolist()
    buy_dates = [x[0] for x in trade_recorder[hedged_index].trades if x[2]>0]
    buy_prices = [x[1] for x in trade_recorder[hedged_index].trades if x[2]>0]
    sell_dates = [x[0] for x in trade_recorder[hedged_index].trades if x[2]<0]
    sell_prices = [x[1] for x in trade_recorder[hedged_index].trades if x[2]<0]
    
    fig, (ax1, ax2, ax3) = plt.subplots(3, sharex = True)
    mondays = WeekdayLocator(MONDAY)
    mondays.MAXTICKS = 2000
    alldays = DayLocator()              # minor ticks on the days
    alldays.MAXTICKS = 2000
    weekFormatter = DateFormatter('%b %d')  # e.g., Jan 12
    dayFormatter = DateFormatter('%d')      # e.g., 12
    ax1.xaxis.set_major_locator(mondays)
    ax1.xaxis.set_minor_locator(alldays)
    ax1.xaxis.set_major_formatter(weekFormatter)
    
    ax1.plot(date, outright_prices)
    ax2.plot(date, fly_prices)
    ax3.plot(date, hedged_prices)
    ax3.plot(date, upper_band, color='k')
    ax3.plot(date, lower_band, color='k')
    ax3.plot(buy_dates, buy_prices, "^", markersize = 5, color='m')
    ax3.plot(sell_dates, sell_prices, "v", markersize = 5, color='k')
    
    ax1.xaxis_date()
    ax1.autoscale_view()

plot("Close_"+OutrightName, "Close_"+ButterflyName, "hr_"+HedgeRatio.__str__())
plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
plt.show()
pp = pprint.PrettyPrinter(indent = 4)
pp.pprint(trade_recorder['hr_'+HedgeRatio.__str__()].trades)

