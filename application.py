# -*- coding: utf-8 -*-
import flask
from flask import *
from flask import Flask
from flask import request
from flask import jsonify
import sys
import json


from urllib import parse
import urllib.request
import requests, json
import pandas as pd

from datetime import date
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from pytz import timezone, utc

from flask_restful import Resource, Api, reqparse
from flask_jwt import JWT, jwt_required, current_identity

import pymysql
hoststr = "localhost"
usrstr = "root"
passwordstr = "co2bot2020!"
dbstr = "CoffeePark"

from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    jwt_refresh_token_required, create_refresh_token,
    get_jwt_identity, set_access_cookies,
    set_refresh_cookies, unset_jwt_cookies
)

import numpy as np
from fbprophet import Prophet
import pickle

from apscheduler.schedulers.background import BackgroundScheduler

application = Flask("coffeepark")



application.config['JWT_TOKEN_LOCATION'] = ['cookies']

application.config['JWT_ACCESS_COOKIE_PATH'] = '/'
application.config['JWT_REFRESH_COOKIE_PATH'] = '/'

application.config['JWT_COOKIE_CSRF_PROTECT'] = False

application.config['JWT_SECRET_KEY'] = 'coffeepark' 

application.config['SESSION_COOKIE_HTTPONLY'] = False
application.config['CSFR_COOKIE_HTTPONLY'] = False

application.config['JWT_COOKIE_SECURE'] = False
application.config['PERMANENT_SESSION_LIFETIME'] = 2678400

api = Api(application)

jwt = JWTManager(application)

@application.route('/coffeepark_monitor')
def coffeepark_monitor():
	return render_template('coffeepark_monitor.html')

@application.route('/')
def main():
    return render_template('coffeepark_login.html')

@application.route("/api/monitor/blockchain")
def getMonitorblockchain():
    conn = pymysql.connect(host=hoststr, user=usrstr, password=passwordstr, db=dbstr, charset='utf8')
    df = ""
    try:
        # 블록체인 날짜 예측
        sql = " select DATE_FORMAT(CONVERT_TZ(Insert_Dt, '+0:00', '+9:00'),'%Y-%m-%d %H:%i') as DateTime, TranQty  from BLOCKCHAIN_LOG  order by Insert_Dt desc limit 0,6 "        
        df = pd.read_sql_query(sql,conn)
        print(df)
        return df.to_json(orient='records')
    
    finally:
        conn.close()
        
@application.route("/api/monitor/prediction")
def getMonitorPredict():
    fcast =[]
    
    fcast = pd.read_pickle("coffeepark_provide_ver1.pkl")  
    fcast_demand = pd.read_pickle("coffeepark_demand_ver1.pkl")
        
    fcast["trend2_demand"] = fcast_demand["trend"]
    #오늘 날짜 기준 7개 가져옴 (한국 시간대로 해야함)
    KST = timezone('Asia/Seoul')
    now = datetime.utcnow()
    today_dt = utc.localize(now).astimezone(KST) 
    today_string = today_dt.strftime("%Y-%m-%d")
    print(today_string)
    end_date = today_dt + timedelta(days=8)
    end_date_string = end_date.strftime("%Y-%m-%d")
    print(end_date.strftime("%Y-%m-%d"))
    fcast = fcast.loc[(fcast['ds'] >= today_string) & (fcast['ds'] <= end_date_string)]
    fcast = fcast.drop_duplicates(['ds'], keep='last')
    fcast = fcast[['ds', 'trend', 'trend2_demand']] # 날짜 / 공급 / 수요
    return fcast.to_json(orient='records')

