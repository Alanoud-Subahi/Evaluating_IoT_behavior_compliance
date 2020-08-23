from __future__ import print_function
from __future__ import division
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import Extract_IoTPPA

#from dns import resolver, reversename
# run with python 2.7




def convertCapturesToCsv(pcapng_path, destination_file_path):
    # This routine transform de pcapng file into a csv format file which includes several features extracted from the packets captured.
    # For this to work, you need to start the npf service doing the follow:
    # 1) Open a cmd as adminitrator
    # 2) Type: net start npf


    cmd = "tshark -r " + pcapng_path + " -Y ssl.app_data -T fields -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport -e udp.srcport -e udp.dstport -e frame.len -E separator=, -E header=y >" + destination_file_path + "\\tmp_features.csv"
    os.system(cmd)


def find_prev(df, next_values_to_find, pos=0):
    # This routine finds a value or a set o values which are before an specific position (pos) whitin a dataframe. If you want to look from the beggining, don't provide the 'pos' parameter.
    # 'next_values_to_find' parameter is a list of values. If you're looking for one single value, provide it as a list anyway ( like -> [value]). Keep in mind the type of value you're looking for: 'strings', numbers (without quotation marks)
    # Te return value is a tuple which contains the packet length needed and its index in the dataframe. Also, provides 2 ip addresses to use later
    index = pos
    while (df.loc[index].comm_type not in next_values_to_find):
        index -= 1
    pkt_len = df.loc[index].packet_length
    ip_src = df.loc[index].ip_src
    ip_dst = df.loc[index].ip_dst
    return [ip_src, ip_dst, pkt_len, index]

#####################################################################################################################################

