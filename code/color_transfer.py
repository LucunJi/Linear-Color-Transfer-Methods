import cv2
import numpy as np
from scipy.linalg import sqrtm
from numpy.linalg import cholesky, svd, inv, qr, eig


# use the style of img1 to modify img2
# summarize the basic steps of linear color transfer
def color_trans_linear(img1, img2, func):
    shape2 = img2.shape
    img1 = img1.reshape((-1, img1.shape[-1]))
    img2 = img2.reshape((-1, img1.shape[-1]))
    mean1 = np.mean(img1, axis=0)
    mean2 = np.mean(img2, axis=0)
    cov1 = np.cov(img1.T)
    cov2 = np.cov(img2.T)
    t = func(cov1, cov2)
    ret = (img2 - mean2) @ t.T + mean1
    return ret.reshape(shape2)


# SVD decomposition
# implements the paper Color Transfer in Correlated Color Space by Xuezhong Xiao et al.
# the formula in the original paper mistakenly omitted some square roots and I fixed that here
def trans_svd(cov1, cov2):
    u1, lambda1, _ = svd(cov1)
    u2, lambda2, _ = svd(cov2)
    return u1 @ np.diag(np.sqrt(lambda1)) @ np.diag(1 / (np.sqrt(lambda2) + 1e-12)) @ inv(u2)


# assume that three channels are not correlated
# implements the paper Color Transfer between Images by Erik Reinhard et al.
def trans_indep(cov1, cov2):
    diag1 = np.diagonal(cov1)**0.5
    diag2 = np.diagonal(cov2)**0.5
    return np.diag(diag1 / diag2)


# Cholesky decomposition
# implements the Cholesky method in the paper The Linear Monge-Kantorovitch Linear Colour Mapping for Example-Based Colour Transfer by F. Pitie et al.
def trans_cholesky(cov1, cov2):
    return cholesky(cov1) @ inv(cholesky(cov2))


# Monge-Kantorovitch method
# implements the MK method in the paper The Linear Monge-Kantorovitch Linear Colour Mapping for Example-Based Colour Transfer by F. Pitie et al.
def trans_mk(cov1, cov2):
    t = sqrtm(cov2) @ cov1 @ sqrtm(cov2)
    return inv(sqrtm(cov2)) @ sqrtm(t) @ inv(sqrtm(cov2))


# Square root decomposition
# implements the SQRT method method in the paper The Linear Monge-Kantorovitch Linear Colour Mapping for Example-Based Colour Transfer by F. Pitie et al.
def trans_sqrt(cov1, cov2):
    return sqrtm(cov1) @ inv(sqrtm(cov2))


# implements the color space transform between RGB and l-alpha-beta in the papers
# Color Transfer between Images by Erik Reinhard et al. and
# Statistics of cone responses to natural images:implications for visual coding by Daniel L. Ruderman et al.
RGB2XYZ = np.array([
    [0.5141, 0.3239, 0.1604],
    [0.2651, 0.6702, 0.0641],
    [0.0241, 0.1228, 0.8444]
])
XYZ2LMS = np.array([
    [0.3897, 0.6890, -0.0787],
    [-0.2298, 1.1834, 0.0464],
    [0, 0, 1]
])
RGB2LMS = XYZ2LMS @ RGB2XYZ
LMS2RGB = inv(RGB2LMS)
lgLMS2lab = np.diag([1 / np.sqrt(3), 1 / np.sqrt(6), 1 / np.sqrt(2)]) @ np.array([
    [1, 1, 1],
    [1, 1, -2],
    [1, -1, 0]
])
lab2lgLMS = inv(lgLMS2lab)


def rgb2lab(img):
    return np.log10(img @ RGB2LMS.T + 1e-12) @ lgLMS2lab.T # add a very small number to avoid log(0) error


def lab2rgb(img):
    return (10 ** (img @ lab2lgLMS.T)) @ LMS2RGB.T


def main():
    color_space_from = cv2.COLOR_BGR2RGB
    color_space_to = cv2.COLOR_RGB2BGR

    img1 = cv2.imread('./inputs/Trafo-Galerie-in-Prague.jpg')
    img2 = cv2.imread('./inputs/Stained-glass-window-in-St.-Vitus-Cathedral.jpg')

    img1 = cv2.cvtColor(img1, color_space_from)
    img2 = cv2.cvtColor(img2, color_space_from)

    result = color_trans_linear(rgb2lab(img1), rgb2lab(img2), trans_indep)
    result = lab2rgb(result)
    result = cv2.cvtColor(cv2.convertScaleAbs(result), color_space_to)
    cv2.imwrite('./outputs/indep.jpg', result)

    result = color_trans_linear(img1, img2, trans_cholesky)
    result = cv2.cvtColor(cv2.convertScaleAbs(result), color_space_to)
    cv2.imwrite('./outputs/cholesky.jpg', result)

    result = color_trans_linear(img1, img2, trans_sqrt)
    result = cv2.cvtColor(cv2.convertScaleAbs(result), color_space_to)
    cv2.imwrite('./outputs/sqrt.jpg', result)

    result = color_trans_linear(img1, img2, trans_mk)
    result = cv2.cvtColor(cv2.convertScaleAbs(result), color_space_to)
    cv2.imwrite('./outputs/mk.jpg', result)

    result = color_trans_linear(img1, img2, trans_svd)
    result = cv2.cvtColor(cv2.convertScaleAbs(result), color_space_to)
    cv2.imwrite('./outputs/svd.jpg', result)
    return


if __name__ == '__main__':
    main()
