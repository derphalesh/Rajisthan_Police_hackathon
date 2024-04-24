from tkinter import messagebox
from tkinter import filedialog
from tkinter import ttk
from tkinter import *
import os
import pandas as pd
import json
import smtplib
from PIL import Image, ImageTk
import xlsxwriter
from openpyxl.styles import PatternFill
import openpyxl

from pdf2image import convert_from_path
import os
import cv2
import numpy as np
import tensorflow as tf
from ultralytics import YOLO
from paddleocr import PaddleOCR
import pandas as pd
import os
from PIL import Image, ImageDraw
from docx import Document
import json
from docx2pdf import convert

def pdfTOCsv():
    if not os.path.exists('pages'):
        os.makedirs('pages')

    def identify_and_convert_to_image(input_file, output_folder):
        file_extension = input_file.split(".")[-1].lower()

        output_folder_path = os.path.join(os.getcwd(), output_folder)

        if not os.path.exists(output_folder_path):
            os.makedirs(output_folder_path)

        if file_extension == "pdf":
            from pdf2image import convert_from_path
            images = convert_from_path(input_file)
            for i in range(len(images)):
                images[i].save('pages/page'+str(i)+'.jpg', 'JPEG')
            print("PDF file converted to images.")

        elif file_extension == "json":
            with open(input_file, "r") as file:
                json_data = json.load(file)
            image = Image.new("RGB", (500, 300), color="white")
            draw = ImageDraw.Draw(image)
            draw.text((10, 10), json.dumps(json_data, indent=4), fill="black")
            image.save(os.path.join(output_folder_path,
                       "output_image.png"), "PNG")
            print("JSON file converted to image.")

        elif file_extension == "docx":
            convert(input_file, 'output_file4.pdf')
            from pdf2image import convert_from_path
            images = convert_from_path('output_file4.pdf')
            for i in range(len(images)):
                images[i].save('pages/page'+str(i)+'.jpg', 'JPEG')
            print("DOCX file converted to images.")

        else:
            print("Unsupported file type. Cannot convert to image.")

    # Usage example:
    identify_and_convert_to_image(
        filepath6 , "pages")
    # Load the YOLO model
    model = YOLO('BOUNDING_BOX/best.pt')
    # Clear out_array before processing all pages
    out_array = []

    no_of_pages = 0
    out_array = []
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
            results = model.predict(source=image, save=False, conf=0.5)

            # Access the bounding box coordinates for each detected table
            if len(results) > 0:
                # Assuming the first item in the list contains the results
                first_result = results[0]
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
        cv2.imwrite('ext_im.jpg', im[y_1:y_2, x_1:x_2])
        ocr = PaddleOCR(lang='en')
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
        for box, text in zip(boxes, texts):
            cv2.rectangle(image_boxes, (int(box[0][0]), int(
                box[0][1])), (int(box[2][0]), int(box[2][1])), (0, 0, 255), 1)
            cv2.putText(image_boxes, text, (int(box[0][0]), int(
                box[0][1])), cv2.FONT_HERSHEY_SIMPLEX, 1, (222, 0, 0), 1)
        cv2.imwrite('detections.jpg', image_boxes)
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

            cv2.rectangle(im2, (x_h, y_h), (x_h + width_h,
                          y_h+height_h), (255, 255, 0), 1)
            cv2.rectangle(im2, (x_v, y_v), (x_v + width_v,
                          y_v+height_v), (0, 255, 0), 1)

        cv2.imwrite('horiz_vert.jpg', im2)
        horiz_out = tf.image.non_max_suppression(
            horiz_boxes,
            probabilities,
            max_output_size=1000,
            iou_threshold=0.1,
            score_threshold=float('-inf'),
            name=None
        )
        horiz_lines = np.sort(np.array(horiz_out))
        # print(horiz_lines)
        im_nms = image_cv.copy()
        for val in horiz_lines:
            cv2.rectangle(im_nms, (int(horiz_boxes[val][0]), int(horiz_boxes[val][1])), (int(
                horiz_boxes[val][2]), int(horiz_boxes[val][3])), (0, 0, 255), 1)
        cv2.imwrite('im_nms.jpg', im_nms)
        vert_out = tf.image.non_max_suppression(
            vert_boxes,
            probabilities,
            max_output_size=1000,
            iou_threshold=0.1,
            score_threshold=float('-inf'),
            name=None
        )
        # print(vert_out)
        vert_lines = np.sort(np.array(vert_out))
        # print(vert_lines)
        for val in vert_lines:
            cv2.rectangle(im_nms, (int(vert_boxes[val][0]), int(vert_boxes[val][1])), (int(
                vert_boxes[val][2]), int(vert_boxes[val][3])), (255, 0, 0), 1)
        cv2.imwrite('im_nms.jpg', im_nms)
        out_array = [["" for i in range(len(vert_lines))]
                     for j in range(len(horiz_lines))]
        # print(np.array(out_array).shape)
        # print(out_array)
        unordered_boxes = []
        for i in vert_lines:
            # print(vert_boxes[i])
            unordered_boxes.append(vert_boxes[i][0])
        ordered_boxes = np.argsort(unordered_boxes)
        # print(ordered_boxes)

        def intersection(box_1, box_2):
            return [box_2[0], box_1[1], box_2[2], box_1[3]]

        def iou(box_1, box_2,):
            x_1 = max(box_1[0], box_2[0])
            y_1 = max(box_1[1], box_2[1])
            x_2 = min(box_1[2], box_2[2])
            y_2 = min(box_1[3], box_2[3])

            inter = abs(max((x_2 - x_1, 0)) * max((y_2 - y_1), 0))
            if inter == 0:
                return 0
            box_1_area = abs((box_1[2] - box_1[0]) * (box_1[3] - box_1[1]))
            box_2_area = abs((box_2[2] - box_2[0]) * (box_2[3] - box_2[1]))
            return inter / float(box_1_area + box_2_area - inter)
        page_data = []
        for i in range(len(horiz_lines)):
            row_data = []
            for j in range(len(vert_lines)):
                resultant = intersection(
                    horiz_boxes[horiz_lines[i]], vert_boxes[vert_lines[ordered_boxes[j]]])
                cell_text = ""
                for b in range(len(boxes)):
                    the_box = [boxes[b][0][0], boxes[b][0]
                               [1], boxes[b][2][0], boxes[b][2][1]]
                    if(iou(resultant, the_box) > 0.1):
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

    pd.DataFrame(combined_array).to_csv(
        'CONVERTEDCSV/NewCsv.csv')

    # Remove all pages from the "pages" folder
    for image_path in os.listdir('pages'):
        if image_path.endswith('.jpg'):
            os.remove(os.path.join('pages', image_path))




