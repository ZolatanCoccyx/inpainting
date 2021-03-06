# -*- coding: utf-8 -*-
"""
Created on Sun Apr 24 14:08:41 2016

@author: Rémi
"""

import numpy as np
from scipy.misc import imread
import pylab as plt
#from skimage import io
from time import time
from inpaintools import *

im = imread('elephant2_300x225_rgb.jpg').squeeze()
mask = imread('elephant2_300x225_msk.jpg').squeeze()
mask = mask > 10

    
def Data(im, mx, my, mask, F, neighborhood):
    #F=frontiere(mask,neighborhood)
    M = np.copy(mask)
    I = im * (np.dstack((M==0, M==0, M==0)))
    e = []
    E = []
    D = []
    S = np.zeros(mask.shape)
    Data = np.zeros(mask.shape)
    for i, j in zip(neighborhood[:,0], neighborhood[:,1]):
        u = shift_image(I, i, j)
        v = warp(u, mx, my)
        e.append(u)
        E.append(v)
        x = (i ** 2 + j ** 2) ** 0.5
        D.append(w(x) * ((diff_image(u,v) ** 2) * ((u[:,:,0]>0) * (v[:,:,0]>0))))
        S = S + w(x) * ((v[:,:,0]>0) * (u[:,:,0]>0))
    S2 = S + ((S * F)==0)
    for Dataterm in D:
        Data = Data + (1 / S2) * Dataterm
    P = penaltydata(mx, my, mask)
    return ((Data + 5000000 * ((S * F)==0)) * (F > 0)) + P
    
def Datat(im, mask, shifts, neighborhood = np.array([[0,1],[0,-1],[0,2],[0,-2],[1,0],[-1,0],[2,0],[-2,0]])):
    F = frontiere(mask,neighborhood)
    n, k, v = im.shape
    l = shifts.shape[0]
    D = np.zeros((n,k,l))
    for m in range(l):
        mx = shifts[m,0]
        my = shifts[m,1]
        Mx = mx * np.ones((n,k)) * mask
        My = my * np.ones((n,k)) * mask
        Dm = Data(im, Mx, My, mask, F, neighborhood)
        D[:, :, m] = Dm
    return D    
    
def dataterm(im, mask, shifts, data_neighborhood):
    #bob = time()
    width, height, depth = im.shape
    im = im * (np.dstack((1 - mask, ) * depth))
    card_offsets = len(shifts)
    card_neighbors = len(data_neighborhood)
    result = np.zeros((width, height, card_offsets))
    neighims = np.zeros((width, height, depth, card_neighbors))
    
    for index_neighbor in range(card_neighbors):
        dx, dy = data_neighborhood[index_neighbor]
        neighims[:, :, :, index_neighbor] = shift_image(im, dx, dy)
    
    print 'Calcul du dataterm. ', card_offsets, 'offsets. 0% ',
    p = 0.0
    for index_offset in range(card_offsets):
        if float(index_offset) / card_offsets > p:
            print '#',
            p += 0.05
        mx, my = shifts[index_offset]
        Mx = mx * np.ones((width, height)) * mask
        My = my * np.ones((width, height)) * mask
        partial_result = np.zeros((width, height))
        normalisation = np.zeros((width, height))
        
        for index_neighbor in range(card_neighbors):
            dx, dy = data_neighborhood[index_neighbor]
            neighim = neighims[:, :, :, index_neighbor].copy()
            offsetim = warp(neighim, Mx, My)
            neigh_length = (dx ** 2 + dy ** 2) ** 0.5
            partial_result += w(neigh_length) * (diff_image(neighim, offsetim) ** 2) * (neighim[:,:,0]>0) * (offsetim[:,:,0]>0)
            normalisation += w(neigh_length) * (neighim[:,:,0]>0) * (offsetim[:,:,0]>0)
        
        normalisation += normalisation == 0
        partial_result /= normalisation
        result[:, :, index_offset] = partial_result + penaltydata(Mx, My, mask)
    print '100%'
    #print 'Temps de calcul = ', time()-bob
    return result
            
