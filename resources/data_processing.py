import numpy as np
import statsmodels.api as sm
import pandas as pd


def getR2FromPast(csv, ticker):
    df = pd.read_csv(csv,delimiter=',', encoding="utf-8-sig")
    print(df.columns)

    y = df[ticker].values.tolist()

    x = [
        df['Joy'].values.tolist(),
        df['Anger'].values.tolist(),
        df['Frequency'].values.tolist(),
        ]


    ones = np.ones(len(x[0]))
    X = sm.add_constant(np.column_stack((x[0], ones)))
    for ele in x[1:]:
        X = sm.add_constant(np.column_stack((ele, X)))
    results = sm.OLS(y, X).fit()
    return results

def getFutureValue(RegressionResults, futureVals):
    coeff_list = RegressionResults.params
    x = 0
    for coeff in range(3):
        x += futureVals[coeff]*coeff_list[coeff]
    x += coeff_list[3]
    return x

futureVals = [0.5701695, 0.54274264, 0.10282083]

print (getR2FromPast('all_facebook_statuses_p2.csv', 'RGR').summary())
print (getR2FromPast('all_facebook_statuses_p2.csv', 'RGR').params)
print ("\n\n")
print (getR2FromPast('all_facebook_statuses_p2.csv', 'AOBC').summary())
print (getR2FromPast('all_facebook_statuses_p2.csv', 'AOBC').params)