def build_db(pcapng_path, destination_file_path, iot_type):

    convertCapturesToCsv(pcapng_path, destination_file_path)
    csv_input = pd.read_csv(destination_file_path +"tmp_features.csv", error_bad_lines=False, warn_bad_lines=False)

    ### Merge port columns ###

    untouched_columns = ['ip.src', 'ip.dst', 'frame.len']
    df = pd.DataFrame()
    df = csv_input[untouched_columns].copy()

    df_tmp = pd.DataFrame(columns=['src_port', 'dst_port'])
    df_tmp['src_port'] = csv_input['tcp.srcport'].combine_first(csv_input['udp.srcport'])
    df_tmp['dst_port'] = csv_input['tcp.dstport'].combine_first(csv_input['udp.dstport'])

    df = pd.concat([df, df_tmp], axis=1)

    ### Replace NaNs ###
    df.replace(np.nan, '-1', regex=True, inplace=True)

    ### Create a new feature column ###
    df['comm_type'] = 'XX'

    ### Change columns names ###
    columns = {"ip.src": "ip_src", "ip.dst": "ip_dst", "frame.len": "packet_length"}
    df.rename(columns=columns, inplace=True)

    ### Labeling the packets ###

    # Smartphone <-> Smartplug
    iotDeviceType= iot_type

    if (iotDeviceType == '1'):  # iotDevice is Tplink smart camera
        phone_ip = ['192.168.200.143','192.168.200.144']
        # PhoneApp <-> Cloud
        # 01 -> domain 1

        # action1, action2 = find_actions_ips(df)
        domain1 = ['52.18.97.211', '52.211.107.78', '34.242.134.62', '52.31.84.22','54.195.243.98']  # appserver-0-1284302819.eu-west-1.elb.amazonaws.com
        domain2 = ['54.77140.227', '54.72.191.203', '107.23.65.87', '34.197.50.172']  # analytics.tplinkcloud:


        indexes01 = df.loc[((df['ip_src'].isin(phone_ip)) | (df['ip_dst'].isin(phone_ip))) & ((df['ip_src'].isin(domain1)) | (df['ip_dst'].isin(domain1)))].index.tolist()
        indexes10 = df.loc[((df['ip_src'].isin(phone_ip)) | (df['ip_dst'].isin(phone_ip))) & ((df['ip_src'].isin(domain2)) | (df['ip_dst'].isin(domain2)))].index.tolist()
        # 01 api = 2.2
        # 10 wap = 2.1
        df.loc[indexes01, 'comm_type'] = '1.1'
        df.loc[indexes10, 'comm_type'] = '1.2'
        # Complete dataset
        df.to_csv(destination_file_path + "TpCam-db.csv", index=False)

        # File 2 (phone ip, cloud ip, packet length)
        # Also added 'comm_type', but can drop that column out deleting its name from here (*)
        indexesCSV2 = df.loc[(df.comm_type == '1.1') | (df.comm_type == '1.2')].index.tolist()
        f2 = df.loc[indexesCSV2]
        f2.to_csv(destination_file_path + "PhoneToCloud.csv",
                  columns=['comm_type', 'ip_src', 'ip_dst', 'packet_length', 'src_port', 'dst_port'],
                  index=False)  # (*)

    if (iotDeviceType=='2'): # iotDevice is Tplink smart plug
         phone_ip = ['192.168.0.20', '192.168.0.16', '192.168.0.7', '192.168.0.27', '192.168.0.8', '192.168.0.19',
                    '192.168.200.143', '192.168.200.144', '192.168.0.5', '192.168.0.3']
    # PhoneApp <-> Cloud
    # 01 -> domain 1
    # 10 -> domain 2
    # 11 -> domain 3

    #action1, action2 = find_actions_ips(df)
         domain1 = ['54.175.20.158', '52.201.189.156', '52.204.39.38', '34.192.110.9', '54.88.137.188', '107.21.60.24','34.192.187.146','52.20.90.101']  # api.tplinkra.com:
         domain2 = ['52.18.97.211', '52.211.107.78', '34.242.134.62', '52.31.84.22', '52.214.120.178','46.51.135.221','52.31.15.72','54.31.15.72','54.77.42.106']  # appserver-0-1284302819.eu-west-1.elb.amazonaws.com

         indexes01 = df.loc[((df['ip_src'].isin(phone_ip)) | (df['ip_dst'].isin(phone_ip))) & ((df['ip_src'].isin(domain1)) | (df['ip_dst'].isin(domain1)))].index.tolist()
         indexes10 = df.loc[((df['ip_src'].isin(phone_ip)) | (df['ip_dst'].isin(phone_ip))) & ((df['ip_src'].isin(domain2)) | (df['ip_dst'].isin(domain2)))].index.tolist()
         #01 api = 2.2
         #10 wap = 2.1
         df.loc[indexes01, 'comm_type'] = '2.2'
         df.loc[indexes10, 'comm_type'] = '2.1'
         # Complete dataset
         df.to_csv(destination_file_path + "TpPlug-db.csv", index=False)

         # File 2 (phone ip, cloud ip, packet length)
         # Also added 'comm_type', but can drop that column out deleting its name from here (*)
         indexesCSV2 = df.loc[(df.comm_type == '2.1') | (df.comm_type == '2.2')].index.tolist()
         f2 = df.loc[indexesCSV2]
         f2.to_csv(destination_file_path + "PhoneToCloud.csv",
              columns=['comm_type', 'ip_src', 'ip_dst', 'packet_length', 'src_port', 'dst_port'], index=False)  # (*)

    if (iotDeviceType=='3'): # iotDevice is Belkin NetCam
         phone_ip = ['192.168.200.142', '192.168.200.143']
    # PhoneApp <-> Cloud
    # 01 -> domain 1
    # 10 -> domain 2
    # 11 -> domain 3

    #action1, action2 = find_actions_ips(df)
         domain1 = ['34.247.247.148', '54.154.140.63']  # NetCam-webserver-eu.belkin.com
         domain2 = ['35.175.97.238']  # NetCam.belkin/com
         domain3 = ['54.72.17.33', '54.72.251.99', '54.173.56.172'] # NetCam-event-eu.belkin.com

         indexes01 = df.loc[((df['ip_src'].isin(phone_ip)) | (df['ip_dst'].isin(phone_ip))) & ((df['ip_src'].isin(domain1)) | (df['ip_dst'].isin(domain1)))].index.tolist()
         indexes10 = df.loc[((df['ip_src'].isin(phone_ip)) | (df['ip_dst'].isin(phone_ip))) & ((df['ip_src'].isin(domain2)) | (df['ip_dst'].isin(domain2)))].index.tolist()
         indexes11 = df.loc[((df['ip_src'].isin(phone_ip)) | (df['ip_dst'].isin(phone_ip))) & ((df['ip_src'].isin(domain3)) | (df['ip_dst'].isin(domain3)))].index.tolist()

         df.loc[indexes01, 'comm_type'] = '3.1'
         df.loc[indexes10, 'comm_type'] = '3.2'
         df.loc[indexes11, 'comm_type'] = '3.3'
         # Complete dataset
         df.to_csv(destination_file_path + "BelkinNetCam-db.csv", index=False)

         # File 2 (phone ip, cloud ip, packet length)
         # Also added 'comm_type', but can drop that column out deleting its name from here (*)
         indexesCSV2 = df.loc[(df.comm_type == '3.1') | (df.comm_type == '3.2') | (df.comm_type == '3.3')].index.tolist()
         f2 = df.loc[indexesCSV2]
         f2.to_csv(destination_file_path + "PhoneToCloud.csv",
              columns=['comm_type', 'ip_src', 'ip_dst', 'packet_length', 'src_port', 'dst_port'], index=False)  # (*)

    if (iotDeviceType=='4'): # iotDevice is LIFX smart lamp
         phone_ip = ['192.168.0.2', '192.168.0.12']
    # PhoneApp <-> Cloud
    # 01 -> domain 1
    # 10 -> domain 2
    # 11 -> domain 3
    # 02 -> domain 4
    # 20 -> domain 5

    #action1, action2 = find_actions_ips(df)
         domain1 = ['34.196.35.65 ','52.207.60.209','107.23.35.254','34.235.94.173','52.202.82.209','34.192.17.169','34.224.0.167','107.21.8.180','52.21.83.194']  # 4.1Content.swrve.com
         domain2 = ['35.175.97.238','52.3.141.160','18.205.214.103','18.205.54.112','18.213.238.241','18.205.52.6','18.209.128.139','18.214.70.7','52.22.186.22',
                    '52.200.104.43','52.20.146.49','18.205.48.194','52.206.73.180','18.205.131.184','34.226.243.23','34.236.75.174','34.227.23.140','34.236.161.64',
                    '34.234.155.57']  # 4.2 Api.swrve.com
         domain3 = ['35.184.172.128'] # 4.3 cloud.lifx.com
         domain4 = ['52.21.79.95', '34.235.241.79']  # 4.4 Identity.swrve.com
         domain5 = ['54.230.3.151','54.230.3.153','54.230.3.236','54.230.3.192','54.230.3.25']  # 4.5 Hosted.lifx.com

         indexes01 = df.loc[((df['ip_src'].isin(phone_ip)) | (df['ip_dst'].isin(phone_ip))) & ((df['ip_src'].isin(domain1)) | (df['ip_dst'].isin(domain1)))].index.tolist()
         indexes10 = df.loc[((df['ip_src'].isin(phone_ip)) | (df['ip_dst'].isin(phone_ip))) & ((df['ip_src'].isin(domain2)) | (df['ip_dst'].isin(domain2)))].index.tolist()
         indexes11 = df.loc[((df['ip_src'].isin(phone_ip)) | (df['ip_dst'].isin(phone_ip))) & ((df['ip_src'].isin(domain3)) | (df['ip_dst'].isin(domain3)))].index.tolist()
         indexes02 = df.loc[((df['ip_src'].isin(phone_ip)) | (df['ip_dst'].isin(phone_ip))) & ((df['ip_src'].isin(domain4)) | (df['ip_dst'].isin(domain4)))].index.tolist()
         indexes20 = df.loc[((df['ip_src'].isin(phone_ip)) | (df['ip_dst'].isin(phone_ip))) & ((df['ip_src'].isin(domain5)) | (df['ip_dst'].isin(domain5)))].index.tolist()


         df.loc[indexes01, 'comm_type'] = '4.1'
         df.loc[indexes10, 'comm_type'] = '4.2'
         df.loc[indexes11, 'comm_type'] = '4.3'
         df.loc[indexes02, 'comm_type'] = '4.4'
         df.loc[indexes20, 'comm_type'] = '4.5'

         # Complete dataset
         df.to_csv(destination_file_path + "LIFX-db.csv", index=False)

         # File 2 (phone ip, cloud ip, packet length)
         # Also added 'comm_type', but can drop that column out deleting its name from here (*)
         indexesCSV2 = df.loc[(df.comm_type == '4.1') | (df.comm_type == '4.2') | (df.comm_type == '4.3') | (df.comm_type == '4.4') | (df.comm_type == '4.5')].index.tolist()
         f2 = df.loc[indexesCSV2]
         f2.to_csv(destination_file_path + "PhoneToCloud.csv",
              columns=['comm_type', 'ip_src', 'ip_dst', 'packet_length', 'src_port', 'dst_port'], index=False)  # (*)

