from flask import Flask, jsonify, request
import requests
import datetime
import pprint
from pymongo import MongoClient
#MOMGO USER -- abigailmarlett
#MONGO PASS -- fitbit


app = Flask(__name__)
token = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIyMzhSNkIiLCJzdWIiOiJCNEYzNVEiLCJpc3MiOiJGaXRiaXQiLCJ0eXAiOiJhY2Nlc3NfdG9rZW4iLCJzY29wZXMiOiJyc29jIHJzZXQgcm94eSBybnV0IHJwcm8gcnNsZSByYWN0IHJsb2MgcnJlcyByd2VpIHJociBydGVtIiwiZXhwIjoxNjkyMjk1NDQ0LCJpYXQiOjE2NjA3NTk0NDR9.bILcGIrPRXPWRrWBZDKRLsZdtTKKqPUpZ4NZZ-U3k5g"
acturl = "https://api.fitbit.com/1/user/-/activities/date/today.json"
profile = "https://api.fitbit.com/1/user/-/profile.json"
heartrate = "https://api.fitbit.com/1/user/-/activities/heart/date/today/1d/1min.json"
sleep = "https://api.fitbit.com/1.2/user/-/sleep/date/today.json"
activity = "https://api.fitbit.com/1/user/-/activities/date/today.json"
client = MongoClient("mongodb+srv://abigailmarlett:fitbit@cluster0.umkulcv.mongodb.net/?retryWrites=true&w=majority")
db = client["mydb"]
# rows = db.env.find({})

# for x in rows:
#    print(x)

header = {'Accept' : 'application/json', 'Authorization' : 'Bearer {}'.format(token)}
name = requests.get(profile,headers=header).json()
resp = requests.get(acturl, headers=header).json()
hr = requests.get(heartrate, headers=header).json()
sleep_log = requests.get(sleep, headers=header).json()
activity_log = requests.get(activity, headers=header).json()
#print(hr)


@app.route("/myjoke", methods=["GET"])
def mymethod():
    joke = "Why did everyone cross the road? Ha! ha, ha!"
    ret = {'category' : 'very funny', 'value' : joke}
    return jsonify(ret)

@app.route("/name", methods=["GET"])
def nameMethod():
    if "errors" in name.keys():
        return (resp["errors"])
    else:
        user = name["user"]
        return jsonify(user["fullName"])
        
@app.route("/heartrate/last", methods=["GET"])
def heartRate():
    intraday = hr["activities-heart-intraday"]
    #print(intraday)
    #pprint.pprint(intraday)
    dataSet = intraday["dataset"]
    num = len(dataSet)
    mostRecent = dataSet[num - 1] 

    time_from_api = mostRecent["time"]
    date_from_api = hr["activities-heart"][0]["dateTime"]
    api_full_date_string = date_from_api+" "+time_from_api
    api_dt_obj = datetime.datetime.strptime(api_full_date_string, '%Y-%m-%d %H:%M:%S')

    # current time
    time_now = datetime.datetime.now()
    time_diff_base = time_now - api_dt_obj
    time_diff_minutes = time_diff_base.total_seconds() / 60
    hours = 0
    while time_diff_minutes > 60:
        hours += 1
        time_diff_minutes -= 60

    time_diff_minutes_rounded = round(time_diff_minutes, 2)
    rate = mostRecent["value"]
    ret = {"heart rate" : rate, "time offset" :  str(hours-4) + " hours, and " + str(time_diff_minutes_rounded) + " minutes!"}
    return jsonify(ret)