def returnPercentage(amount):
    ''' 
    This function takes value as an argument and if value is between(10 to 10000) then return 5%
    else if value is between (10001 to 100000) then return percentage equal to 10.
    '''
    if amount in range(10001, 100001):
        return 0.05
    else:
        return 0.1


def updateCommonAccount(accNo):
    '''
    This function is used to store common account count.
    '''
    file = open("GUI_files/commonAccount.txt", "r")
    content = file.read()
    file.close()
    account_dict = json.loads(content)
    if accNo in account_dict:
        count = account_dict[accNo]
        account_dict[accNo] = count+1
    else:
        account_dict[accNo] = 1
    file = open("GUI_files/commonAccount.txt", 'w')
    json.dump(account_dict, file)
    file.close()


def login():
    user = username.get()
    pas = password.get()

    if user == "admin" and pas == "admin":
        app.destroy()
        optionMenu()
    elif user == "" and pas == "":
        messagebox.showerror("Invalid", "Please enter Username and Password")
    elif user == "":
        messagebox.showerror("Invalid", "Username is required")
    elif pas == "":
        messagebox.showerror("Invalid", "Password is required")
    elif user != "admin" and pas != "admin":
        messagebox.showerror(
            "Invalid", "Please enter valid Username and Password")
    elif user != "admin":
        messagebox.showerror(
            "Invalid", "Please enter valid Username ")
    elif pas != "admin":
        messagebox.showerror(
            "Invalid", "Please enter valid Password")


def addCase():
    try:
        file = open("GUI_files/allCases.txt", "r")
        content = file.read()
        account_dict = json.loads(content)
        file.close()
    except:
        account_dict = {}

    c_no = int(caseNumber.get())
    if caseNumber.get() in account_dict:
        messagebox.showerror(
            "Invalid", "Case already exists")
        return True
    else:
        account_dict[int(c_no)] = "Pending"
        file = open("GUI_files/allCases.txt", 'w')
        json.dump(account_dict, file)
        file.close()
        return False


