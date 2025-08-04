import numpy.random as rnd

def Wait(env, mean, std):
    k = (mean / std) ** 2
    theta = mean / k
    waitingTime = rnd.gamma(k, theta)
    return waitingTime