#공급 / 수요 데이터 불러와서 피클 만들기
@application.route("/api/monitor/ai-creation")
def getAICreate():
    
    conn = pymysql.connect(host=hoststr, user=usrstr, password=passwordstr, db=dbstr, charset='utf8')
    df = ""
    try:
        # 공급 예측
        sql = " select DATE_FORMAT(Insert_Dt,'%Y-%m-%d') as ds, CAST(Sum(COFFEEPARK_LOG.QtyKg) as unsigned int) as y from COFFEEPARK_LOG "        
        sql +=" where UserType='Provide' and DATE_FORMAT(Insert_Dt,'%Y-%m') = DATE_FORMAT(sysdate(),'%Y-%m') "                
        sql +=" group by DATE_FORMAT(Insert_Dt,'%Y-%m-%d') "

        df = pd.read_sql_query(sql,conn)
        
        m = Prophet()
        m.add_seasonality(name='weekly',  period=7, fourier_order = 10, prior_scale=0.1);
        m.fit(df)

        future = m.make_future_dataframe(periods=365, freq='H')
        forcast = m.predict(future)
                
        print(forcast)
        
        forcast['ds'] =  forcast['ds'].dt.strftime('%Y-%m-%d') 
        forcast['trend'] = forcast['trend'].apply(np.int64)

        print(forcast)
        print("ds change3")
        
        forcast.to_pickle("coffeepark_provide_ver1.pkl")
        
        # 수요 예측
        sql = " select DATE_FORMAT(Insert_Dt,'%Y-%m-%d') as ds, CAST(Sum(COFFEEPARK_LOG.QtyKg) as unsigned int) as y from COFFEEPARK_LOG "        
        sql +=" where UserType='Demand' and DATE_FORMAT(Insert_Dt,'%Y-%m') = DATE_FORMAT(sysdate(),'%Y-%m') "                
        sql +=" group by DATE_FORMAT(Insert_Dt,'%Y-%m-%d') "

        df = pd.read_sql_query(sql,conn)
        
        m = Prophet()
        m.add_seasonality(name='weekly',  period=7, fourier_order = 10, prior_scale=0.1);
        m.fit(df)

        future = m.make_future_dataframe(periods=365, freq='H')
        forcast = m.predict(future)
        
        forcast['ds'] =  forcast['ds'].dt.strftime('%Y-%m-%d') 
        forcast['trend'] = forcast['trend'].apply(np.int64)
        print(forcast)
        forcast.to_pickle("coffeepark_demand_ver1.pkl")

    finally:
        conn.close()
    
    return "Save the Pickle", 200

@jwt.user_claims_loader
def add_claims_to_access_token(identity):
    conn = pymysql.connect(host=hoststr, user=usrstr, password=passwordstr, db=dbstr, charset='utf8')
    username = ""
    usertype = ""
    
    try:
        cursor = conn.cursor()
        sql = " select UserName, UserType from USER_INFO  "
        sql +=" where UserID = '"+identity+"'  "
        cursor.execute(sql)
        result = cursor.fetchall()
        print(result)
        returnValue = 0
        for data in result:
            username = data[0]
            usertype = data[1]
            print(username)
            print(usertype)
            
    finally:
        conn.close()   
            
    return {
        'username': username,
        'usertype': usertype
        }

@application.route('/api/user', methods=['POST', 'GET'])
def login():
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    
    conn = pymysql.connect(host=hoststr, user=usrstr, password=passwordstr, db=dbstr, charset='utf8')
    try:
        cursor = conn.cursor()
        sql = " select UserName from USER_INFO  "
        sql +=" where UserID = '"+email+"'  "
        cursor.execute(sql)
        result = cursor.fetchall()
        print(result)
        returnValue = 0
        for data in result:
            print(data[0])
            returnValue = data[0]
            
        if returnValue == 0:
            return jsonify({'login': False}), 401
    finally:
        conn.close()    
    
    access_token = create_access_token(identity=email)
    refresh_token = create_refresh_token(identity=email)

    resp = jsonify({'login': True})
    #application.config['SESSION_COOKIE_HTTPONLY'] = False
    set_access_cookies(resp, access_token) 
    #resp.set_cookie('HttpOnly','False')
    set_refresh_cookies(resp, refresh_token)
    #resp.set_cookie('HttpOnly','False')
    print(resp.headers)
    print(resp.json)
    print(access_token)
    return resp, 200

def getUserType(Userid) :
    conn = pymysql.connect(host=hoststr, user=usrstr, password=passwordstr, db=dbstr, charset='utf8')
    try:
        cursor = conn.cursor()
        sql = " select UserType from USER_INFO  "
        sql +=" where UserID = '"+Userid+"'  "
        cursor.execute(sql)
        result = cursor.fetchall()
        print(result)
        returnValue = 0
        for data in result:
            print(data[0])
            returnValue = data[0]

    finally:
        conn.close()  
        
    return returnValue
    