def is_folder_empty(folder_path):
    return not any(os.listdir(folder_path))

def open_file():

    folder_path = 'CONVERTEDCSV'

    if is_folder_empty(folder_path):
        messagebox.showerror("Invalid", "No dataset available.Please  provide a dataset...")
        global fraud_account_no
        global filepath6
        status = addCase()
        if(status == False):
            global filepath
            file = filedialog.askopenfile(
                mode='r', filetypes=[('Bank Statements', '*.pdf')])
            if file:
                filepath = os.path.abspath(file.name)
                filepath6 = filepath
                filepath = str(filepath)
            print(filepath)
            filepath = filepath.replace(".pdf", ".csv")

            df = pd.read_csv(filepath)

            t_id = int(transactionId.get())
            result_transaction = df[df['TRANSACTION ID'] == t_id]
            account_no = result_transaction.iloc[0, 3]
            fraud_account_no = int(account_no)
            account_dict = {int(account_no): 1}

            file = open("GUI_files/commonAccount.txt", 'w')
            json.dump(account_dict, file)
            file.close()
            # dict = {"DATE": date.get(), "TRANSACTION ID": transactionId.get(),
            #         "ACCOUNT NO.": int(account_no)}
            dict = {"TRANSACTION ID": transactionId.get(),
                    "ACCOUNT NO.": int(account_no)}
            dct2 = {str(int(account_no)): "Red"}
            file = open('GUI_files/mainReport.txt', 'a')
            file.write(json.dumps(dict))
            file.write("\n")
            file.write(json.dumps(dct2))
            file.close()

            fraudIdLabel.config(text=f"Fradulent Account : {fraud_account_no}")
            pdfTOCsv()
    else:
        caseResult()
        


def sendAcutalMail():
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login("pranu11v@gmail.com", "ybqjlvcgyeguneoo")
    s.sendmail("pranu11v@gmail.com", e_email.get(), sub)
    s.quit()
    messagebox.showinfo("Sent successfully", "Email sent successfully...")
    sendMail_app.destroy()


def send_mail_func():
    global e_email
    global sub
    global sendMail_app
    sub = f"Respected Sir/Madam\nPlease provide us with the bank statement for account {fraud_account_no}, because\nwe found some suspicious transaction happened to this account.\nThank you.\nBest regards\n Cyber Cell"

    sendMail_app = Tk()
    sendMail_app.geometry("620x300")
    e_email = StringVar()
    frame = Frame(
        sendMail_app, width=600, height=470)
    frame.pack()
    label1 = Label(
        frame, text="E-mail", font=("verdana", 12))
    label1.place(x=50, y=50)
    email_entry = Entry(
        frame, width=60, textvariable=e_email)

    email_entry.place(x=150, y=55)
    text = Text(frame, width=225, height=6)
    text.insert("1.0", sub)
    text.place(x=10, y=100)

    send_button = Button(frame, text="Send Mail",
                         font=("verdana", 10, "bold"), height=1, command=sendAcutalMail)
    send_button.place(x=150, y=220)
    sendMail_app.mainloop()


def createCase():
    optionMenu_app.destroy()
    global caseNumber
    global date
    global acccountNumber
    global amount
    global transactionId
    global createCase_app
    global fraudIdLabel
    createCase_app = Tk()
    createCase_app.geometry("1000x580")
    createCase_app.resizable(False,False)
    img1=ImageTk.PhotoImage(Image.open("create_case_window.png"))
    img2=ImageTk.PhotoImage(Image.open("upload_statement.png"))
    img3=ImageTk.PhotoImage(Image.open("reqMail.png"))
    img4=ImageTk.PhotoImage(Image.open("create_Back.png"))
    l1=Label(master=createCase_app,image=img1)
    l1.pack()

    
    caseNumber = StringVar()
    transactionId = StringVar()


    transactionIdEntry = Entry(
        l1, width=60, textvariable=transactionId)

    transactionIdEntry.place(x=500, y=227)

    nameEntry = Entry(
        l1, width=60, textvariable=caseNumber)
    nameEntry.place(x=500, y=141)

    button = Button(
        l1,command=open_file, font=("verdana", 16),highlightthickness=0,borderwidth=0,height=55,width=150,image=img2)
    button.place(x=520, y=340)

    back_button = Button(
        l1, command=back_to_optionMenu, font=("verdana", 16),highlightthickness=0,borderwidth=0,height=35,width=150,image=img4)
    
    back_button.place(x=790, y=510)

    send_mail = Button(
        l1, command=send_mail_func, font=("verdana", 16),highlightthickness=0,borderwidth=0,height=55,width=150,image=img3)
    
    send_mail.place(x=755, y=340)

    fraudIdLabel = Label(
        l1, text="", font=("verdana", 18), fg="red",bg="#DFDFDF")
    fraudIdLabel.place(x=500, y=410)

    createCase_app.mainloop()