################################################################################################################################################

def main(pcapng_path, destination_file_path,iot_type):
    build_db(pcapng_path, destination_file_path,iot_type)


########################################################################
#convert the file to conversation.csv

def conversation (csv_destination, path2):
    df = pd.read_csv(csv_destination, error_bad_lines=False, warn_bad_lines=False)

    result = (df.groupby((df != df.shift()).cumsum().to_records(index=False))
              .agg({'ip_src': 'last',
                    'ip_dst': 'last',
                    'packet_length': ['count', 'max'],
                    'src_port': 'last',
                    'dst_port': 'last',
                    'comm_type': 'last'
                    })
              .reset_index(drop=True))


    result.columns = ['ip_src','src_port','ip_dst','dst_port','count','packet_length','comm_type']


    # where pkt is a dataframe's row  ## pkt data ##2
    def find_response(df, pkt, pos=0):
        comm_type = pkt.comm_type
        ip_src = pkt.ip_src
        ip_dst = pkt.ip_dst
        src_port = pkt.src_port
        dst_port = pkt.dst_port
        count = pkt['count']
        pkt_len = pkt.packet_length


        tmp_list = []


        sliced_df = df[pos:]
        for index, row in sliced_df.iterrows():
            # response (inverted ip addresses and ports)
            r_ip_src = ip_dst
            r_ip_dst = ip_src
            r_src_port = dst_port
            r_dst_port = src_port
            if ((row.ip_src == r_ip_src) & (row.ip_dst == r_ip_dst) & (row.src_port == r_src_port) & (
                    row.dst_port == r_dst_port)):
                tmp_list = [comm_type, ip_src, src_port, ip_dst, dst_port, int(count), int(pkt_len), int(row['count']),
                            int(row.packet_length)]
                return tmp_list

        return tmp_list

    new_df = pd.DataFrame()
    results = []
    for index, row in result.iterrows():
        fila_nueva = find_response(result, row)

        if (fila_nueva == []):
            pass

        else:

            results.append(fila_nueva)
            # to remove the repetition of the send and recieve packets
            temp = fila_nueva[6]  # save the length of the send packets in var= temp
            length = len(results)  # bcz the len of the results is != to the index
            if (length == 1):  # this mean we only have one record so there wont be any repetition so far
                pass
            else:
                temp_2 = results[length - 2][8]  # save the length of the recieve packet from the results in temp-2.
                # e.g. if the length of the results = 3, but the index of the results is {0,1,2}, then
                # temp= results[2][6] is => 612
                # temp_2 = results[1][8] => 612
                if ((temp == temp_2) or (temp == 100)):
                    results.remove(results[length - 1])

    new_df = pd.DataFrame(columns=['comm_type','ip_src', 'src_port', 'ip_dst', 'dst_por', 'Packets sent A->B', 'Bytes sent A->B', 'Packets sent B->A', 'Bytes sent B->A'], data=results)
    new_df.to_csv(path2+'PhoneToCloud_conversations.csv', index=False)