@application.route("/api/coffee", methods=['POST', 'GET'])
@jwt_required
def insertCoffeePark():
    Userid = get_jwt_identity()
    print(Userid)
    amount = request.json.get('amount', None)
    print(amount)
    UserType = getUserType(Userid)
    QtyKg = amount
    Status = "waiting"
    returnValue = "fail"
    
    print(Userid)
    print(UserType)
    print(QtyKg)
    
    conn = pymysql.connect(host=hoststr, user=usrstr, password=passwordstr, db=dbstr, charset='utf8')
    
    try:
        cursor = conn.cursor()
        sql = " insert into COFFEEPARK_LOG (UserID, UserType, QtyKg, Status, Insert_Dt) "
        sql +=" Values('"+Userid+"','"+UserType+"','"+str(QtyKg)+"','"+Status+"',sysdate()) "        
        cursor.execute(sql)
        conn.commit()
        returnValue = "success"
    finally:
        conn.close()
    
    #블록체인 insert
    data = {'cafeId':Userid,'amount':QtyKg}
    url = "http://101.101.209.10:3000/coffee-ground"
    res = requests.post(url, data = data)
    if res.status_code == 200 :
        returnValue = "success"
        print(res.json())
    else :
        returnValue = "faile"
        
    return { "status" : returnValue, "content" : { "status" : "waiting" }}	

@application.route("/api/<userid>/coffee" , methods=['GET'])
@jwt_required
def getCoffeeParkHistory(userid):
    
    conn = pymysql.connect(host=hoststr, user=usrstr, password=passwordstr, db=dbstr, charset='utf8')
    df = ""
    try:
        sql = " select insert_dt as timestamp , status as status, QtyKg as amount from COFFEEPARK_LOG  "
        sql +=" where UserID = '"+userid+"' order by Insert_Dt desc  "
        df = pd.read_sql_query(sql,conn)
        print(df)
    finally:
        conn.close()
        
    return df.to_json(orient='records')


@application.route("/api/<userid>/amount" , methods=['GET'])
@jwt_required
def getCoffeeParkMonthly(userid):
    
    conn = pymysql.connect(host=hoststr, user=usrstr, password=passwordstr, db=dbstr, charset='utf8')
    returnValue = 0
    try:
        cursor = conn.cursor()
        sql = " select Sum(QtyKg) from COFFEEPARK_LOG  "
        sql +=" where UserID = '"+userid+"' and DATE_FORMAT(Insert_Dt,'%Y-%m') = DATE_FORMAT(sysdate(),'%Y-%m') "
        cursor.execute(sql)
        result = cursor.fetchall()
        print(result)
        
        for data in result:
            print(data[0])
            returnValue = data[0]
    finally:
        conn.close()
        
    return { "amount" : returnValue }


@application.route("/api/<userid>/badge" , methods=['GET'])
@jwt_required
def getBadgeHistory(userid):
    print(userid)
    
    conn = pymysql.connect(host=hoststr, user=usrstr, password=passwordstr, db=dbstr, charset='utf8')
    df = ""
    try:
        sql = " select BADGE_INFO.Image_src as image_src, BADGE_INFO.Name as name, BADGE_INFO.Way as way, BADGE_LOG.Insert_Dt as date, BADGE_INFO.Rarity as rarity "
        sql += " from BADGE_LOG left join BADGE_INFO on BADGE_LOG.BadgeKey = BADGE_INFO.Idx  "
        sql +=" where Userid = '"+userid+"' order by Insert_Dt desc  "
        df = pd.read_sql_query(sql,conn)
        print(df)
    finally:
        conn.close()
        
    return df.to_json(orient='records')