def back_to_optionMenu2():
    app2.destroy()
    optionMenu()


def back_to_optionMenu3():
    resumeCaseDashboard_app.destroy()
    optionMenu()

def back_to_optionMenu4():
    showCases_app.destroy()
    optionMenu()


def markDone():
    file = open("GUI_files/allCases.txt", "r")
    content = file.read()
    file.close()
    account_dict = json.loads(content)
    account_dict[caseNo.get()] = "Done"
    file = open("GUI_files/allCases.txt", 'w')
    json.dump(account_dict, file)
    file.close()
    resumeCaseDashboard_app.destroy()
    optionMenu()

def plot_graph(file):
    img_path = f"Dataset/{file}.png"
    def resize_and_display_image2(img_path, window_name, max_width, max_height):
        # Read the image
        image = cv2.imread(img_path)

        # Get the dimensions of the image
        image_height, image_width = image.shape[:2]

        # Calculate the scaling factor to fit the image within the specified dimensions
        scale_factor = min(max_width / image_width, max_height / image_height)

        # Resize the image
        resized_image = cv2.resize(image, None, fx=scale_factor, fy=scale_factor)

        # Display the resized image in a new window
        cv2.imshow(window_name, resized_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    # Specify the path to the image file

    # Set the maximum dimensions for the display window
    max_display_width = 1200
    max_display_height = 1000

    # Call the function to resize and display the image
    resize_and_display_image2(img_path, 'Resized Image', max_display_width, max_display_height)


def generateOneReport(dataframe):
    global abhishek_transaction_status
    first_dataframe = dataframe.iloc[[0]]
    value = int(first_dataframe["AMOUNT"])
    percent = returnPercentage(value)
    temp = value

    after_credited_abhishek_df = dataframe.iloc[1:].fillna(0)
    after_credited_abhishek_df.drop(
        after_credited_abhishek_df[after_credited_abhishek_df["STATUS"] == "Cr"].index, inplace=True)
    after_credited_abhishek_df_to_list = after_credited_abhishek_df.values.tolist()
    abhishek_transaction_status = {}
    for i in after_credited_abhishek_df_to_list:
        if i[2] == "UPI(Transfer to Genuine Account)":
            if i[3] == 0:
                abhishek_transaction_status[str(
                    (int(fraud_ac_no.get()), "Withdrawal"))] = "Green"
            else:
                abhishek_transaction_status[str(
                    (int(fraud_ac_no.get()), int(i[3])))] = "Green"
            continue

        if i[5] >= int(percent*value) and i[4] == 'Dr':
            if temp > 0:
                temp = temp-i[5]

                if i[3] == 0:
                    abhishek_transaction_status[str(
                        (int(fraud_ac_no.get()), "Withdrawal"))] = "Orange"
                else:
                    updateCommonAccount(str(int(i[3])))
                    abhishek_transaction_status[str(
                        (int(fraud_ac_no.get()), int(i[3])))] = "Orange"

        else:
            if i[3] == 0:
                abhishek_transaction_status[str(
                    (int(fraud_ac_no.get()), "Withdrawal"))] = "Green"
            else:
                abhishek_transaction_status[str(
                    (int(fraud_ac_no.get()), int(i[3])))] = "Green"
    file = open('GUI_files\mainReport.txt', 'a')
    file.write("\n")
    file.write(json.dumps(abhishek_transaction_status))
    file.close()

    
    populate_table(abhishek_transaction_status)


def open_file2():
    try:
        abhishek_transaction_status.clear()
    except:
        pass
    global filepath2
    file = filedialog.askopenfile(
        mode='r', filetypes=[('Bank Statements', '*.pdf')])
    if file:
        filepath2 = os.path.abspath(file.name)
        filepath2 = str(filepath2)
    print(filepath2)
    filepath2 = filepath2.replace(".pdf", ".csv")
    df = pd.read_csv(filepath2)
    print(df)
    generateOneReport(df)


def populate_table(data):
    for item in tree.get_children():
        tree.delete(item)
    tree.tag_configure('green_col',background='lawn green')
    tree.tag_configure('orange_col',background='tan1')
    tags = 'orange_col'


    for key, value in data.items():
        if(value=='Green'):
            tags='green_col'
        else:
            tags='orange_col'
        tree.insert('', 'end', values=(key, value),tags=(tags))
    plot_graph(fraud_ac_no.get())


def downloadReport():
    folder_path = 'Report'
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)
    
    report_file_name = f"{caseNo.get()}report{fraud_ac_no.get()}.txt"
    report_file_name_workbook = xlsxwriter.Workbook(
        f"{caseNo.get()}report{fraud_ac_no.get()}.xlsx")
    com_path = os.path.join(folder_path, report_file_name)
    com_path2 = os.path.join(folder_path, report_file_name)
    worksheet = report_file_name_workbook.add_worksheet()
    row = 0
    column = 0

    for x in abhishek_transaction_status:
        worksheet.write(row, column, x)
        worksheet.write(row, column+1, abhishek_transaction_status[x])
        row += 1

    report_file_name_workbook.close()

    file = open(com_path, 'w')
    file.write(str(json.dumps(abhishek_transaction_status)))

    file.close()
    messagebox.showinfo("Downloaded successfully..",
                        f"file saved to location {folder_path}{report_file_name}")