#*******************************************************************************************************************************************************************#
def PII_Analysis(PII_db, PIItype_db, prediction): ## this function has 3 different ML to pridect the user PII packets
    ## read the .csv files
    df_PII = pd.read_csv(PII_db)
    df_PIItype = pd.read_csv(PIItype_db)
    df_predict = pd.read_csv (prediction)
    ## drop the un wanted columns from the un-seen file
    predict_data = np.array(df_predict.drop(['ip_src', 'src_port', 'ip_dst', 'dst_por', 'Packets sent A->B', 'Packets sent B->A'], 1))


## train the first machine learning to predict the PII if it is (sensitive, non-sensitive, non) ##

    X_1 = np.array(df_PII.drop(['PII'], 1))
    y_1 = np.array(df_PII['PII'])
    X_train_1, X_test_1, y_train_1, y_test_1 = train_test_split(X_1, y_1, test_size=0.2, random_state=42)

    PII_model =  RandomForestClassifier(n_estimators=10, min_samples_leaf = 3,bootstrap = False, min_samples_split= 8, criterion= 'entropy', max_features= 'auto', max_depth= 90)
    PII_model.fit(X_train_1, y_train_1)
    PII_accuracy = PII_model.predict(X_test_1)

    ## apply the ML and predict the un-seen data ##
    PII_predict = PII_model.predict(predict_data)
    y_pred_1 = PII_accuracy

    outF = open("PII_result.txt", "w")

    for line in PII_predict:
        # write line to output file
        outF.write(line)
        outF.write("\n")
    outF.close()

    # open and read the file that contain the results from the first Machine Learning
    ## create new list to hold the PII
    PII = []

    inf = open('PII_result.txt', 'r')
    # put the file content in a list inside variable x
    line = inf.readlines()
    for x in line:
        l = x.strip()
        PII.append(l)
    inf.close()
