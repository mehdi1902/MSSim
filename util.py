# -*- coding: utf-8 -*-

def properties(prop_str):
    props = open('properties', 'r').readlines()
    for prop in props:
        if prop_str in prop:
            return prop.split('=')[-1]