# def sendAcutalMail2():
#     subject = f"Respected Sir/Madam\nPlease provide us with the bank statement for account {acc2.get()} , because\nwe found some suspicious transaction happened to this account.\nThank you.\nBest regards\n Cyber Cell"
#     s = smtplib.SMTP('smtp.gmail.com', 587)
#     s.starttls()
#     s.login("pranu11v@gmail.com", "ybqjlvcgyeguneoo")
#     s.sendmail("pranu11v@gmail.com", email2.get(), subject)
#     s.quit()


def sendAcutalMail2():

    # Content of the email (pre-drafted)
    subject = f"Respected Sir/Madam\nPlease provide us with the bank statement for account {acc2.get()} , because\nwe found some suspicious transaction happened to this account.\nThank you.\nBest regards\n Cyber Cell"

    # Sender's email and password (replace these with your own)
    sender_email = "pranu11v@gmail.com"
    sender_password = "ybqjlvcgyeguneoo"

    # try:
    #     server = smtplib.SMTP("smtp.gmail.com", 587)
    #     server.starttls()
    #     server.login(sender_email, sender_password)
    #     server.sendmail(sender_email, email2.get(), subject)
    #     server.quit()

    # except smtplib.SMTPAuthenticationError:
    #     pass
    # except Exception as e:
    #     pass
    messagebox.showinfo("Sent successfully", "Email sent successfully...")
    sendMail_app_2.destroy()


def send_mail_Accounts():
    subject = f"Respected Sir/Madam\nPlease provide us with the bank statement for account , because\nwe found some suspicious transaction happened to this account.\nThank you.\nBest regards\n Cyber Cell"
    global email2
    global acc2
    global sendMail_app_2

    sendMail_app_2 = Tk()
    sendMail_app_2.geometry("620x300")
    email2 = StringVar()
    acc2 = StringVar()

    frame = Frame(
        sendMail_app_2, width=600, height=470)
    frame.pack()
    label1 = Label(
        frame, text="E-mail", font=("verdana", 12))
    label1.place(x=40, y=50)
    email_entry = Entry(
        frame, width=35, textvariable=email2)
    email_entry.place(x=110, y=55)

    label2 = Label(
        frame, text="Acc No.", font=("verdana", 12))
    label2.place(x=340, y=50)

    acc_entry = Entry(
        frame, width=25, textvariable=acc2)
    acc_entry.place(x=420, y=55)

    text = Text(frame, width=225, height=6)
    text.insert("1.0", subject)
    text.place(x=10, y=100)

    send_button = Button(frame, text="Send Mail",
                         font=("verdana", 10, "bold"), height=1, command=sendAcutalMail2)
    send_button.place(x=230, y=220)
    sendMail_app_2.mainloop()


