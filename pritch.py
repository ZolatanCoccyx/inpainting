# -*- coding: utf-8 -*-
"""
Created on Wed Jun 08 14:44:02 2016

@author: D
"""

import numpy as np
from scipy.misc import imread
import pylab as plt
from inpaintools import *

w = lambda x : np.exp(-0.25 * (x**2))    

#im = imread('kom03.png').squeeze()
#mask = imread('kom03_msk.png', 'png').squeeze()
#mask = mask>0
#im = imread('elephant2_300x225_rgb.jpg').squeeze()
#mask = imread('elephant2_300x225_msk.jpg').squeeze()
#mask = mask > 10

#im=np.random.randint(255,size=(5,5,1))
#mask=np.zeros((5,5))
#mask[1:4,1:4]=1


numshifts = 99
shifts = np.zeros((numshifts, 2))

shifts[50:,:] = square_neighborhood(7) * np.array([30, 5])
shifts[0:25,:] = square_neighborhood(5) * 11
shifts[25:50,:] = square_neighborhood(5) * 5

#shifts = np.array([(i,j) for i in range(-1,2) for j in range(-1,1)])

data_neighborhood = square_neighborhood(3)
smoothness_neighborhood = square_neighborhood(3)

def alpha_expansion_step(im, mask, mx, my, alpha, D0, D1, smoothness_neighborhood):
    sh = mask.shape
    indices = np.arange(0, np.prod(sh)).reshape(sh).astype(np.int32)
    alphax, alphay = alpha
    alphax = alphax * mask
    alphay = alphay * mask
    outM = warp(im, mx, my).astype(np.float32)
    outalpha = warp(im, alphax, alphay).astype(np.float32)
    mask_broadcast = mask.reshape((mask.shape[0], mask.shape[1], 1))
    intM = mask - frontiere(mask, smoothness_neighborhood)

    half_neighborhood = [np.array([0,1])]
    for k in smoothness_neighborhood:
        if k[0] > 0:
            half_neighborhood.append(k)
    half_neighborhood = np.array(half_neighborhood)    
    
    L = []    
    
    for i, j in half_neighborhood:
        a, b, c, d = -j if j<0 else None,-j if j>0 else None,-i if i<0 else None,-i if i>0 else None
        p1 = indices[a:b,c:d]
        p2 = shift_image(indices, -i, -j)

        L.append(p1.astype(np.int32))
        L.append(p2[a:b,c:d].astype(np.int32))        
        
        Mnew = intM + frontiere(1- intM, np.array([[-i,-j]]))
        tempx = shift_image(mx, -i, -j) * mask
        tempy = shift_image(my, -i, -j) * mask
        outQ = (warp(im, tempx, tempy) * mask_broadcast).astype(np.float32)
<<<<<<< HEAD
        E00 = ((diff_image(outM[:,:,:3], outQ[:,:,:3]) + difflabel(mx, my, tempx, tempy)) * Mnew).astype(np.float32)
        E10 = ((diff_image(outalpha[:,:,:3], outQ[:,:,:3]) + difflabel(alphax, alphay, tempx, tempy)) * Mnew).astype(np.float32)
        E01 = ((diff_image(outM[:,:,:3], outalpha[:,:,:3]) + difflabel(mx, my, alphax, alphay)) * Mnew).astype(np.float32)
        E11 = mx * 0
        #E00 = mint(E00,E01+E10)-1
=======
        E00 = ((diff_image(outM, outQ) + difflabel(mx, my, tempx, tempy)) * Mnew).astype(np.float32)
        E10 = ((diff_image(outalpha, outQ) + difflabel(alphax, alphay, tempx, tempy)) * Mnew).astype(np.float32)
        E01 = ((diff_image(outM, outalpha) + difflabel(mx, my, alphax, alphay)) * Mnew).astype(np.float32)
        E11 = mx * 0
        
>>>>>>> parent of 734d31e... hesun qui marche super bien + pritch modifié
        L.append(E00[a:b,c:d].astype(np.float32))
        L.append(E10[a:b,c:d].astype(np.float32))
        L.append(E01[a:b,c:d].astype(np.float32))
        L.append(E11[a:b,c:d].astype(np.float32))
        
