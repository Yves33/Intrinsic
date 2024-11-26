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

import jsonpickle
import numpy as np
import quantities as pq
import jsonpickle.ext.numpy as jsonpickle_numpy
from jsonpickle.ext.numpy import NumpyBaseHandler,NumpyGenericHandler,NumpyNDArrayHandlerView
@jsonpickle.handlers.register(np.int64, base=True)
@jsonpickle.handlers.register(np.int32, base=True)
@jsonpickle.handlers.register(np.float64, base=True)
@jsonpickle.handlers.register(np.float32, base=True)
@jsonpickle.handlers.register(np.generic, base=True)
class MyScalarHandler(NumpyGenericHandler):
    def flatten(self, obj, data):
        try:
            return obj.item()
        except:
            return super(MyScalarHandler,self).flatten(obj,data)


@jsonpickle.handlers.register(np.ndarray, base=True)
class MyArrayHandler(NumpyNDArrayHandlerView):
    def flatten(self, obj, data):
        ## NumpyNDArrayHandlerViewis complex. calling super will fail if obj.size<size_treshold
        ## we don't care as we want to dump all small objects as lists(object size<250)  
        if obj.size<250:
            return obj.tolist()
        else:
            return super(MyArrayHandler,self).flatten(obj.copy(),data)
        #except Exception as ex:
        #    print(*args,**kwargs)
        #    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        #    message = template.format(type(ex).__name__, ex.args)
        #    print(message)

@jsonpickle.handlers.register(pq.Quantity, base=True)
class MyQuantityHandler(NumpyNDArrayHandlerView):
    def flatten(self, obj, data):  # data contains {}
        try:
            return super(MyQuantityHandler,self).flatten(obj.copy(),data)
        except:
            return("JSONPICKLEERROR")


if __name__=='__main__':
    jsonpickle_numpy.register_handlers()
    arrsize=15
    d=np.ndarray(shape=(1,arrsize),buffer=np.array([1.0/np.random.randint(1,65365) for _ in range(arrsize)]).tobytes())
    #d=np.int64(456)
    print(jsonpickle.encode(d))