# def resumeCaseApproval():
#     try:
#         file = open("GUI_files\\allCases.txt", "r")
#         content = file.read()
#         account_dict = json.loads(content)
#         file.close()
#     except:
#         print("no such file exists")

#     if resume_case_entry.get() in account_dict:
#         if account_dict[resume_case_entry.get()] == "Pending":
#             app2.destroy()
#             global tree
#             global resumeCaseDashboard_app
#             global fraud_ac_no
#             resumeCaseDashboard_app = Tk()

#             resumeCaseDashboard_app.geometry("750x534")
#             case_lab = Label(resumeCaseDashboard_app, text=f"Case Number: {caseNo.get()}",
#                              font=("verdana", 15)).place(x=25, y=25)

#             mark_done = Button(resumeCaseDashboard_app,
#                                text="Case Completed", font=("verdana", 14, "bold"), command=markDone).place(x=275, y=20)

#             back_but = Button(resumeCaseDashboard_app,
#                               text="Back to Option Menu", font=("verdana", 14, "bold"), command=back_to_optionMenu3).place(x=475, y=20)

#             frame = Frame(resumeCaseDashboard_app,
#                           width=700, height=280, bg="cyan")
#             frame.pack(padx=(25, 25), pady=(80, 150))

#             l = Label(frame, text="REPORT WINDOW", font=(
#                 "verdana", 15, "bold")).place(x=5, y=5)

#             l2 = Label(frame, text="Account Number", font=(
#                 "verdana", 12)).place(x=320, y=10)
#             fraud_ac_no = StringVar()
#             fraud_ac_no_entry = Entry(
#                 frame, textvariable=fraud_ac_no, width=30).place(x=470, y=10)

#             tree = ttk.Treeview(frame, columns=('Key', 'Value'),
#                                 show='headings')

#             tree.heading('Key', text='(From , To)')
#             tree.heading('Value', text='Status')

#             tree.column('Key', width=220, anchor='c')
#             tree.column('Value', width=220, anchor='c')
#             tree.place(x=140, y=45)

#             upload_butt = Button(resumeCaseDashboard_app,
#                                  text="Upload Statement", font=("verdana", 14, "bold"), command=open_file2).place(x=250, y=380)

#             download_report_butt = Button(
#                 resumeCaseDashboard_app, text="Download Report", font=("verdana", 14, "bold"), command=downloadReport).place(x=125, y=430)

#             request_bank_butt = Button(
#                 resumeCaseDashboard_app, text="Request Bank Statement", font=("verdana", 14, "bold"), command=send_mail_Accounts).place(x=350, y=430)

#             resumeCaseDashboard_app.mainloop()

#         else:
#             messagebox.showerror(
#                 "Invalid", f"Case {resume_case_entry.get()} Investigation is completed.")

