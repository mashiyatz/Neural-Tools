#This script performs the linear color transfer step that 
#leongatys/NeuralImageSynthesis' Scale Control code performs.
#https://github.com/leongatys/NeuralImageSynthesis/blob/master/ExampleNotebooks/ScaleControl.ipynb
#Standalone script by github.com/htoyryla, and github.com/ProGamerGov

import numpy as np
import argparse
import scipy.ndimage as spi
from skimage import io,transform,img_as_float
from skimage.io import imread,imsave
from numpy import eye 

parser = argparse.ArgumentParser()
parser.add_argument('--target_image', type=str, help="The image you are transfering color to. Ex: target.png", required=True)
parser.add_argument('--target_mask_image', type=str, help="The mask image for the image you are transfering color to. Ex: target_mask.png")
parser.add_argument('--source_image', type=str, help="The image you are transfering color from. Ex: source.png", required=True)
parser.add_argument('--source_mask_image', type=str, help="The mask image for the image you are transfering color from. Ex: source_mask.png")
parser.add_argument('--output_image', default='output.png', help="The name of your output image. Ex: output.png", type=str)
parser.add_argument('--mode', default='pca', help="The color transfer mode. Options are pca, chol, or sym.", type=str)
parser.add_argument('--eps', default='1e-5', help="Your eps value in scientific notation or normal notation. Ex: 1e-5 or 0.00001", type=str)
parser.parse_args()
args = parser.parse_args()
target_img = args.target_image
source_img = args.source_image
target_mask = args.target_mask_image
source_mask = args.source_mask_image
output_name = args.output_image
transfer_mode = args.mode
eps_value = args.eps
color_list = args.color_codes.split(",")

target_img = spi.imread(target_img, mode="RGB").astype(float)/256
source_img = spi.imread(source_img, mode="RGB").astype(float)/256

def match_color(target_img, source_img, mode='pca', eps=1e-5):
    '''
    Matches the colour distribution of the target image to that of the source image
    using a linear transform.
    Images are expected to be of form (w,h,c) and float in [0,1].
    Modes are chol, pca or sym for different choices of basis.
    '''
    mu_t = target_img.mean(0).mean(0)
    t = target_img - mu_t
    t = t.transpose(2,0,1).reshape(3,-1)
    Ct = t.dot(t.T) / t.shape[1] + eps * eye(t.shape[0])
    mu_s = source_img.mean(0).mean(0)
    s = source_img - mu_s
    s = s.transpose(2,0,1).reshape(3,-1)
    Cs = s.dot(s.T) / s.shape[1] + eps * eye(s.shape[0])
    if mode == 'chol':
        chol_t = np.linalg.cholesky(Ct)
        chol_s = np.linalg.cholesky(Cs)
        ts = chol_s.dot(np.linalg.inv(chol_t)).dot(t)
    if mode == 'pca':
        eva_t, eve_t = np.linalg.eigh(Ct)
        Qt = eve_t.dot(np.sqrt(np.diag(eva_t))).dot(eve_t.T)
        eva_s, eve_s = np.linalg.eigh(Cs)
        Qs = eve_s.dot(np.sqrt(np.diag(eva_s))).dot(eve_s.T)
        ts = Qs.dot(np.linalg.inv(Qt)).dot(t)
    if mode == 'sym':
        eva_t, eve_t = np.linalg.eigh(Ct)
        Qt = eve_t.dot(np.sqrt(np.diag(eva_t))).dot(eve_t.T)
        Qt_Cs_Qt = Qt.dot(Cs).dot(Qt)
        eva_QtCsQt, eve_QtCsQt = np.linalg.eigh(Qt_Cs_Qt)
        QtCsQt = eve_QtCsQt.dot(np.sqrt(np.diag(eva_QtCsQt))).dot(eve_QtCsQt.T)
        ts = np.linalg.inv(Qt).dot(QtCsQt).dot(np.linalg.inv(Qt)).dot(t)
    matched_img = ts.reshape(*target_img.transpose(2,0,1).shape).transpose(1,2,0)
    matched_img += mu_s
    matched_img[matched_img>1] = 1
    matched_img[matched_img<0] = 0
    return matched_img


def extract_mask(image, color_list):
   mask = None
   if color == 'green':
       mask = np.all(image == (0,255,0), axis=-1)#.astype(int)   
   elif color == 'black': 
       mask = np.all(image == (0,0,0), axis=-1)#.astype(int)
   elif color == 'white':
       mask = np.all(image == (255,255,255), axis=-1)#.astype(int)
   elif color == 'red':
       mask = np.all(image == (255,0,0), axis=-1)#.astype(int)
   elif color == 'blue':
       mask = np.all(image == (0,0,255), axis=-1)#.astype(int)
   elif color == 'yellow':
       mask = np.all(image == (255,255,0), axis=-1)#.astype(int)
   elif color == 'grey':
       mask = np.all(image == (128,128,128), axis=-1)#.astype(int)
   elif color == 'lightblue':
       mask = np.all(image == (0,255,255), axis=-1)#.astype(int)
   elif color == 'purple':
       mask = np.all(image == (255,0,255), axis=-1)#.astype(int)
   else: 
       print "Color not recognized"
   return mask 


if args.target_mask_image == None and args.source_mask_image == None:
    output_img = match_color(target_img, source_img, mode=transfer_mode, eps=float(eps_value))
elif args.target_mask_image == None and args.source_mask_image != None:
    print "Target image mask was not provided"
    raise SystemExit
elif args.target_mask_image != None and args.source_mask_image == None:
    print "Source image mask was not provided"
    raise SystemExit
elif args.target_mask_image != None and args.source_mask_image != None:
    target_mask = spi.imread(target_mask, mode="RGB").astype(float)
    source_mask = spi.imread(source_mask, mode="RGB").astype(float)
    target_mask_list = []
    source_mask_list = []
    for color in list(color_list):
        print(color)
        color_mask = extract_mask(target_mask, color)
        target_mask_list.append(color_mask)
        color_mask = extract_mask(source_mask, color)
        source_mask_list.append(color_mask)
imsave(output_name, output_img)
