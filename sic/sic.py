#!/usr/bin/env python3
import argparse
import os
import numpy as np
import cv2

def parse_args():
    parser = argparse.ArgumentParser(prog='sic', description='simple image clustering based on k-means clustering')

    parser.add_argument('-i', '--infile', type=str, required=True, help='you must provide an input image to cluster it')
    parser.add_argument('-s', '--spectral', dest='spectral_switch', action='store_true', help='switch to spectral clustering mode (see documentation for details)')
    parser.add_argument('-c','--clusters', type=int, default=5, dest='num_clusters', help='choose the number of clusters to produce (default is 5) [integer]')
    parser.add_argument('-r', '--runs', type=int, default=10, dest='num_runs', help='choose the number of clustering runs to attempt (default is 10) [integer]')
    parser.add_argument('-e', '--extension', type=str, default='png', dest='extension', help='choose the filename extension of the saved clustered image (default is png) [string]')
    parser.add_argument('--version', action='version', version='%(prog)s 0.3')

    args = parser.parse_args()
    return args

def load_data(args):
    if args.spectral_switch == True:
        # load all RGB images in a folder and convert them to grayscale
        all_img = []
        path = args.infile
        os.chdir(path)
        print('Loading images from path:')
        print(str(os.getcwd()))
        directory = os.fsencode(path)
        sorted_dir = sorted(os.listdir(directory))

        for img_file in sorted_dir:
            filename = os.fsdecode(img_file)
            print(str(filename))
            if filename.endswith('.tif'):
                img = cv2.imread(filename)
                img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
                all_img.append(img)
                print(img.shape)

        # preprocessing
        # stack all images (grayscale (x,y) ) together into a single (x,y,z) array
        all_img = np.stack(all_img, axis=-1)
        global img_shape
        img_shape = all_img.shape
        print(img_shape)
        all_img = all_img.reshape(-1, img_shape[2])
        og_img = np.copy(all_img)
        all_img = np.float32(all_img)
        print(all_img.shape)

        return all_img, og_img

    elif args.spectral_switch == False:
        # load all RGB images in a folder and convert them to grayscale
        # load single RGB image
        print('Loading input image...')
        print(args.infile)
        img = cv2.imread(str(args.infile))
        img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)

        # preprocessing
        img_shape = img.shape
        img = img.reshape((-1,3))
        img = np.float32(img)
        return img

def clustering(img, args):
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    flags = cv2.KMEANS_PP_CENTERS

    print('Starting clustering...')
    compactness, labels, centers = cv2.kmeans(img, K=args.num_clusters, bestLabels=None, attempts=args.num_runs, criteria=criteria, flags=flags)
    
    centers = np.uint8(centers)
    result = centers[labels.flatten()]
    result_img = result.reshape((img_shape))
    print(result_img.shape)

    return result_img, labels

def save_img(img, args):
    if args.spectral_switch == True:
        result_img = np.mean(img, axis=2)
        print(result_img.shape)

        print('Saving clustered image to ...')
        savepath = str(args.infile)
        savepath = savepath + str(args.num_clusters) + '_CLUSTERS_ALL_WVN.' + str(args.extension)
        print(savepath)
        cv2.imwrite(savepath, result_img)

    elif args.spectral_switch == False:
        print('Saving clustered image to ...')
        savepath = str(args.infile).split('.')
        savepath = savepath[0] + '_' + str(args.num_clusters) + '_CLUSTERS.' + str(args.extension)
        print(savepath)
        result_img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        cv2.imwrite(savepath, result_img)

def spectral_selection(img, choice, labels):
    import matplotlib.pyplot as plt

    masked_img = np.copy(img)
    labels = labels.flatten()
    selection = masked_img[labels == choice]
    selection = np.array(selection)

    # plotting
    mean_intensities=[]
    for i in selection.T:
        x = np.mean(i)
        mean_intensities.append(x)

    plt.plot(mean_intensities)
    plt.xlabel('WVN')
    plt.ylabel('SRS -  Cluster intensity (a.u.)')
    savepath = str(args.infile)
    savepath = savepath + str(args.num_clusters) + '_CLUSTERS_ALL_WVN' + '_spectra_of_cluster_' + str(choice) + '.' + str(args.extension)
    plt.savefig(savepath, dpi=600)

    # .txt file creation
    txtpath = str(args.infile)+ str(args.num_clusters) + '_CLUSTERS_ALL_WVN' + '_spectra_of_cluster_' + str(choice) + '.txt' 
    f = open(txtpath, 'w')
    for mean in mean_intensities:
        f.write('%s\n' % mean)
    f.close()

def all_mean_spectra(img, labels):
    ''' plot mean spectra of all clusters and write corresponding text files for all clusters
    '''
    import matplotlib.pyplot as plt
    os.mkdir((str(args.infile) + 'mean_spectra_per_cluster_FOR_A_CLUSTERING_OF_' + str(args.num_clusters)))

    masked_img = np.copy(img)
    labels = labels.flatten()
    for i in range(args.num_clusters):
        selection = masked_img[labels == i]
        selection = np.array(selection)

        # plotting
        mean_intensities=[]
        for j in selection.T:
            x = np.mean(j)
            mean_intensities.append(x)
        
        plt.plot(mean_intensities)
        plt.xlabel('WVN')
        plt.ylabel('SRS -  Cluster intensity (a.u.)')
        plt.title('Mean spectral intensities for cluster nr. ' + str(i))
        savepath = str(args.infile) + 'mean_spectra_per_cluster_FOR_A_CLUSTERING_OF_' + str(args.num_clusters) + '/'+ str(args.num_clusters) + '_CLUSTERS_ALL_WVN' + '_spectra_of_cluster_' + str(i) + '.' + str(args.extension)
        plt.savefig(savepath, dpi=600)
        plt.clf()

        # .txt file creation
        txtpath =  str(args.infile) + 'mean_spectra_per_cluster_FOR_A_CLUSTERING_OF_' + str(args.num_clusters) + '/'+ str(args.num_clusters) + '_CLUSTERS_ALL_WVN' + '_spectra_of_cluster_' + str(i) + '.txt' 
        f = open(txtpath, 'w')
        for mean in mean_intensities:
            f.write('%s\n' % mean)
        f.close()



#######################################

if __name__ == "__main__":
    args = parse_args()
    print('Called with arguments:')
    print(args)

    if args.spectral_switch == True:
        img, og_img = load_data(args)
    elif args.spectral_switch == False:
        img = load_data(args)

    result_img, labels = clustering(img, args)

    save_img(result_img, args)

    if args.spectral_switch == True:
        all_mean_spectra(og_img, labels)

        print('\n')
        choice = int(input('Select the cluster of choice to extract a spectrum. [integer] : '))
        spectral_selection(og_img, choice, labels)

    print('Done!')