## calculate the persentage of the occurrence of the sensitive packets ##

    sen_PII = PII.count('sensitive')
    Non_Sen_PII = PII.count('non-sensitive')
    Non_PII = PII.count('Non')


## train the second machine learning to predict the PII type if it is (credential, location, userName) ##

    X_2 = np.array(df_PIItype.drop(['PII'], 1))
    y_2 = np.array(df_PIItype['PII'])
    X_train_2, X_test_2, y_train_2, y_test_2 = train_test_split(X_2, y_2, test_size=0.2, random_state=42)

    PIItype_model = RandomForestClassifier(n_estimators=10, min_samples_leaf = 3,bootstrap = False, min_samples_split= 8, criterion= 'entropy', max_features= 'auto', max_depth= 90)
    PIItype_model.fit(X_train_2, y_train_2)
    PIItype_accuracy = PIItype_model.predict(X_test_2)
    PIItype_prediction = PIItype_model.predict(predict_data)
    y_pred_2= PIItype_accuracy
    ## create file to save the result of the predicted file temporary ##

    outF = open("PIItype_result.txt", "w")

    for line in PIItype_prediction:
        # write line to output file
        outF.write(line)
        outF.write("\n")
    outF.close()

    # open and read the file that contain the results from the second Machine Learning
    ## create new list to hold the PII type
    PIItype = []

    inf = open('PIItype_result.txt', 'r')
    # put the file content in a list inside variable x
    line = inf.readlines()
    for x in line:
        l = x.strip()
        PIItype.append(l)
    inf.close()
## create new list to put the type of sensitive data ##
    sensitive_type = []
    if any('location' in PIItype for i in PIItype):
        sensitive_type.append('user location')
    if any('credential' in PIItype for i in PIItype):
        sensitive_type.append('user credential')
## create new list to put the non-sensitive ##
    non_sensitive_type = []
    if any('userName' in PIItype for i in PIItype):
        non_sensitive_type.append('user name or email')

    return sensitive_type, non_sensitive_type
#***********************************************************************************************************#

def user_Interaction_Analysis (Interaction_db,prediction):

    df_Interaction = pd.read_csv (Interaction_db)
    df_predict = pd.read_csv(prediction)
    ## drop the un wanted columns from the un-seen file
    predict_data = np.array(df_predict.drop(['ip_src', 'src_port', 'ip_dst', 'dst_por', 'Packets sent A->B', 'Packets sent B->A'], 1))
## train the third machine learning to predict user interaction with the IoT app

    X_3 = np.array(df_Interaction.drop(['Action'], 1))
    y_3 = np.array(df_Interaction['Action'])
    X_train_3, X_test_3, y_train_3, y_test_3 = train_test_split(X_3, y_3, test_size=0.2, random_state=42)

    userAction_model = RandomForestClassifier(n_estimators=10, min_samples_leaf = 3,bootstrap = False, min_samples_split= 8, criterion= 'entropy', max_features= 'auto', max_depth= 90)
    userAction_model.fit(X_train_3, y_train_3)
    Interaction_accuracy = userAction_model.predict(X_test_3)

    # test the un-seen data
    Interaction_prediction = userAction_model.predict(predict_data )

    y_pred_3= Interaction_accuracy


