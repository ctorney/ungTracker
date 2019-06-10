import os, sys, glob
import csv
import cv2
import yaml
import numpy as np

import time
from yolo_detector import yoloDetector
from yolo_tracker import yoloTracker
from utils.utils import md5check


def main(argv):
    if(len(sys.argv) != 3):
        print('Usage ./runTracker.py [data_dir] [config.yml]')
        sys.exit(1)
    #Load data
    data_dir = argv[1]  + '/' #in case we forgot '/'
    print('Opening file' + argv[2])
    with open(argv[2], 'r') as configfile:
        config = yaml.safe_load(configfile)

    tracking_setup = config["tracking_setup"]

    np.set_printoptions(suppress=True)
    data_dir = data_dir + config['movie_dir']

    videos_list= data_dir + config[tracking_setup]['videos_list']

    weights_dir = data_dir + config['weights_dir']
    weights = weights_dir + config[tracking_setup]['weights']
    md5check(config[tracking_setup]['weights_md5'],weights)

    step_frames=config[tracking_setup]['step_frames']
    obj_thresh=config[tracking_setup]['obj_thresh']
    nms_thresh=config[tracking_setup]['nms_thresh']
    max_age_val=config[tracking_setup]['max_age']
    track_thresh_val=config[tracking_setup]['track_thresh']
    init_thresh_val=config[tracking_setup]['init_thresh']
    init_nms_val=config[tracking_setup]['init_nms']
    link_iou_val=config[tracking_setup]['link_iou']

    max_l=config['MAX_L'] #maximal object size in pixels
    min_l=config['MIN_L']
    im_width=config['IMAGE_W'] #size of training imageas for yolo
    im_height=config['IMAGE_H']


    save_output = config['save_output']
    showDetections = config['showDetections']

    #READ IN A FILE LIST TODO
    with open(videos_list, 'r') as video_config_file_h:
        video_config = yaml.safe_load(video_config_file_h)

    filelist = video_config
    print(yaml.dump(filelist))

    for input_file_dict in filelist:

        input_file = data_dir + input_file_dict["filename"]

        direct, ext = os.path.split(input_file)
        noext, _ = os.path.splitext(ext)



        print("Loading " + str(len(input_file_dict["periods"])) + " predefined periods for tracking...")
        for period in input_file_dict["periods"]:
            print(period["clipname"], period["start"], period["stop"])
            data_file = data_dir + '/tracks/' +  noext + "_" + period["clipname"] + '_POS.txt'
            video_file = data_dir + '/tracks/' +  noext + "_" + period["clipname"] + '_TR.avi'
            print(input_file, video_file)
            if os.path.isfile(data_file):
                print("File already analysed, dear sir. Remove output files to redo")
                continue

            cap = cv2.VideoCapture(input_file)
            fps = round(cap.get(cv2.CAP_PROP_FPS))
            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            S = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
            ##########################################################################
            ##          set-up yolo detector and tracker
            ##########################################################################
            #detector = yoloDetector(width, height, wt_file = weights, obj_threshold=0.05, nms_threshold=0.5, max_length=100)
            #tracker = yoloTracker(max_age=30, track_threshold=0.5, init_threshold=0.9, init_nms=0.0, link_iou=0.1)
            detector = yoloDetector(width, height, wt_file = weights, obj_threshold=obj_thresh, nms_threshold=nms_thresh, max_length=100) #TODO max_length?

            tracker = yoloTracker(max_age=max_age_val, track_threshold=track_thresh_val, init_threshold=init_thresh_val, init_nms=init_nms_val, link_iou=link_iou_val)

            results = []


            ##########################################################################
            ##          open the video file for inputs and outputs
            ##########################################################################
            if save_output:
                fourCC = cv2.VideoWriter_fourcc('X','V','I','D')
                out = cv2.VideoWriter(video_file, fourCC, 5, S, True)


            ##########################################################################
            ##          corrections for camera motion
            ##########################################################################
    #       warp_mode = cv2.MOTION_AFFINE
            #warp_mode = cv2.MOTION_HOMOGRAPHY
    #       number_of_iterations = 20
            # Specify the threshold of the increment in the correlation coefficient between two iterations
    #       termination_eps = 1e-6;
            # Define termination criteria
    #        criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, number_of_iterations,  termination_eps)

    #       im1_gray = np.array([])
    #      warp_matrix = np.eye(3, 3, dtype=np.float32) 
    #      warp_matrix = np.eye(2, 3, dtype=np.float32) 
    #     full_warp = np.eye(3, 3, dtype=np.float32)

            ###::. Loading Transformations .::###
            tr_file = data_dir + input_file_dict["transform"]
            print("Loading transformations from " + tr_file)
            if os.path.isfile(tr_file):
                save_warp = np.load(tr_file)
                print("done!")
            else:
                save_warp = None
                print(":: oh dear! :: No transformations found.")




            frame_idx=0
            nframes = round(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            for i in range(nframes):

                ret, frame = cap.read()
                sys.stdout.write('\r')
                sys.stdout.write("[%-20s] %d%% %d/%d" % ('='*int(20*i/float(nframes)), int(100.0*i/float(nframes)), i,nframes))
                sys.stdout.flush()

                #jump frames
                if (i%step_frames)!=0 and i < period["start"]:
                    continue
                if i > period["stop"] and period["stop"] != 0:
                    break


            #   if not(im1_gray.size):
                    # enhance contrast in the image
            #       im1_gray = cv2.equalizeHist(cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY))#[200:-200,200:-200])

            #   im2_gray =  cv2.equalizeHist(cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY))#[200:-200,200:-200])


            #   start=time.time()
            #   try:
            #       # find difference in movement between this frame and the last frame
            #       (cc, warp_matrix) = cv2.findTransformECC(im1_gray,im2_gray,warp_matrix, warp_mode, criteria)
            #       # this frame becames the last frame the next iteration
            #       im1_gray = im2_gray.copy()
            #   except cv2.error as e:
    #       #        warp_matrix = np.eye(2, 3, dtype=np.float32)
            #       warp_matrix = np.eye(3, 3, dtype=np.float32)
    #
                # all moves are accumulated into a matrix
                #full_warp = np.dot(np.vstack((warp_matrix,[0,0,1])),full_warp)
            #   full_warp = np.dot(warp_matrix,full_warp)
                if save_warp is None:
                    full_warp = np.eye(3, 3, dtype=np.float32)
                else:
                    full_warp = save_warp[i]
            #   print('ecc ', time.time()-start)

                # Run detector
                detections = detector.create_detections(frame, np.linalg.inv(full_warp))
                # Update tracker
                tracks = tracker.update(np.asarray(detections))

                if showDetections:
                    for detect in detections:
                        bbox = detect[0:4]
                        if save_output:
                            iwarp = (full_warp)
                            corner1 = np.expand_dims([bbox[0],bbox[1]], axis=0)
                            corner1 = np.expand_dims(corner1,axis=0)
                            corner1 = cv2.perspectiveTransform(corner1,iwarp)[0,0,:]
                            minx = corner1[0]
                            miny = corner1[1]
                            corner2 = np.expand_dims([bbox[2],bbox[3]], axis=0)
                            corner2 = np.expand_dims(corner2,axis=0)
                            corner2 = cv2.perspectiveTransform(corner2,iwarp)[0,0,:]
                            maxx = corner2[0]
                            maxy = corner2[1]

                            cv2.rectangle(frame, (int(minx)-2, int(miny)-2), (int(maxx)+2, int(maxy)+2),(0,0,0), 1)


                for track in tracks:
                    bbox = track[0:4]
                    if save_output:
                        iwarp = (full_warp)

                        corner1 = np.expand_dims([bbox[0],bbox[1]], axis=0)
                        corner1 = np.expand_dims(corner1,axis=0)
                        corner1 = cv2.perspectiveTransform(corner1,iwarp)[0,0,:]
                        corner2 = np.expand_dims([bbox[2],bbox[3]], axis=0)
                        corner2 = np.expand_dims(corner2,axis=0)
                        corner2 = cv2.perspectiveTransform(corner2,iwarp)[0,0,:]
                        corner3 = np.expand_dims([[bbox[0],bbox[3]]], axis=0)
        #               corner3 = np.expand_dims(corner3,axis=0)
                        corner3 = cv2.perspectiveTransform(corner3,iwarp)[0,0,:]
                        corner4 = np.expand_dims([bbox[2],bbox[1]], axis=0)
                        corner4 = np.expand_dims(corner4,axis=0)
                        corner4 = cv2.perspectiveTransform(corner4,iwarp)[0,0,:]
                        maxx = max(corner1[0],corner2[0],corner3[0],corner4[0]) 
                        minx = min(corner1[0],corner2[0],corner3[0],corner4[0]) 
                        maxy = max(corner1[1],corner2[1],corner3[1],corner4[1]) 
                        miny = min(corner1[1],corner2[1],corner3[1],corner4[1]) 

                        np.random.seed(int(track[4])) # show each track as its own colour - note can't use np random number generator in this code
                        r = np.random.randint(256)
                        g = np.random.randint(256)
                        b = np.random.randint(256)
                        cv2.rectangle(frame, (int(minx), int(miny)), (int(maxx), int(maxy)),(r,g,b), 4)
                        cv2.putText(frame, str(int(track[4])),(int(minx)-5, int(miny)-5),0, 5e-3 * 200, (r,g,b),2)

                    results.append([frame_idx, track[4], bbox[0], bbox[1], bbox[2], bbox[3]])
                frame_idx+=1

                if save_output:
            #       cv2.imshow('', frame)
            #       cv2.waitKey(10)
                    frame = cv2.resize(frame,S)
                #   im_aligned = cv2.warpPerspective(frame, full_warp, (S[0],S[1]), borderMode=cv2.BORDER_TRANSPARENT, flags=cv2.WARP_INVERSE_MAP)
                    out.write(frame)

                #cv2.imwrite('pout' + str(i) + '.jpg',frame)
        #   break

            with open(data_file, "w") as output:
                writer = csv.writer(output, lineterminator='\n')
                writer.writerows(results)
        #   break
            #   for val in results:
            #      writer.writerow([val])    



if __name__ == '__main__':
    main(sys.argv)
