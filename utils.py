import numpy as np
import rasterio
import cv2

# Order of the features in every pixel (the model depends on this order)
featureNames=['B2','B3','B4','B8','B8A','B11','B12',
              'NDVI','NDWI','NBR','RENDVI','VARI','ExG']


def readImage(imagePath):
    '''
    Reads a Sentinel-2 tile (7 bands) and returns the 13 features per pixel, shape (H,W,13)
    '''
    with rasterio.open(imagePath) as src:
        bandsData=src.read().astype(np.float32)  # (7,H,W)
        profile=src.profile

    bandsData=np.nan_to_num(bandsData,nan=0.0)

    # GEE stores reflectance x 10000
    bandsData/=10000.0

    B2,B3,B4,B8,B8A,B11,B12=bandsData

    # 3x3 gaussian low-pass filter
    kernel=(1/16.0)*np.array([[1,2,1],
                              [2,4,2],
                              [1,2,1]],dtype=np.float32)

    B2f =cv2.filter2D(B2, -1,kernel,borderType=cv2.BORDER_REFLECT)
    B3f =cv2.filter2D(B3, -1,kernel,borderType=cv2.BORDER_REFLECT)
    B4f =cv2.filter2D(B4, -1,kernel,borderType=cv2.BORDER_REFLECT)
    B8f =cv2.filter2D(B8, -1,kernel,borderType=cv2.BORDER_REFLECT)
    B8Af=cv2.filter2D(B8A,-1,kernel,borderType=cv2.BORDER_REFLECT)
    B11f=cv2.filter2D(B11,-1,kernel,borderType=cv2.BORDER_REFLECT)
    B12f=cv2.filter2D(B12,-1,kernel,borderType=cv2.BORDER_REFLECT)

    def div(n,d,eps=1e-6):
        return n/(np.abs(d)+eps)

    NDVI  =div(B8f-B4f, B8f+B4f)
    NDWI  =div(B3f-B8f, B3f+B8f)
    NBR   =div(B8f-B12f,B8f+B12f)
    RENDVI=div(B8f-B8Af,B8f+B8Af)
    VARI  =div(B3f-B4f, B3f+B4f-B2f)
    ExG   =2*B3f-B4f-B2f

    img=np.stack([B2f,B3f,B4f,B8f,B8Af,B11f,B12f,NDVI,NDWI,NBR,RENDVI,VARI,ExG],axis=-1)

    return img,profile