## create new file to save the result of the un-seen data
    outF = open("userAction_result.txt", "w")

    for line in Interaction_prediction:
        # write line to output file
        outF.write(line)
        outF.write("\n")
    outF.close()

    userInteraction = []
## read from the file and save the data in the userInteraction list
    inf = open('userAction_result.txt', 'r')
    # put the file content in a list inside variable x
    line = inf.readlines()
    for x in line:
        l = x.strip()
        userInteraction.append(l)
    inf.close()

    userAction_type = []
    if any('Logout' in userInteraction for i in userInteraction):
        userAction_type.append('user Logout from the IoT-app')
    if any('Login' in userInteraction for i in userInteraction):
        userAction_type.append('user Login to the IoT-app')
    if any('ModifyPassword' in userInteraction for i in userInteraction):
        userAction_type.append('user change his IoT-app password')
    if any('Delete' in userInteraction for i in userInteraction):
        userAction_type.append('user delete the IoT device from the IoT-app')

    print('\n\nThe user interaction type with the IoT-app is/are : ', userAction_type)

######################################################################################################################


#this function will redirect the requests to its proper ML functions in order to predict the percentage of the packet that being sent from the IoT-app to the cloud
def IoT_packet_analysis(prediction, iot_type):


    if (iot_type == '1'):

        PII_db = '~/Downloads/IoT-Devices/IoT-PII.csv'
        PIItype_db = '~/Downloads/IoT-Devices/IoT-user-PIItype.csv'
        Interaction_db = '~/Downloads/IoT-Devices/IoT-InteractionType.csv'

        sensitive_words, non_sensitive_words = PII_Analysis(PII_db, PIItype_db, prediction)
        user_Interaction_Analysis(Interaction_db, prediction)


    if (iot_type == '2'):
        ## the path of the database ##
        PII_db = '~/Downloads/IoT-Devices/IoT-PII.csv'
        PIItype_db = '~/Downloads/IoT-Devices/IoT-user-PIItype.csv'
        Interaction_db = '~/Downloads/IoT-Devices/IoT-InteractionType.csv'

        sensitive_words, non_sensitive_words = PII_Analysis(PII_db, PIItype_db, prediction)
        user_Interaction_Analysis(Interaction_db,prediction)

    if (iot_type =='3'):
         ## the path of the databases ##
         PII_db = '~/Downloads/IoT-Devices/IoT-PII.csv'
         PIItype_db = '~/Downloads/IoT-Devices/IoT-user-PIItype.csv'
         Interaction_db = '~/Downloads/IoT-Devices/IoT-InteractionType.csv'

         sensitive_words, non_sensitive_words = PII_Analysis(PII_db, PIItype_db, prediction)
         user_Interaction_Analysis(Interaction_db, prediction)

    if (iot_type == '4'):

             ## the path of the databases ##
        PII_db = '~/Downloads/IoT-Devices/IoT-PII.csv'
        PIItype_db = '~/Downloads/IoT-Devices/IoT-user-PIItype.csv'
        Interaction_db = '~/Downloads/IoT-Devices/IoT-InteractionType.csv'

        sensitive_words, non_sensitive_words =PII_Analysis(PII_db, PIItype_db, prediction)
        user_Interaction_Analysis(Interaction_db, prediction)

    return sensitive_words, non_sensitive_words



def Print_compliance_Table(sensitive_PII, non_sensitive_PII,sensitive_IoT_PPA, non_sensitive_IoT_PPA ):
    print("The evaluation results are:\n")
    headers = ["IoT-app Inspector", "IoT Privacy Plicy Agreement", "Compliance decision"]
    rows = ["Collect Location", "Collect Login", "Collect Password", "Collect Username", "Collect Email", "Collect Device Information"]
    data = []
    # we assume that always the traffic collect the device information
    temp_inspector = [0, 0, 0, 0, 0, 1]
    temp_PPA = [0, 0, 0, 0, 0, 0]

# we assume that the packet hold the login and passwprd in the same packet
    for x in sensitive_PII:
        if "location" in x:
            temp_inspector[0]= 1
        elif "credential" in x:
            temp_inspector[1] = 1 # login
            temp_inspector[2] = 1 # password
        else:
            pass
    # we assume that the traffic collect the user name or password in the same packet
    for x in non_sensitive_PII:
        if "name"in x:
            temp_inspector[3] = 1 # username
            temp_inspector[4] = 1 # email