#     else:
#         messagebox.showerror(
#             "Invalid", f"No such Case {resume_case_entry.get()} exists")
def resumeCaseApproval():
    try:
        file = open("allCases.txt", "r")
        content = file.read()
        account_dict = json.loads(content)
        file.close()
    except:
        print("no such file exists")

    if resume_case_entry.get() in account_dict:
        if account_dict[resume_case_entry.get()] == "Pending":
            app2.destroy()
            global tree
            global resumeCaseDashboard_app
            global fraud_ac_no
            resumeCaseDashboard_app = Tk()

            resumeCaseDashboard_app.geometry("1000x580")
            resumeCaseDashboard_app.resizable(False,False)

            upload_window=ImageTk.PhotoImage(Image.open("report_window_img.png"))
            back_to_optionMenu_btn=ImageTk.PhotoImage(Image.open("backTooptions.png"))
            mark_done_btn=ImageTk.PhotoImage(Image.open("caseCompleted.png"))
            request_btn=ImageTk.PhotoImage(Image.open("Request_Bank_Statement.png"))
            download_btn=ImageTk.PhotoImage(Image.open("download_img.png"))
            upload_btn=ImageTk.PhotoImage(Image.open("upload_report_img.png"))
            l1=Label(master=resumeCaseDashboard_app,image=upload_window)
            l1.pack()

            case_lab = Label(l1, text=f"Case Number: ", font=("verdana", 15),background="#FFFFFF")
            # {caseNo.get()}
            case_lab.place(x=165, y=55)

            mark_done = Button(l1,highlightthickness=0,borderwidth=0,height=35,width=270,image=mark_done_btn, command=markDone)
            # 
            mark_done.place(x=395, y=25)

            back_but = Button(l1,highlightthickness=0,borderwidth=0,height=35,width=270,image=back_to_optionMenu_btn, command=back_to_optionMenu3)
            # 
            back_but.place(x=395, y=77)

            # frame = Frame(resumeCaseDashboard_app,
            #               width=700, height=280, bg="cyan")
            # frame.pack(padx=(25, 25), pady=(80, 150))


            fraud_ac_no = StringVar()
            fraud_ac_no_entry = Entry(l1, textvariable=fraud_ac_no, width=20)
            fraud_ac_no_entry.place(x=185, y=103)

            tree = ttk.Treeview(l1, columns=('Key', 'Value'),
                                show='headings')

            tree.heading('Key', text='(From , To)')
            tree.heading('Value', text='Status')

            tree.column('Key', width=220, anchor='c')
            tree.column('Value', width=220, anchor='c')
            tree.place(x=140, y=155)

            upload_butt = Button(resumeCaseDashboard_app,highlightthickness=0,borderwidth=0,height=35,width=220,image=upload_btn, command=open_file2)
            # 
            upload_butt.place(x=210, y=483)

            download_report_butt = Button(resumeCaseDashboard_app,highlightthickness=0,borderwidth=0,height=35,width=220,image=download_btn, command=downloadReport)
            # 
            download_report_butt.place(x=55, y=535)

            request_bank_butt = Button(resumeCaseDashboard_app,highlightthickness=0,borderwidth=0,height=35,width=220,image=request_btn, command=send_mail_Accounts)
        
            request_bank_butt.place(x=375, y=535)

            resumeCaseDashboard_app.mainloop()

        else:
            messagebox.showerror(
                "Invalid", f"Case {resume_case_entry.get()} Investigation is completed.")

    else:
        messagebox.showerror(
            "Invalid", f"No such Case {resume_case_entry.get()} exists")


def resumeCase():
    optionMenu_app.destroy()
    global app2
    global resume_case_entry
    global caseNo
    app2 = Tk()
    app2.geometry("1000x580")
    app2.resizable(False,False)
    img1=ImageTk.PhotoImage(Image.open("Resume_case_img.png"))
    countinue_btn=ImageTk.PhotoImage(Image.open("continue_img.png"))
    back_btn=ImageTk.PhotoImage(Image.open("back_resume_img.png"))
    l1=Label(master=app2,image=img1)
    l1.pack()

    caseNo = StringVar()

    resume_case_entry = Entry(l1, width=40, textvariable=caseNo)
    resume_case_entry.place(x=375, y=250)
    button = Button(l1,highlightthickness=0,borderwidth=0,height=35,width=150,image=countinue_btn, command=resumeCaseApproval)
    button.place(x=290, y=355)
    
    button2 = Button(l1,highlightthickness=0,borderwidth=0,height=35,width=150,image=back_btn, command=back_to_optionMenu2)
    button2.place(x=540, y=355)
    
    app2.mainloop()


def populate_table2(data):
    for key, value in data.items():
        tree.insert('', 'end', values=(key, value))


def showCases():
    global showCases_app
    optionMenu_app.destroy()
    showCases_app = Tk()

    showCases_app.geometry("1000x580")
    img2=ImageTk.PhotoImage(Image.open("Back_btn_show.png"))
    img1=ImageTk.PhotoImage(Image.open("Show_Case_img.png"))
    l1 = Label(master=showCases_app,image=img1)
    l1.pack()

    # fram = Frame(showCases_app,
    #              width=450, height=270, bg="cyan")
    # fram.pack(padx=(25, 25), pady=(80, 20))

    file = open(
        "allCases.txt", "r")
    content = file.read()
    file.close()
    account_dict5 = json.loads(content)

    tree2 = ttk.Treeview(l1, columns=('Key', 'Value'),
                         show='headings')

    tree2.heading('Key', text='Case Number')
    tree2.heading('Value', text='Status')

    tree2.column('Key', width=350, anchor='c')
    tree2.column('Value', width=350, anchor='c')
    for key, value in account_dict5.items():
        tree2.insert('', 'end', values=(key, value))
    tree2.place(x=175, y=150)

    button = Button(l1,highlightthickness=0,borderwidth=0,height=45,width=150,image=img2,command=back_to_optionMenu4)
    button.place(x=420,y=495)

    showCases_app.mainloop()


