library(readr)
library(forecast)
library(zoo)
tb24 <- read_csv("~/Documents/thesis-bak/tibet-toolkit/python_code/24_cont_anom.csv")

##first try deseasonalizing
## Create a daily Date object - helps my work on dates
inds <- seq(as.Date("1997-02-04"), as.Date("2017-06-26"), by = "day")
#either use the climate averaged anomalies or the deseasonalized trend
tpts <- ts(tb24$anom) 
#first look at the plots
par(mfrow=c(3,1))
plot(tpts, main="tibet snow coverage km^2")
acf(tpts, main= "snow ACF")
pacf(tpts, type="partial", main="snow PACF")

#try to make ts stationary
tptsPos = tpts + 2000000

#log drops acf off. looks like an AR(5)
ts.log = log(tptsPos)
par(mfrow=c(3,1))
plot(ts.log, main="log tibet snow coverage km^2")
acf(ts.log, main= "log snow ACF")
pacf(ts.log, type="partial", main="log snow PACF")

ts.sqrt = sqrt(tptsPos)
par(mfrow=c(3,1))
plot(ts.sqrt, main="sqrt tibet snow coverage km^2")
acf(ts.sqrt, main= "sqrt snow ACF")
pacf(ts.sqrt, type="partial", main="sqrt snow PACF")

# these don't turn out so well.
ts.isqrt = 1/sqrt(tptsPos)
par(mfrow=c(3,1))
plot(ts.isqrt, main="inv sqrt tibet snow coverage km^2")
acf(ts.isqrt, main= "inv sqrt snow ACF")
pacf(ts.isqrt, type="partial", main="inv sqrt snow PACF")

ts.inv = 1/tptsPos
par(mfrow=c(3,1))
plot(ts.inv, main="inv tibet snow coverage km^2")
acf(ts.inv, main= "inv snow ACF")
pacf(ts.inv, type="partial", main="inv snow PACF")


#lowest aic so far...
fitAnom <- arima(ts.log, order=c(5,0,2))
print(fitAnom)
tsdiag(fitAnom)
myResAnom <- residuals(fitAnom)

#autofit doesn't quite work as well as manually searching
autotpts = auto.arima(ts.log, seasonal=TRUE)
print(autotpts)
tsdiag(autotpts)
myResAutotpts <- residuals(autotpts)
autoDetpts = auto.arima(destpts, seasonal=FALSE)
print(autoDetpts)
tsdiag(autoDetpts)
myResautoDetpts <- residuals(autoDetpts)


par(mfrow=c(1,1))
qqnorm(myResAnom, main = "Normal Q-Q Plot", xlab = "Theoretical Quantiles", ylab = "Sample Quantiles")


library(tsDyn)
autopairs(ts.log, lag=1, type="regression")
hist(ts.log, br = 15) #does not suggest bimodality
fitCmp <- arima(ts.log, order=c(5,0,0))


selectSETAR(ts.log, m=5, mL=1:6, mH=1:6, thSteps = 1:5, thDelay=0:2)

mod = list()
mod[['linear']] <- linear(ts.log, m=6)
mod[['setar']] <- setar(ts.log, m=6, mL=1, mH=1, thDelay=1)
mod[['lstar']] <- lstar(ts.log, m=6, thDelay=2)
mod[["aar"]] <- aar(ts.log, m=6)

#tbd neural network
mod[["nnetTs"]] <- nnetTs(ts.log, m=5, d=t, steps=10, size=5)
sapply(mod, AIC)

sapply(mod, MAPE)

summary(mod[['linear']])
plot(mod[["linear"]])

summary(mod[['lstar']])
plot(mod[["lstar"]])
