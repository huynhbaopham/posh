import streamlit as st
import MySQLdb as sql
from datetime import datetime, time, timezone


# @st.cache_resource
def poshdb_connect():
    db = sql.connect(
        host=st.secrets["connections"]["host"],
        user=st.secrets["connections"]["username"],
        password=st.secrets["connections"]["password"],
        database=st.secrets["connections"]["database"],
        autocommit=True,
        ssl_mode="VERIFY_IDENTITY",
        ssl={"ca": "poshdb.pem"},
    )

    return db


def checkin(phone, client=None):
    db = poshdb_connect()
    conn = db.cursor()
    try:
        if client == None:
            conn.execute(
                f"SELECT firstName, points FROM Clients WHERE phoneNumber={phone};"
            )
            r = conn.fetchone()
        else:
            r = client

        if r != None:
            conn.execute(
                f"SELECT * FROM CheckIns WHERE DATE(dateTime)=CURDATE() and phoneNumber={phone};"
            )
            if conn.fetchone() == None:
                conn.execute(
                    f"UPDATE Clients SET points={r[1]+1} WHERE phoneNumber={phone}"
                )

            conn.execute(f"INSERT INTO CheckIns (phoneNumber) VALUES ({phone});")

    except:
        conn.close()
        return -1

    conn.close()
    return r


def signup(client):
    db = poshdb_connect()
    conn = db.cursor()

    try:
        conn.execute(
            f"SELECT firstName, points FROM Clients WHERE phoneNumber={client[0]};"
        )
        c = conn.fetchone()
        if c != None:
            conn.close()
            checkin(phone=client[0], client=c)
            return 0, c

        conn.execute(
            """
                     INSERT INTO Clients (phoneNumber, firstName, lastName, birthdate) 
                     VALUES (%s, %s, %s, %s)
                     """,
            client,
        )
        conn.execute(f"INSERT INTO CheckIns (phoneNumber) VALUES ({client[0]});")

    except:
        conn.close()
        return -1, None

    conn.close()
    return 1, None


def get_checkins(sdate, edate):
    sdate = datetime.combine(sdate, time.fromisoformat("00:00:01-07:00")).astimezone()
    edate = datetime.combine(edate, time.fromisoformat("23:59:59-07:00")).astimezone()

    db = poshdb_connect()
    conn = db.cursor()

    try:
        conn.execute(
            f"SELECT CONCAT(firstName, ' ', lastName) as name, birthdate, points, Clients.phoneNumber, dateTime FROM Clients, CheckIns WHERE Clients.phoneNumber = CheckIns.phoneNumber AND dateTime BETWEEN '{sdate}' AND '{edate}';"
        )
        clients = conn.fetchall()
        conn.close()
    except:
        conn.close()
        return -1
    return clients


def get_client(phone=None, fname=None, lastName=None):
    command = "SELECT * FROM Clients;"

    db = poshdb_connect()
    conn = db.cursor()

    try:
        conn.execute(command)
        clients = conn.fetchall()
        conn.close()
    except:
        conn.close()
        return -1
    return clients


def updateClientInfo(edited_rows, df):
    instances = []
    rows = edited_rows.keys()
    for row in rows:
        phone = df.at[row, "phoneNumber"]
        changes = map(lambda i: f"{i[0]}='{i[1]}'", edited_rows[row].items())
        changes = ", ".join(list(changes))
        instances.append((changes, phone))

    cmds = [f"UPDATE Clients SET {i[0]} WHERE phoneNumber={i[1]};" for i in instances]
    db = poshdb_connect()
    conn = db.cursor()
    try:
        for cmd in cmds:
            conn.execute(cmd)
        conn.close()
        print("success")
        return
    except:
        conn.close()
        print("fail")
        return -1


def redeemDB(points: list, phones: list):
    db = poshdb_connect()
    conn = db.cursor()
    try:
        [
            conn.execute(
                f"UPDATE Clients SET points={point} WHERE phoneNumber={phone};"
            )
            for point, phone in zip(points, phones)
        ]
        conn.close()
        print("success")
        return
    except:
        conn.close()
        print("fail")
        return -1