def shiftmaps(im, mask, shifts, D, smoothness_neighborhood = np.array([[0,1],[0,-1],[1,0],[-1,0]]),  rounds = 2):
    F = frontiere(mask, smoothness_neighborhood)
    M = np.copy(mask - F)
    F2 = frontiere(mask, np.array([[1,0],[0,1]]))
    nlabels = len(shifts)
    sz = np.prod(mask.shape[0:2])
    sh = mask.shape[0:2]
    
    indices = np.arange(sz).reshape(sh).astype(np.int32)

    # generate a trivial initial labeling
    labelmap = np.ones(sh).astype(np.int32)
    mx, my = compute_displacement_map(labelmap, shifts, mask)
    mx, my = mx.astype(np.int32), my.astype(np.int32)
    #D0=Data(im,mx,my,mask,F).astype(np.float32)
    E = 2000000 + np.sum(D[:, :, 0])
     
    half_neighborhood = [np.array([0,1])]
    for k in smoothness_neighborhood:
        if k[0] > 0:
            half_neighborhood.append(k)
    half_neighborhood = np.array(half_neighborhood)
    
    # alpha expansion loop
    print 'Alpha-expansion. ', len(shifts), 'offsets. 0% ',
    p = 0.0
    for t in range(rounds*len(shifts)):
        if float(t) / (rounds*len(shifts)) > p:
            print '#',
            p += 0.05
        
        currlab = np.mod(t,len(shifts))
        ai,aj = shifts[currlab]
        # compute warp for the current map
        mx, my = compute_displacement_map(labelmap, shifts, mask)
        # compute warped image for the current map 
        outM = warp(im, mx, my)
        # compute warped image for the candidate shift 
        outAlpha = warp(im, ai*mask, aj*mask)    # can be precomputed
        
        L = []
        
        for i,j in half_neighborhood:
            tmpx = shift_image(mx,-i,-j).astype(np.int32)
            tmpy = shift_image(my,-i,-j).astype(np.int32)
            outQ = warp(im, tmpx, tmpy)
            Mnew = M + frontiere(1-M, np.array([[-i,-j]]))
            a, b, c, d = -j if j<0 else None,-j if j>0 else None,-i if i<0 else None,-i if i>0 else None
            p1 = indices                      # current pixel
            p2 = shift_image(indices,-i,-j)   # always the same idx
            L.append(p1[a:b,c:d])
            L.append(p2[a:b,c:d])
            
            Mnew2 = mask - frontiere(mask, np.array([[-i,-j]]))            
            mx = mx * Mnew2
            my = my * Mnew2
            
            nullarray = (0 * mx).astype('float32')
            E00 = (((diff_image(outM, outQ) + difflabel(mx, my, tmpx, tmpy)) * Mnew)[a:b,c:d]).astype(np.float32)
            E01 = (((diff_image(outM, outAlpha) + difflabel(mx, my, nullarray + ai, nullarray + aj)) * Mnew)[a:b,c:d]).astype(np.float32)
            E10 = (((diff_image(outAlpha, outQ) + difflabel(tmpx, tmpy, nullarray + ai, nullarray + aj)) * Mnew)[a:b,c:d]).astype(np.float32)
            E11 = (nullarray[a:b,c:d]).astype(np.float32)
            
           # print(labelmap,8)
#            print(i, j)
#            plt.figure(1)
#            plt.clf()
#            plt.imshow(outQ[:,:,0]*mask*Mnew, interpolation= 'nearest')
#            plt.pause(10**(-3))
#            plt.figure(2)
#            plt.clf
#            plt.imshow(outM[:,:,0]*mask*Mnew, interpolation= 'nearest')
#            plt.pause(10**(-3))
#            plt.figure(3)
#            plt.clf
#            plt.imshow(labelmap, interpolation= 'nearest')
#            plt.pause(10**(-3))
            
            L.append(E00) #E00
            L.append(E01) #E01
            L.append(E10) #E10
            L.append(E11) #E11
            
            if np.sum((E01-E00+E10-E11)<0) > 0:
                plt.figure()
                plt.imshow(labelmap,interpolation='nearest')
                plt.pause(10**(-3))
                plt.figure()
                plt.imshow((E01-E00+E10-E11)<=0)
                plt.pause(10**(-3))
                print(np.min((E01-E00+E10-E11)))

        ix, iy = np.meshgrid(np.arange(sh[1]), np.arange(sh[0]))
#        
        D0 = D[iy, ix, labelmap].astype(np.float32)
        D1 = D[:, :, currlab].astype(np.float32)
        
        # trim the last row/column of the edge matrices
        energy, blab = solve_binary_problem(indices, D0, D1, L)
        
        # update solution
        bob = time()
        if energy<E:
            E=energy
            print "it:%02d \t l:%d \t (%d,%d) \t changed:%d \t e:%f"%(t, currlab, ai, aj, np.sum(blab[:]), energy)
#            mx, my = compute_displacement_map(labelmap, shifts, mask)
#            outM = warp(im, mx, my)
#            plt.imshow(outM/255.)
#            plt.pause(0.01)
            labelmap = labelmap * (1 - blab) + currlab * blab
            #print(time()-bob)
            
    print '100%'    
    mx, my = compute_displacement_map(labelmap, shifts, mask)
    outM = warp(im, mx, my)
    plt.figure(5)
    plt.plot(bobidibop)
    return outM, labelmap
    

maxshift = 200
numshifts = 99
shifts = np.zeros((numshifts, 2))

shifts[50:,:] = square_neighborhood(7) * np.array([30, 5])
shifts[0:25,:] = square_neighborhood(5) * 11
shifts[25:50,:] = square_neighborhood(5) * 5
#shifts[50:75,:] = square_neighborhood(5) * 16
#shifts[75:,:] = square_neighborhood(5) * np.array([30, 5])

plt.figure(0)
plt.plot(shifts[:,0], shifts[:,1], 'o')
plt.title('repartition offsets')

#im=np.zeros((8,8,1))
#im[:,:,0] = np.random.randint(255,size=64).reshape((8,8))
#mask=np.zeros((8,8))
#mask[2:6,2:5]=1
#mask[1:7,5]=1
#shifts=np.array([(i,j) for i in range(-1,2) for j in range(-1,1)])

#im = imread('foule.jpg').squeeze().astype(np.float32)
#
#mask = imread('foulem.jpg').squeeze().astype(np.float32)
#mask=mask[:,:,0]
#im=np.dstack((im,im,im))

#T0 = time()

D = dataterm(im, mask, shifts, square_neighborhood(3))

out, labelmap, bobidibop = shiftmaps(im, mask, shifts, D, rounds=1)
#T1=time() 
#print(T1-T0)
#import scipy.ndimage
#out = scipy.ndimage.filters.gaussian_filter(out, sigma=.5)
#plt.figure(1)
#plt.imshow(out/np.max(out))
#plt.figure(2)
#plt.imshow(labelmap)