<<<<<<< HEAD
        if np.sum((E01-E00+E10-E11)<0) > 0:
            print(np.min(E01-E00+E10-E11))
            plt.figure(1)
            plt.imshow(mx)
            plt.pause(10**(-3))
            plt.figure(2)
            plt.imshow(my,interpolation='nearest')
            plt.pause(10**(-3)) 
            plt.figure(3)
            plt.imshow(E00,interpolation='nearest')
            plt.pause(10**(-3))
            plt.figure(4)
            plt.imshow(E01,interpolation='nearest')
            plt.pause(10**(-3))
            plt.figure(5)
            plt.imshow((E01-E00+E10-E11)<0)
            plt.pause(10**(-3))
            input()
=======
        if np.sum((E01[a:b,c:d]-E00[a:b,c:d]+E10[a:b,c:d]-E11[a:b,c:d])<0) > 0:
            return 'energie non reguliere'
>>>>>>> parent of 734d31e... hesun qui marche super bien + pritch modifié
        energy, alphamap = solve_binary_problem(indices, D0.astype(np.float32), D1.astype(np.float32), L)
    return energy, alphamap


def alpha_expansion(im, mask, shifts, data_energy, smoothness_neighborhood, rounds):
    sh = mask.shape
    labelmap = np.zeros(sh).astype(np.int32)
    energy = float('inf')
    
    for t in range(rounds * len(shifts)):
        currlab = t % len(shifts)
        alpha = shifts[currlab]
        ix, iy = np.meshgrid(np.arange(sh[1]), np.arange(sh[0]))
        D0 = data_energy[iy, ix, labelmap]
        D1 = data_energy[:,:,currlab]
        mx, my = compute_displacement_map(labelmap, shifts, mask)
        print(mx.shape)
        print(my.shape)
        print(alpha)
        print(D0.shape)
        print(D1.shape)
        print(alpha_expansion_step(im, mask, mx, my, alpha, D0, D1, smoothness_neighborhood)[0])
        print(alpha_expansion_step(im, mask, mx, my, alpha, D0, D1, smoothness_neighborhood)[1])
        new_energy, alphamap = alpha_expansion_step(im, mask, mx, my, alpha, D0, D1, smoothness_neighborhood)
        if new_energy < energy :
            energy = new_energy
            labelmap = currlab * alphamap + labelmap * (1 - alphamap)
            #print "it:%02d \t l:%d \t (%d,%d) \t changed:%d \t e:%f"%(t, currlab, alpha[0], alpha[1], np.sum(alphamap[:]), energy)
    
    return labelmap
    
    
def pritch(im, mask, shifts, data_neighborhood, smoothness_neighborhood, rounds):
    data_energy = dataterm(im, mask, shifts, data_neighborhood)
    labelmap = alpha_expansion(im, mask, shifts, data_energy, smoothness_neighborhood, rounds)
    mx, my = compute_displacement_map(labelmap, shifts, mask)
    return warp(im, mx, my)

<<<<<<< HEAD
#out, labelmap = pritch(im, mask, shifts2, data_neighborhood, smoothness_neighborhood, 2)
#plt.imsave('C:\Users\D\Desktop\inpainting\image\komo03_pritch.png',out,vmin=0,vmax=255,format='png')
=======
#out = pritch(im, mask, shifts, data_neighborhood, smoothness_neighborhood, 2)

>>>>>>> parent of 734d31e... hesun qui marche super bien + pritch modifié
#out2=np.zeros(out.shape)
#for i in range(225):
#    for j in range(300):
#        out2[i,j,:]=out[224-i,299-j,:]
#
#def petite_fonction(n):
#    return str(n//100) + str((n%100 - n%10)/10) + str(n%10)
#
#for i in range(1,145):
#    print(i)
#    r=petite_fonction(i)
#    im = imread('a' + r +'.png').squeeze()
#    mask = imread('a' + r +'_msk.png', 'png').squeeze()
#    mask = mask>0
#    out, labelmap = pritch(im, mask, shifts2, data_neighborhood, smoothness_neighborhood, 2)
#    plt.imsave('C:\Users\D\Desktop\inpainting\image\a' + r + '_pritch.png',out,vmin=0,vmax=255,format='png')
#    plt.imsave('C:\Users\D\Desktop\inpainting\image\a' + r + '_pritchlabel.png',labelmap,vmin=0,vmax=98,format='png')
#   