@app.route("/steps/last", methods=["GET"])
def steps():
    offsetLink = "https://api.fitbit.com/1/user/-/activities/steps/date/today/1d/1min.json"
    offsetF = requests.get(offsetLink,headers=header).json()
    dataSetList = offsetF["activities-steps-intraday"]
    dataSet = dataSetList["dataset"]
    num = len(dataSet)
    mostRecent = dataSet[num - 1] 

    time_from_api = mostRecent["time"]
    date_from_api = offsetF["activities-steps"][0]["dateTime"]
    api_full_date_string = date_from_api+" "+time_from_api
    api_dt_obj = datetime.datetime.strptime(api_full_date_string, '%Y-%m-%d %H:%M:%S')

    # current time
    time_now = datetime.datetime.now()
    time_diff_base = time_now - api_dt_obj
    time_diff_minutes = time_diff_base.total_seconds() / 60
    hours = 0
    while time_diff_minutes > 60:
        hours += 1
        time_diff_minutes -= 60
    time_diff_minutes = round(time_diff_minutes, 2)
    hours -= 4
    summ = resp["summary"]
    numberSteps = summ["steps"]
    distanceTable = summ["distances"][0]
    ret = {"step-count" : numberSteps, "distance" : distanceTable["distance"], "offset" : str(hours) + " hours and " + str(time_diff_minutes) + " minutes."}
    return ret

@app.route("/sleep/<date>", methods=["GET"])
def sleep(date):
    sleepLink = "https://api.fitbit.com/1.2/user/-/sleep/date/" + date + ".json"
    log = requests.get(sleepLink, headers=header).json()
    
    if "summary" in log:
        try:
            deep = log["summary"]["stages"]["deep"]
            light = log["summary"]["stages"]["light"]
            rem = log["summary"]["stages"]["rem"]
            wake = log["summary"]["stages"]["wake"]
            return jsonify({"deep": deep, "light": light, "rem": rem, "wake": wake})
        except:
            return "No data available for this day."
    else:
        return "No data available for this day."
        

@app.route("/activity/<date>", methods=["GET"])
def activity(date):
    activityLogByDate = "https://api.fitbit.com/1/user/-/activities/date/"+ date + ".json"
    activityHeader = requests.get(activityLogByDate, headers=header).json()
    summ = activity_log["summary"]
    sedentaryMin = summ["sedentaryMinutes"]
    lightlyActive = summ["lightlyActiveMinutes"] 
    highlyActive = summ["veryActiveMinutes"] 
    ret = {"very-active" : highlyActive, "lightly-active" : lightlyActive, "sedentary" : sedentaryMin}
    return jsonify(ret)

@app.route("/sensors/env", methods=["GET"])
def tempHumid():
    mydoc = db.env.find().sort("timestamp", -1)
    items = mydoc[0]
    temp = items["temp"]
    hum = items["humidity"]
    time = items["timestamp"]
    ret = {"temp": temp, "humidity" : hum, "timestamp": time}
    return jsonify(ret)
    


@app.route("/sensors/pose", methods=["GET"])
def pose():
    # Returns the last logged gesture/pose/presence information*
    # e.g., {‘presence’: ‘yes’, ‘pose’: ‘sitting’, ‘timestamp’: 1594823426.159446}
    mydoc = db.pose.find().sort("timestamp", -1)
    items = mydoc[0]
    presence = items["presence"]
    pose = items["pose"]
    time = items["timestamp"]
    ret = {"presence": presence, "pose" : pose, "timestamp": time}
    return jsonify(ret)


@app.route("/post/env", methods=["POST"])
def pTempHumid():
    # data = request.get_json()
            # gets data from postman
    data = request.get_json()
    #print(data)
    temp = data["temp"]
    hum = data["humidity"]
    time = datetime.timestamp(datetime.now())
    to_insert = {"temp": temp, "humidity": hum, "timestamp" : time}
    id = db.env.insert_one(to_insert)

            # download postman onto mac 
            #sign in, specify POST as method, copy and paste link from local browser, in "body" click raw put in a json, click send, 
            #import datetime for timestamp 
    return str(to_insert)
   

@app.route("/post/pose", methods=["POST"])
def pPose():
    data = request.get_json()
    #print(data)
    presence = data["presence"]
    pose = data["pose"]
    time = datetime.timestamp(datetime.now())
    to_insert = {"presence": presence, "pose": pose, "timestamp" : time}
    id = db.pose.insert_one(to_insert)
    return str(to_insert)




if __name__ == '__main__':
    app.run(debug=True)

