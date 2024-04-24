import pandas as pd
import pickle
csv_file_path = "test.csv"


class MachineLearningClassifier:

    def transactionStatus(self):
        # This function returns a list with staus flag of transaction.
        with open('model2.pkl', 'rb') as file:
            loaded_model = pickle.load(file)
        df = pd.read_csv(csv_file_path)
        columns_to_be_dropped = ['TransactionID', 'MerchantID', 'CustomerID', 'Name', 'Age', 'Address']
        df = df.drop(columns_to_be_dropped, axis=1)
        df['Timestamp1'] = pd.to_datetime(df['Timestamp'])
        df['Hour'] = df['Timestamp1'].dt.hour
        df['LastLogin'] = pd.to_datetime(df['LastLogin'])
        df['gap'] = (df['Timestamp1'] - df['LastLogin']).dt.days.abs()
        df = df.drop(['FraudIndicator', 'Timestamp','Timestamp1', 'LastLogin'], axis=1)


        all_categories = ['Online', 'Other', 'Travel', 'Food','Retail']
        for category in all_categories:
            new_column_name = f'Category_{category}'
            df[new_column_name] = (df['Category'] == category).astype(int)

        df.drop('Category', axis=1, inplace=True)
        fix_order = ['TransactionAmount', 'AnomalyScore', 'Amount', 'AccountBalance', 'SuspiciousFlag', 'Hour','gap', 'Category_Food', 'Category_Online', 'Category_Other', 'Category_Retail', 'Category_Travel']

        df = df.reindex(columns=fix_order)
        probabilities = loaded_model.predict_proba(df)
        probabilities_list = list(probabilities)
        status_list = []


        for i in range(len(probabilities_list)):
            if probabilities_list[i][0] > probabilities_list[i][1]:
                status_list.append("Valid")

                # if probabilities_list[i][0] > 0.95:
                #     status_list.append("Valid")
                # else:
                #     status_list.append("Suspicious")

            else:
                if probabilities_list[i][1] > 0.95:
                    status_list.append("Fradulent")

                else:
                    status_list.append("Suspicious")
        return status_list

    def returnTransactionIDWithStatus(self):
        # This function returns a dictionary which contains transaction id with their status.
        l = self.transactionStatus()
        transactionStatusWithID = {}
        df = pd.read_csv(csv_file_path)
        transaction_ids = df['TransactionID'].tolist()
        for i in range(len(transaction_ids)):
            transactionStatusWithID[str(transaction_ids[i])] = l[i]
        return transactionStatusWithID

    def returnTransactionIDWithStatusAndFromTo(self):
        # This function returns a dictionary which contains transaction id with their status and from which account to which account information.
        l = self.transactionStatus()
        transactionIDWithStatusAndFromTo = {}
        df = pd.read_csv(csv_file_path)
        transaction_ids = df['TransactionID'].tolist()
        from_ids = df['CustomerID'].tolist()
        to_ids = df['MerchantID'].tolist()
        for i in range(len(transaction_ids)):
            transactionIDWithStatusAndFromTo[str(transaction_ids[i])] = {"Status" : l[i] , "From" : str(from_ids[i]) , "To" : str(to_ids[i])}
        return transactionIDWithStatusAndFromTo



if __name__ == '__main__':
    obj = MachineLearningClassifier()
    l = obj.returnTransactionIDWithStatusAndFromTo()
    print(l)

    keys_to_delete = [key for key,
                      value in l.items() if value["Status"] == "Valid"]

    for key in keys_to_delete:
        del l[key]

    print("#########################################################")
    print(l)


    # s = {1: {"Status": "Valid", "From": 1952, "To": 2701},
    #      9: {"Status": "Fradulent", "From": 1347, "To": 2612}}

    # print(s)
    # print(s[1])
    # print(s[1]["Status"])
    # print(type(s[1]["Status"]))
    # print(s[1]["From"])
    # print(type(s[1]["From"]))
    # print(s[1]["To"])
    # print(type(s[1]["To"]))