@application.route("/api/ranking" , methods=['GET'])
@jwt_required
def getCoffeeParkRank():   
    Userid = get_jwt_identity()
    UserType = getUserType(Userid)
    conn = pymysql.connect(host=hoststr, user=usrstr, password=passwordstr, db=dbstr, charset='utf8')
    df = ""
  
    try:
        sql = " select B.UserName as name, Sum(A.QtyKg) as amount from COFFEEPARK_LOG as A "
        sql +=" left join  USER_INFO as B on A.Userid = B.Userid "
        sql +=" where B.UserType = '"+UserType+"' "
        sql +=" group by B.Userid, B.UserName "
        sql +=" order by Sum(A.QtyKg) desc "
    
        df = pd.read_sql_query(sql,conn)
        print(df)
    finally:
        conn.close()
        
    return df.to_json(orient='records')

@application.route("/api/monitor/amount" , methods=['GET'])
def getCoffeeParkHistoryByMonitor():
    
    Province = request.args.get('province')
    conn = pymysql.connect(host=hoststr, user=usrstr, password=passwordstr, db=dbstr, charset='utf8')
    df = ""
    try:
        sql = " select COFFEEPARK_LOG.Userid as UserId, USER_INFO.UserName as UserName, COFFEEPARK_LOG.UserType, DATE_FORMAT(COFFEEPARK_LOG.Insert_Dt,'%Y-%m-%d') as timestamp , COFFEEPARK_LOG.status as status, COFFEEPARK_LOG.QtyKg as amount, USER_INFO.Province as  Province from COFFEEPARK_LOG  left join USER_INFO on COFFEEPARK_LOG.Userid = USER_INFO.Userid "
        
        if Province == "" :
            sql +=" where DATE_FORMAT(Insert_Dt,'%Y-%m') = DATE_FORMAT(sysdate(),'%Y-%m') "        
        else :
            sql +=" where USER_INFO.Province='"+Province+"' and  DATE_FORMAT(Insert_Dt,'%Y-%m') = DATE_FORMAT(sysdate(),'%Y-%m') "        
            
        sql +=" order by COFFEEPARK_LOG.Insert_Dt desc  "
        df = pd.read_sql_query(sql,conn)
        print(df)
    finally:
        conn.close()
        
    return df.to_json(orient='records')

@application.route("/api/monitor/province-amount" , methods=['GET'])
def getCoffeeParkProvinceByMonitor():
        
    conn = pymysql.connect(host=hoststr, user=usrstr, password=passwordstr, db=dbstr, charset='utf8')
    df = ""
    try:
        sql = " select USER_INFO.Province as Province, COFFEEPARK_LOG.UserType as UserType, CAST(Sum(COFFEEPARK_LOG.QtyKg) as unsigned int) as amount from COFFEEPARK_LOG "
        sql +=" left join USER_INFO on COFFEEPARK_LOG.Userid = USER_INFO.Userid "    
        sql +=" where DATE_FORMAT(Insert_Dt,'%Y-%m') = DATE_FORMAT(sysdate(),'%Y-%m') "                
        sql +=" group by USER_INFO.Province, COFFEEPARK_LOG.UserType "

        df = pd.read_sql_query(sql,conn)
        print(df)
    finally:
        conn.close()
        
    return df.to_json(orient='records')

def startBlockChainMonitorJob():
    
    # 블록체인 1분 단위로 누적 트랜잭션 수 가져오기
    url = "http://101.101.209.10:3000/total-transaction"
    url_data = urllib.request.urlopen(url)
    jsonString = url_data.read().decode("utf-8")
    jsonString = json.loads(jsonString)
    TranQty = jsonString["totalTransaction"]
    
    conn = pymysql.connect(host=hoststr, user=usrstr, password=passwordstr, db=dbstr, charset='utf8')
    try:
        cursor = conn.cursor()
        sql = " insert into BLOCKCHAIN_LOG (TranQty, Insert_Dt) "
        sql +=" Values('"+str(TranQty)+"',sysdate()) "        
        cursor.execute(sql)
        conn.commit()
        returnValue = "success"
        print('I am working blockchain trans batchjob working for 1 min')

    finally:
        conn.close()
     
if __name__ == "__main__":
    
    #스케줄러 시작
    scheduler = BackgroundScheduler()
    job = scheduler.add_job(startBlockChainMonitorJob, 'interval', minutes=1)
    scheduler.start()

    #웹서버 시작
    application.run(host='0.0.0.0', port=80)
