from flask import Flask, render_template, request, make_response, g
from redis import Redis

import psycopg2
import sys
import time
import datetime
import os
import socket
import random
import json

def init_db():
    connection_string = "host='db' dbname='postgres' user='postgres' password='theCamelsHateUs'"
    print "DEBUG ::: Connecting to database\n    ->%s" % (connection_string)
    while True:
      try:
          conn = psycopg2.connect(connection_string)
          break
      except psycopg2.OperationalError as err:
          print "DEBUG ::: psycopg2.connect error: {0} ".format(err)
          time.sleep(1)
    cursor = conn.cursor()
    return cursor

def get_all_options(cursor):
    sql = "SELECT * FROM fetch_candidates()"
    cursor.execute(sql)
    row = cursor.fetchone()
    opts = []
    while row is not None:
        opt = [{'id':row[0], 'name':row[1]}, { 'id': row[2] , 'name':row[3] }]
        opts.append(opt)
        row = cursor.fetchone()
    return opts

def get_all_votes(cursor, _id):
    print "get all votes for '{0}' ".format(_id)
    sql = "SELECT * FROM fetch_votes_for_voter('{0}')".format(_id)
    cursor.execute(sql)
    row = cursor.fetchone()
    opts = []
    while row is not None:
        opt = [{'vid':row[0], 'voter_id':row[1] , 'voter_name': row[2] , 'candidate_id':row[3], 'first_voted':row[4],  'last_change':row[5],  'change_count':row[6]    }]
        opts.append(opt)
        print "getAllVotes:  My Votes are '{0}'".format(opt)
        row = cursor.fetchone()
    return opts

def get_opponent(cursor, _id):
    sql = "SELECT * FROM fetch_opponent('{0}')".format(_id)
    cursor.execute(sql)
    row = cursor.fetchone()
    
    while row is not None:
        opt = {'id':row[0], 'name':row[1] , 'opponent_id': row[2]}
        
        row = cursor.fetchone()
    return opt

# TODO: WE NEED TO add database key for these array
name = 'name'
_id = 'id'
#options =[[{_id:1,name:"Cats"}, {_id:2, name:"Dogs"}] , [{_id:3,name:"Apple"}, {_id:4,name:"Android"}] , [{_id:5,name:"Pepsi"}, {_id:6,name:"Coca Cola"}], [{_id:7,name:"Blue Pen"}, {_id:8,name:"Black Pen"}], [{_id:9,name:"Regular Pen"},{_id:10,name:"Fountain Pen"}], [{_id:11,name:"Pencil"},{_id:12,name:"Mechanical Pencil"}] ]

#print options

hostname = socket.gethostname()

app = Flask(__name__)

def get_redis():
    if not hasattr(g, 'redis'):
        g.redis = Redis(host="redis", db=0, socket_timeout=5)
    return g.redis

@app.route("/", methods=['POST','GET'])
def hello():
    voter_id = request.cookies.get('voter_id')
    if not voter_id:
        voter_id = hex(random.getrandbits(64))[2:-1]
    #todo: fetch all votes from this person and make a response
    vote = None
    cursor = init_db();
    # test : if this app gets the correct data?
    cursor.execute("SELECT * FROM voting");
    row = cursor.fetchone()
    
    while row is not None:
        opt = {'id':row[0], 'voter':row[1] , 'candidate_id': row[2], 'first_voted':row[3], 'last_change':row[4], 'changes_count':row[5]}
        print "DEBUG ::: There are votings in db : {0}".format(opt)
        row = cursor.fetchone()
    
    options = get_all_options(cursor)
    votes = get_all_votes(cursor, str(voter_id))
    opponent = "0"
    if request.method == 'POST':
        redis = get_redis()
        vote = request.form['vote']
        _id = vote.split("_")[1]
        opponent = get_opponent(cursor, str(_id))
        #print request.headers.get('User-Agent')
        #print request.access_route
        
        #for i in request.headers:
        #print "K: {0}, \n V: {1} \n\n ".format(i ,request.headers[i])
        #print "K: {0}, \n ".format(i)
        
        print "DEBUG ::: received vote : " + vote
        # todo: add other elements here
        data = json.dumps({'voter_id': voter_id, 'vote': _id, 'user_agent':request.headers.get('User-Agent'), 'user_address':request.remote_addr, 'port':'80', 'last_visit':str(datetime.datetime.now())})
        redis.rpush('votes', data)

    resp = make_response(render_template(
        'index.html',
        options=options,
        hostname=hostname,
        votes=votes,
        vote=vote,
        opponent=opponent
    ))
    resp.set_cookie('voter_id', voter_id)
    return resp


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
