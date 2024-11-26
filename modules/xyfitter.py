#!/usr/bin/env python3
# Copyright (c)2020-2022, Yves Le Feuvre <yves.le-feuvre@u-bordeaux.fr>
#
# All rights reserved.
#
# This file is prt of the intrinsic program
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted under the terms of the BSD License. See
# LICENSE file in the root of the Project.

import logging
import numpy as np
import scipy

######################################################################################
## fitter object
## can fit linear, single and double exponentials
## for linear f(x)=a*x+b:                       : params are f.a and f.b
## for single exp f(x)=a*exp(-(x-o)/tc)) +b     : params are f.tc
## for double exp f(x)=a*exp(-(x-o)/tc1)) +b exp(-(x-o)/tc2)) +c : params are f.wtc (weighted average tc), f.atc (arythmetic average), f.tc1 and f.tc2
## usage 
#> f=xyfitter(xvalues,yvalues)
#> if f.success and fitter.r2>some_value:
#>     print(f.tc)
#######################################################################################
class XYFitter():
    def fitlinear(self,x,a,b):
        return a*x+b

    ## exponential fits with time offsets,o
    def fit1exp(self,x,a,b,c,o):
        return a*np.exp(-(x-o)/b)+c

    def fit2exp(self,x,a,b,c,d,e,o):
        return a*np.exp(-(x-o)/b)+c*np.exp(-(x-o)/d)+e

    ## exponential fits with time offsets,o
    def fit1expnoo(self,x,a,b,c):
        return a*np.exp(-(x)/b)+c

    def fit2expnoo(self,x,a,b,c,d,e):
        return a*np.exp(-(x)/b)+c*np.exp(-(x)/d)+e

    def __init__(self,x,y,fitmode,weighted=True,o=0.0,maxfev=10000,version=1):
        self.fitmode=fitmode
        self.version=version
        self.maxfev=maxfev
        if fitmode==0:
            self.fitfunc=self.fitlinear
            self.pot=[1.0,0.0]
            self.o=0.0
            try:
                self.pot,pcov=scipy.optimize.curve_fit(self.fitfunc,x,y,p0=tuple(self.pot), maxfev=self.maxfev)
                self.success=True
                self.a, self.b=self.pot[0],self.pot[1]
            except:
                logging.getLogger(__name__).debug(f"Linear fit failed")
                self.a=np.nan
                self.b=np.nan
                self.success=False
        if fitmode==1:
            if self.version==1:
                self.o=o ## should be x[0]?
                self.fitfunc=self.fit2expnoo
                self.pot=[1.0,0.02,-70] ## approximate initial parameters for mb time constants
                x=x-x[0]
            else:
                self.fitfunc=self.fit1exp
                self.pot=[1.0,0.02,-70,o]  ## approximate initial parameters for mb time constants
            try:
                self.pot,pcov=scipy.optimize.curve_fit(self.fitfunc,x,y,p0=tuple(self.pot), maxfev=self.maxfev)
                self.tc=self.pot[1]
                self.success=True
            except:
                logging.getLogger(__name__).debug(f"First order exponential fit failed")
                self.tc=np.nan
                self.success=False
        if fitmode==2:
            if self.version==1:
                self.o=o ## should be x[0]?
                self.fitfunc=self.fit2expnoo
                self.pot=[1.0,0.02,1.0,0.0015,-0.07] ## approximate initial parameters for mb time constants
                x=x-x[0]
            else:
                self.fitfunc=self.fit2exp
                self.pot=[1.0,0.02,1.0,0.0015,-0.07,o] ## approximate initial parameters for mb time constants
            try:
                self.pot,pcov=scipy.optimize.curve_fit(self.fitfunc,x,y,p0=tuple(self.pot), maxfev=self.maxfev)
                self.wtc=(self.pot[0]*self.pot[1]+self.pot[2]*self.pot[3])/(self.pot[0]+self.pot[2]) ## weighted average
                self.atc=(self.pot[1]+self.pot[3])/2                                                 ## average, not weighted
                self.tc1=self.pot[1]                                                                 ## first time constant
                self.tc2=self.pot[3]                                                                 ## second time constant
                if weighted:
                    self.tc=self.wtc
                else:
                    self.tc=self.atc
                self.success=True
                self.r2=self.getr2(x,y)
            except:
                logging.getLogger(__name__).debug(f"Second order exponential fit failed")
                self.tc=np.nan
                self.r2=0.0
                self.success=False
        ## in order to output correct results with jsonpickle, we have to transform pot to list
        self.pot=[float(p) for p in self.pot]
    
    def getr2(self,x,y):
        y_fit=self.line(x)
        ss_res = np.sum((y-y_fit)**2)
        ss_tot = np.sum((y- np.mean(y))**2)
        return 1-(ss_res/ss_tot)

    def line(self,arr):
        if self.success:
            if self.version==1:
                return np.array([self.fitfunc(t-self.o,*self.pot) for t in arr])
            else:
                return np.array([self.fitfunc(t,*self.pot) for t in arr])
        else:
            return np.array([])