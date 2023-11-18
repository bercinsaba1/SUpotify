from flask import Blueprint, Flask, request, url_for, session, jsonify, redirect
from flask_mysqldb import MySQL
from flask_cors import CORS, cross_origin
from spotipy.oauth2 import SpotifyOAuth 
import spotipy
import requests
import time 
import json  
from . import db 

user = Blueprint('user', __name__)

TOKEN_INFO = "token_info" 

client_id = "e3bb122dc61347a6b496d5f15a036a68"
client_secret = "e217a887698a43479bcbcc3698853677"

@user.route('/user_data/<email>', methods=['GET'])
def user_page(email):
    cur = db.connection.cursor()
    
    cur.execute("""
        SELECT user_id, last_sid FROM `User` WHERE `email` = %s
    """, (email,))
    user = cur.fetchone()
    
    cur.execute("""
        SELECT User.user_id, User.profile_pic, User.last_sid
        FROM Friendship
        JOIN User ON (Friendship.user1_id = User.user_id OR Friendship.user2_id = User.user_id)
        WHERE (Friendship.user1_id = %s OR Friendship.user2_id = %s)
        """, (user['user_id'], user['user_id']))
    friends = cur.fetchall()
    
    cur.close()
    return jsonify({
        'user_id': user['user_id'],
        'profile_pic': user['profile_pic'],
        'last_sid': user['last_sid']
    } for user in friends)