import fundFlow as ff
import json

# with open('transactionsStatus.txt', 'r') as file:
#     loaded_dict = json.load(file)

# # print(loaded_dict)
# print(len(loaded_dict))
# fradulent_list = []
# suspicious_list = []


# keys_list = list(loaded_dict.keys())
# for i in keys_list:
#     if loaded_dict[i]["Status"] == "Fradulent":
#         fradulent_list.append(i)
#     else:
#         suspicious_list.append(i)
    
# print(suspicious_list)
# print(fradulent_list)

# for i in suspicious_list:
#     print(i , loaded_dict[str(i)]["From"])


# dic = {"sanket.patil21@vit.edu":[9,11,12,13,14]}
# print(type(dic))
# print(dic)
# print(dic["sanket.patil21@vit.edu"])
# print(type(dic["sanket.patil21@vit.edu"]))

with open('zz.txt', 'r') as file:
    loaded_dict = json.load(file)

print(loaded_dict)
print(type(loaded_dict))
print(loaded_dict["sanket.patil21@vit.edu"])
print(type(loaded_dict["sanket.patil21@vit.edu"]))
loaded_dict["sanket.patil21@vit.edu"].append(7467)
print(len(loaded_dict["sanket.patil21@vit.edu"]))




with open('zz.txt', 'w') as convert_file:
    convert_file.write(json.dumps(loaded_dict))

obj = ff.FundFlow()
dct = obj.rerturnFundFlowDictionary(9)
print(dct)