def caseResult():
    def resize_and_display_image(image_path, window_name, max_width, max_height):
        # Read the image
        image = cv2.imread(image_path)

        # Get the dimensions of the image
        image_height, image_width = image.shape[:2]

        # Calculate the scaling factor to fit the image within the specified dimensions
        scale_factor = min(max_width / image_width, max_height / image_height)

        # Resize the image
        resized_image = cv2.resize(image, None, fx=scale_factor, fy=scale_factor)

        # Display the resized image in a new window
        cv2.imshow(window_name, resized_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    # Specify the path to the image file
    image_path = 'GUI_files\FINAL.jpg'

    # Set the maximum dimensions for the display window
    max_display_width = 1200
    max_display_height = 1000

    # Call the function to resize and display the image
    resize_and_display_image(image_path, 'Resized Image', max_display_width, max_display_height)

def logoutSession():
    optionMenu_app.destroy()
    main_screen()

def optionMenu():

    global optionMenu_app

    optionMenu_app = Tk()
    optionMenu_app.geometry("1000x580")
    optionMenu_app.title('Trail Master')
    optionMenu_app.resizable(False,False)

    img1=ImageTk.PhotoImage(Image.open("2nd_frame_img.png"))
    l1=Label(master=optionMenu_app,image=img1)
    l1.pack()


    # frame = Frame(
    #     optionMenu_app, width=470, height=250, bg="burlywood3")
    # frame.pack(padx=95, pady=75)

    button_create=ImageTk.PhotoImage(Image.open("Create_case.png"))
    button_resume=ImageTk.PhotoImage(Image.open("resume_Case.png"))
    button_show=ImageTk.PhotoImage(Image.open("Show_Case.png"))
    button_result=ImageTk.PhotoImage(Image.open("case_result.png"))
    button_logout=ImageTk.PhotoImage(Image.open("logout.png"))
    button1 = Button(
        l1,command=createCase,highlightthickness=0,borderwidth=0,height=56,width=150,image=button_create)
    button1.place(x=60, y=161)
    button2 = Button(
        l1, command=resumeCase,highlightthickness=0,borderwidth=0,height=56,width=150,image=button_resume)
    button2.place(x=277, y=161)
    button3 = Button(
        l1, command=showCases,highlightthickness=0,borderwidth=0,height=56,width=150,image=button_show)
    button3.place(x=66, y=271)

    button4 = Button(
        l1, command=caseResult,highlightthickness=0,borderwidth=0,height=56,width=150,image=button_result)
    button4.place(x=281, y=268)

    button5 = Button(
        l1, command=logoutSession,highlightthickness=0,borderwidth=0,height=40,width=90,image=button_logout)
    button5.place(x=842, y=512)
    optionMenu_app.mainloop()


def main_screen():
    global username
    global password
    global app

    app = Tk()
    app.geometry("1000x580")
    app.resizable(False,False)
    app.title('Trail Master')
    # app.attributes('-alpha', 0.8)

    img1=ImageTk.PhotoImage(Image.open("login_img_2.png"))
    login_img=ImageTk.PhotoImage(Image.open("login_button.png"))
    l1=Label(master=app,image=img1)
    l1.pack()

    username = StringVar()
    password = StringVar()

    usernameEntry = Entry(
        l1, width=15, textvariable=username, font=("verdana", 10))
    usernameEntry.place(x=480, y=250)

    passwordEntry = Entry(
        l1, width=15, textvariable=password, show="*", font=("verdana", 10))
    passwordEntry.place(x=480, y=285)


    button = Button(
        l1,command=login,highlightthickness=0,borderwidth=0,height=30,width=262,image=login_img)
    button.place(x=375, y=353)


    app.mainloop()


def back_to_optionMenu():
    createCase_app.destroy()
    optionMenu()


main_screen()