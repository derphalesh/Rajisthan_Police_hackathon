from pdf2image import convert_from_path
import os
import cv2
import numpy as np
import tensorflow as tf
from ultralytics import YOLO
from paddleocr import PaddleOCR
import pandas as pd
import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

images = convert_from_path('Final_Dataset/DATASET/1ST_FRAUD(Avinash)_9623745108.pdf')
# Load the YOLO model
model = YOLO('BOUNDING_BOX/best.pt')
# Clear out_array before processing all pages
out_array = []


# Create the "pages" directory if it doesn't exist
if not os.path.exists('pages'):
    os.makedirs('pages')
for i in range(len(images)):
  images[i].save('pages/page'+str(i)+'.jpg','JPEG')
no_of_pages = 0
out_array =[]
out_array2 = []
for page_num, image_path2 in enumerate(os.listdir('pages')):
        image_path2 = os.path.join('pages', image_path2)

        try:
            # Load the image
            image = cv2.imread(image_path2)
            if image is None:
                raise Exception("Error: Unable to read the image.")
            image = image[..., ::-1]

            # Perform prediction and get results
            results = model.predict(source=image, save=False , conf=0.5 )

            # Access the bounding box coordinates for each detected table
            if len(results) > 0:
                first_result = results[0]  # Assuming the first item in the list contains the results
                bounding_boxes = first_result.boxes.xyxy
                # print(bounding_boxes)
            else:
                print("No tables detected.")

        except Exception as e:
            print(str(e))
        for l in bounding_boxes:
          x_1 = int(l[0])
          y_1 = int(l[1])
          x_2 = int(l[2])
          y_2 = int(l[3])
        # print(bounding_boxes)
        im = cv2.imread(image_path2)
        cv2.imwrite('ext_im.jpg',im[y_1:y_2,x_1:x_2])
        ocr = PaddleOCR(lang = 'en')
        image_path = 'ext_im.jpg'
        image_cv = cv2.imread(image_path)
        image_height = image_cv.shape[0]
        image_width = image_cv.shape[1]
        output = ocr.ocr(image_path)
        # print(output)
        boxes = [line[0] for sublist in output for line in sublist]
        texts = [line[1][0] for sublist in output for line in sublist]

        # If you want probabilities as well, you can do this:
        probabilities = [line[1][1] for sublist in output for line in sublist]
        # print(boxes)

        image_boxes = image_cv.copy()
        for box,text in zip(boxes,texts):
            cv2.rectangle(image_boxes, (int(box[0][0]),int(box[0][1])), (int(box[2][0]),int(box[2][1])) , (0,0,255),1)
            cv2.putText(image_boxes , text,(int(box[0][0]), int(box[0][1])),cv2.FONT_HERSHEY_SIMPLEX,1,(222,0,0),1)
        cv2.imwrite('detections.jpg' , image_boxes)
        im2 = image_cv.copy()
        horiz_boxes = []
        vert_boxes = []
        
        for box in boxes:
            x_h, x_v = 0, int(box[0][0])
            y_h, y_v = int(box[0][1]), 0

            width_h, width_v = image_width, int(box[2][0]) - int(box[0][0])
            height_h, height_v = int(box[2][1]) - int(box[0][1]), image_height
            horiz_boxes.append([x_h, y_h, x_h + width_h, y_h + height_h])
            vert_boxes.append([x_v, y_v, x_v + width_v, y_v + height_v])

            cv2.rectangle(im2,(x_h, y_h),(x_h + width_h ,y_h+height_h),(255,255,0),1)
            cv2.rectangle(im2,(x_v, y_v),(x_v + width_v ,y_v+height_v),(0,255,0),1)

        cv2.imwrite('horiz_vert.jpg',im2)
        horiz_out = tf.image.non_max_suppression(
            horiz_boxes,
            probabilities,
            max_output_size= 1000,
            iou_threshold= 0.1,
            score_threshold = float('-inf'),
            name = None
        )
        horiz_lines = np.sort(np.array(horiz_out))
        # print(horiz_lines)
        im_nms = image_cv.copy()
        for val in horiz_lines:
            cv2.rectangle(im_nms, (int(horiz_boxes[val][0]),int(horiz_boxes[val][1])), (int(horiz_boxes[val][2]),int(horiz_boxes[val][3])) , (0,0,255),1)
        cv2.imwrite('im_nms.jpg',im_nms)
        vert_out = tf.image.non_max_suppression(
            vert_boxes,
            probabilities,
            max_output_size= 1000,
            iou_threshold= 0.1,
            score_threshold = float('-inf'),
            name = None
        )
        # print(vert_out)
        vert_lines = np.sort(np.array(vert_out))
        # print(vert_lines)
        for val in vert_lines:
            cv2.rectangle(im_nms, (int(vert_boxes[val][0]),int(vert_boxes[val][1])), (int(vert_boxes[val][2]),int(vert_boxes[val][3])) , (255,0,0),1)
        cv2.imwrite('im_nms.jpg',im_nms)
        out_array = [["" for i in range(len(vert_lines))] for j in range(len(horiz_lines))]
        # print(np.array(out_array).shape)
        # print(out_array)
        unordered_boxes = []
        for i in vert_lines:
            # print(vert_boxes[i])
            unordered_boxes.append(vert_boxes[i][0])
        ordered_boxes = np.argsort(unordered_boxes)
        # print(ordered_boxes)
        def intersection(box_1 , box_2):
            return [box_2[0], box_1[1] , box_2[2] , box_1[3] ]
        def iou(box_1 , box_2 ,):
          x_1 = max(box_1[0],box_2[0])
          y_1 = max(box_1[1],box_2[1])
          x_2 = min(box_1[2],box_2[2])
          y_2 = min(box_1[3],box_2[3])
        
          inter = abs(max((x_2 - x_1, 0)) * max ((y_2 - y_1), 0))
          if inter == 0 :
            return 0
          box_1_area = abs((box_1[2] - box_1[0]) * (box_1[3] - box_1[1]))
          box_2_area = abs((box_2[2] - box_2[0]) * (box_2[3] - box_2[1]))
          return inter / float (box_1_area + box_2_area - inter)
        page_data = []
        for i in range(len(horiz_lines)):
            row_data = []
            for j in range(len(vert_lines)):
                resultant = intersection(horiz_boxes[horiz_lines[i]],vert_boxes[vert_lines[ordered_boxes[j]]])
                cell_text = ""
                for b in range (len(boxes)):
                    the_box = [boxes[b][0][0],boxes[b][0][1],boxes[b][2][0],boxes[b][2][1]]
                    if(iou(resultant , the_box)>0.1):
                        out_array[i][j] = texts[b]
                        cell_text = texts[b]
                        break
                row_data.append(cell_text)
            page_data.append(row_data)

        out_array2.append(out_array)
        # print(out_array2)
        no_of_pages += 1

combined_array = []
for out_array_page in out_array2:
    combined_array.extend(out_array_page)

pd.DataFrame(combined_array).to_csv('final.csv')

# Remove all pages from the "pages" folder
for image_path in os.listdir('pages'):
    if image_path.endswith('.jpg'):
        os.remove(os.path.join('pages', image_path))