# loop through thr IoT PPA
    for x in sensitive_IoT_PPA:
        if "location" in x:
            temp_PPA[0] = 1
        elif "login" in x:
            temp_PPA[1] = 1
        elif "password" in x:
            temp_PPA[2] = 1
        else:
            pass
    for x in non_sensitive_IoT_PPA:
        if "name" in x:
            temp_PPA[3] = 1
        elif "email" in x:
            temp_PPA[4] = 1
        elif "device" in x:
            temp_PPA[5] = 1
        else:
            pass

    for index in range(len(temp_inspector)):
        if temp_inspector[index] == temp_PPA[index]:
            data.append([1,1,"Yes"])
        if temp_inspector[index] > temp_PPA[index]:
            data.append([1,0, "No"])
        if temp_inspector[index] < temp_PPA[index]:
            data.append([0,1, "No"])

    row_format = '{:>35}' * (len(headers)+1)
    print (row_format.format("", *headers))
    for row, i in zip(rows, data):
        print (row_format.format(row, *i))


###################### Main program #########################################

if __name__ == '__main__':

    print("Welcome to the IoT compliance evaluation tool.\n"
          "This tool aims to evaluate the level of the compliance of the actual behavior of your IoT device with its privacy policy agreement.\n"
          "First, the tool infers the data type that transferred from the IoT device to the IoT cloud. Then, it reads the privacy policy agreement of such IoT device.\n"
          "Finaly, it compares the results to check wheather the actual behavior of the IoT device match with what stated in its privacy policy.\n"
          "To proceed please type (Y/y), otherwise press (N/n) to exit.")
    answer= raw_input("your answer is: ")

    if ((answer== 'Y')or (answer =='y')):

        print("\nPlease select the IoT device that you want to evaluate its compliance:\n"
            "1- Tp-link SmartCam.\n"
            "2- Tp-link Smart Plug.\n"
            "3- Belkin NetCam.\n"
            "4- LIFX smart lamp.\n")

        iot_type = raw_input("your answer is: ")

        print ("\nPlease, provide the full path where your IoT file (.pcapng) locate (folder_name1\\..\\folder_nameN\\name.pcapng): ")
        path1 = raw_input(".pcapng file: ")
        print ("Please, provide the full path where your want to store your database and the final results: (folder_name1\\..\\folder_nameN): ")
        path2 = raw_input("dataset destintation: ")
# call the function to built the data base files
        main(path1, path2, iot_type)
        path_new = path2 + 'PhoneToCloud.csv'
    # run the coversation function to prepare the phonecloud file to be in a conversation file, to be ready for the prediction
    # save the conversation path in the prediction_path variable
        conversation(path_new,path2)
        predict_path = path2 + 'PhoneToCloud_conversations.csv'
    # the path of the database in order to predict its PII sensitivety

        print ("Your dataset was created and ready for the evaluation....." )
        sensitive_PII, non_sensitive_PII = IoT_packet_analysis(predict_path, iot_type)

        if ((iot_type == '1') or(iot_type=='2')):
            sensitive_IoT_PPA, non_sensitive_IoT_PPA = Extract_IoTPPA.IoT_PPA_compliance('1') #Extract_IoT_PPA.IoT_PPA_compliance('1')
            Print_compliance_Table(sensitive_PII, non_sensitive_PII, sensitive_IoT_PPA, non_sensitive_IoT_PPA)
        elif (iot_type =='3'):
            sensitive_IoT_PPA, non_sensitive_IoT_PPA = Extract_IoTPPA.IoT_PPA_compliance('2')#Extract_IoT_PPA.IoT_PPA_compliance('2')
            Print_compliance_Table(sensitive_PII, non_sensitive_PII, sensitive_IoT_PPA, non_sensitive_IoT_PPA)
        elif (iot_type == '4'):
            sensitive_IoT_PPA, non_sensitive_IoT_PPA = Extract_IoTPPA.IoT_PPA_compliance('3')#Extract_IoT_PPA.IoT_PPA_compliance('3')
            Print_compliance_Table(sensitive_PII, non_sensitive_PII, sensitive_IoT_PPA, non_sensitive_IoT_PPA)

    else:
        print ('Thank you!!!')

