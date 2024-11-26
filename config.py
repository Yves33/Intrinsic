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


from pathlib import Path
import logging

class basecfg(type):
    __dynamic__={}
    def parse(cls,paramfile):
        if (Path(__file__).resolve().parent/paramfile).is_file():
            with open(paramfile) as pfile:
                for e,line in enumerate(pfile.readlines()):
                    if line.startswith("#") or len(line.strip(' \t\n\r')) == 0:
                        continue
                    paramname=line.split('=',1)[0].strip()
                    paramvalue=line.split('=',1)[1].split('#')[0].strip()
                    try:
                        paramcomment=line.split('=',1)[1].split('#')[1].strip()
                    except:
                        pass
                    if '@' in paramvalue:
                        cls.__dynamic__[paramname]=paramvalue
                    else:
                        setattr(cls,paramname,eval(paramvalue))
                    logging.getLogger(__name__).debug(f"Updating value for param {paramname}")

    def dump(cls):
        d={}
        d.update({k:getattr(cls,k) for k in dir(cls) if not k.startswith('__')})
        d.update(cls.__dynamic__)
        return {k: v for k, v in sorted(d.items(), key=lambda item: item[0])}

    def set(cls,key,value):
        if key in dir(cls):
            setattr(cls,key,value)
        elif key in cls.__dynamic__.keys():
            logging.getLogger(__name__).warning(f"using set on dynamic cfg will freeze {key}")
            setattr(cls,key,value)
            cls.__dynamic__.pop(key)
        else:
            raise AttributeError(f"Can't set non existing attributes {key}") 

    def set_dynamic(cls,key,value):
        if isinstance(value,str):
            cls.__dynamic__[key]=value
        else:
            raise KeyError(f"{cls.__name__} does not have {key} dynamic attribute.")

    def __getattr__(cls,key):
        if key in cls.__dynamic__.keys():
            return eval(cls.__dynamic__[key].replace('@','cfg.'))
        else:
            raise AttributeError(f"{cls.__name__} does not have {key} attribute.")

class cfg(metaclass=basecfg):
    pass

if __name__=='__main__':
    cfg.parse("./params/generic_params_test.py")
    #print(cfg.dump())
    print(cfg.IV_CURRENT_INJECTION_START)
    print(cfg.IV_SAG_PEAK_START)
    cfg.IV_CURRENT_INJECTION_START=0.5
    print(cfg.IV_CURRENT_INJECTION_START)
    print(cfg.IV_SAG_PEAK_START)