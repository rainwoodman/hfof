"""
Friends-of-Friends (FOF) for N-body simulations

Peter Creasey - Oct 2016

"""
from __future__ import absolute_import, print_function
from .lib import fof3d, get_cells, fof3d_periodic
from numpy import flatnonzero, concatenate, argsort, array, floor, zeros
import math


def pad_cube(pos, boxsize, r_pad):
    """
    For a set of points, find images in [0,boxsize)^ndim, then add the repeats
    of those in [0, r_pad) and clone them into [boxsize, boxsize+r_pad)

    An array with the images and the new positions is returned, 
    along with their corresponding indices in the original array (in case you 
    wanted to clone other properties such as their weights).

    pos     - (N,ndim) array
    boxsize - size for periodicity
    r_pad   - edge to pad onto [boxsize, boxsize+r_pad)
    
    returns pad_idx, pos
       pad_idx - (N_new) indices of the positions used to pad
       new_pos - (N+N_new, ndim) array of orig pos + padded pos [0, boxsize+r_pad]
    
    """

    pos = array(pos)
    npts, ndim = pos.shape

    inv_boxsize = float(1.0/boxsize)
    
    scale_r_pad = float(inv_boxsize * r_pad)

    spos = array(pos)*inv_boxsize 
    spos -= floor(spos) # now in [0,1)

    for ax in range(ndim):
        rep_right = zeros((ndim,),spos.dtype)
        rep_right[ax]=1

        # check those within r_pad of 0 
        rt_orig = flatnonzero(spos[:,ax]<scale_r_pad)

        if ax==0:
            # No results from previous padding
            pad_pos = spos[rt_orig]+rep_right
            pad_idx = rt_orig
            continue


        # Some of the *padded* positions may need to be repeated
        rt_pad = flatnonzero(pad_pos[:,ax]<scale_r_pad)

        pad_idx = concatenate((pad_idx, rt_orig, pad_idx[rt_pad]))
            
        pad_pos = concatenate((pad_pos, spos[rt_orig]+rep_right, 
                               pad_pos[rt_pad]+rep_right), axis=0)


    new_pos = concatenate((spos*boxsize, pad_pos*boxsize), axis=0)
                          
    return pad_idx, new_pos


def fof(pos, rcut, log=None):
    """
    Return integers for friends-of-friends domains
    """
    n, dim = pos.shape
    assert(dim==3)

    pos_min = pos.min(axis=0)
    pos_max = pos.max(axis=0)
    
    box_dims = pos_max - pos_min
    max_dim = max(box_dims)
    
    
    cell_width = float(rcut / (3**0.5))
    
    inv_cell_width = float(1.0/cell_width)
    
    nval = int(math.ceil(max_dim*inv_cell_width))+2
    nval = nval | 3 # Make sure last two bits set to 1
    
    if log is not None:
        print('Nval=%d (index conversion factor)'%nval, bin(nval), file=log)
        
        print('Position minima', pos_min, file=log)
        print('Position maxima', pos_max, file=log)
        
    
        print('rcut', rcut,file=log)
    
        print('Finding cells', file=log)
    cells = get_cells(pos, inv_cell_width, nval, log)
    
    if log is not None:
        print('Sorting cells', file=log)        
    sort_idx = argsort(cells)
    if log is not None:
        print('3d fof', file=log)
    domains = fof3d(cells, nval, rcut, sort_idx, pos, log=log)
    return domains

def fof_periodic(pos, boxsize, rcut, log=None):
    """
    As for fof but with periodic repetitions

    Return integers for friends-of-friends domains
    """
    n, dim = pos.shape
    assert(dim==3)


    old_idx, pos = pad_cube(pos, boxsize, rcut)
    assert(old_idx.max()<n)

    n_new = pos.shape[0] # including padded


    pos_min = pos.min(axis=0)
    pos_max = pos.max(axis=0)
    
    box_dims = pos_max - pos_min
    max_dim = max(box_dims)
    
    
    cell_width = float(rcut / (3**0.5))
    
    inv_cell_width = float(1.0/cell_width)
    
    nval = int(math.ceil(max_dim*inv_cell_width))+2 # two extra cells so never wrap
    nval = nval | 3 # Make sure last two bits set to 1
    
    if log is not None:
        print('Inserted {:,} images'.format(n_new-n), file=log)
        print('Nval=%d (index conversion factor)'%nval, bin(nval), file=log)
        
        print('Position minima', pos_min, file=log)
        print('Position maxima', pos_max, file=log)
        
    
        print('rcut', rcut,file=log)
    
        print('Finding cells', file=log)
    cells = get_cells(pos, inv_cell_width, nval, log)
    
    if log is not None:
        print('Sorting cells', file=log)        
    sort_idx = argsort(cells)
    if log is not None:
        print('3d fof periodic', file=log)
    domains = fof3d_periodic(cells, nval, n, old_idx, rcut, sort_idx, pos, log=log)
    return domains